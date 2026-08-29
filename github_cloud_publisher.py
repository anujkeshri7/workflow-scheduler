import os
import json
import time
import datetime
import requests
import re
import subprocess
import sys

from dotenv import load_dotenv
load_dotenv()

META_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

QUEUE_FILE = "posts_queue.json"
GRAPH_VERSION = "v19.0"

# Minimum spacing between posts in minutes
MIN_GAP_MINUTES = 35

# Maximum consecutive failures before skipping a post
MAX_FAIL_COUNT = 2


def get_current_ist_time():
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(tz_ist)


def parse_ist_time_str(time_str):
    """Parse 'YYYY-MM-DD HH:MM AM/PM IST' into a naive datetime."""
    try:
        clean = time_str.replace(" IST", "").strip()
        return datetime.datetime.strptime(clean, "%Y-%m-%d %I:%M %p")
    except Exception:
        return None


def is_within_active_posting_window(now_ist):
    """
    Returns (True, window_name) if current IST time is inside an active window:
      Morning   06:00 - 10:00
      Afternoon 11:45 - 15:30
      Evening   18:00 - 22:30
    """
    total_mins = now_ist.hour * 60 + now_ist.minute
    if 360 <= total_mins <= 600:
        return True, "Morning Window"
    elif 705 <= total_mins <= 930:
        return True, "Afternoon Window"
    elif 1080 <= total_mins <= 1350:
        return True, "Evening Window"
    else:
        return False, "Off-Hours / Night Window"


def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Notice: Telegram credentials not set in cloud environment.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        requests.post(url, json=payload, timeout=20)
    except Exception as e:
        print(f"Telegram alert error: {e}")


# ─────────────────────────────────────────────
# VIDEO URL HEALTH CHECK & SELF-HEALING
# ─────────────────────────────────────────────

def is_video_url_alive(url):
    """
    Quick HEAD/GET check to verify the video file is still downloadable.
    Returns True only if we get a 200 with a video-ish content-type or
    content-length > 10 KB.
    """
    if not url:
        return False
    try:
        r = requests.head(url, timeout=12, allow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            cl = int(r.headers.get("content-length", "0") or "0")
            if "video" in ct or "octet" in ct or cl > 10240:
                return True
        # Some CDNs don't support HEAD properly, try a tiny GET
        r2 = requests.get(url, timeout=12, allow_redirects=True, stream=True,
                          headers={"Range": "bytes=0-1024"})
        alive = r2.status_code in (200, 206) and len(r2.content) > 100
        r2.close()
        return alive
    except Exception:
        return False


def rehost_video_from_queue_data(post):
    """
    Given a post dict, try to find the original local video file and re-upload it.
    This is a best-effort fallback; if the local file is gone it returns None.
    """
    # The video_hoster module should exist alongside this script
    try:
        from video_hoster import upload_video_to_public_host
    except ImportError:
        print("[REHOST] video_hoster.py not available in this environment.")
        return None

    # Look for local video file candidates
    video_path = post.get("local_video_path", "")
    if video_path and os.path.exists(video_path):
        print(f"[REHOST] Re-uploading from local file: {video_path}")
        new_url = upload_video_to_public_host(video_path)
        return new_url

    print("[REHOST] No local video file available for re-upload.")
    return None


# ─────────────────────────────────────────────
# INSTAGRAM PUBLISH FLOW
# ─────────────────────────────────────────────

def create_and_publish_reel(video_url, caption):
    if not META_TOKEN or not IG_ACCOUNT_ID:
        print("[ERROR] META_ACCESS_TOKEN or IG_ACCOUNT_ID missing in environment.")
        return None

    clean_caption = re.sub(
        r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>',
        r'\2 (\1)', caption
    )

    # 1. Create Media Container
    c_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media"
    c_payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': clean_caption,
        'access_token': META_TOKEN
    }

    try:
        c_res = requests.post(c_url, data=c_payload, timeout=30).json()
        container_id = c_res.get('id')
        if not container_id:
            err = c_res.get('error', {})
            print(f"[FAIL] Container creation failed: {c_res}")
            # Check if this is a video-URL-related error
            err_msg = str(err.get('message', '')).lower()
            if 'url' in err_msg or 'video' in err_msg or 'download' in err_msg:
                print("[DIAGNOSIS] Meta could not download the video. URL is likely expired.")
            return None
        print(f"[OK] Container ID: {container_id}. Waiting for processing...")
    except Exception as e:
        print(f"Network error during container creation: {e}")
        return None

    # 2. Wait for Processing (up to 75 seconds)
    s_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}"
    for attempt in range(1, 16):
        try:
            s_res = requests.get(
                s_url,
                params={'fields': 'status_code', 'access_token': META_TOKEN},
                timeout=20
            ).json()
            status = s_res.get('status_code', '').upper()
            if status == 'FINISHED':
                print(f"[OK] Reel processing complete ({attempt * 5}s)!")
                break
            elif status in ['ERROR', 'EXPIRED']:
                print(f"[FAIL] Processing failed with status '{status}': {s_res}")
                return None
            time.sleep(5)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

    # 3. Publish Live
    p_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media_publish"
    try:
        p_res = requests.post(
            p_url,
            data={'creation_id': container_id, 'access_token': META_TOKEN},
            timeout=30
        ).json()
        media_id = p_res.get('id')
        if media_id:
            print(f"[SUCCESS] Reel PUBLISHED LIVE! Instagram Media ID: {media_id}")
            return media_id
        else:
            print(f"[FAIL] Media publish error: {p_res}")
            return None
    except Exception as e:
        print(f"Network error during publishing: {e}")
        return None


# ─────────────────────────────────────────────
# MAIN QUEUE PROCESSOR
# ─────────────────────────────────────────────

def process_queue(force=False):
    now_ist = get_current_ist_time()
    time_str = now_ist.strftime('%Y-%m-%d %I:%M %p IST')

    print(f"\n{'='*60}")
    print(f"Instagram Autonomous Cloud Scheduler")
    print(f"Triggered: {time_str}")
    print(f"{'='*60}\n")

    if not os.path.exists(QUEUE_FILE):
        print(f"Error: {QUEUE_FILE} not found.")
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)

    pending = queue_data.get("pending_posts", [])
    published = queue_data.get("published_posts", [])

    if not pending:
        print("[EMPTY QUEUE] No pending posts. Nothing to do.")
        send_telegram_alert(
            "🔔 <b>Queue Empty</b>\n\n"
            "Sabhi reels publish ho chuki hain.\n"
            "Naye posts queue me add karein via Antigravity workflow. 🚀"
        )
        return

    print(f"Queue Status: {len(pending)} pending | {len(published)} published\n")

    # ── Determine if this is a manual trigger ──
    github_event = os.getenv("GITHUB_EVENT_NAME", "")
    is_manual = (
        github_event == "workflow_dispatch"
        or force
        or (len(sys.argv) > 1 and sys.argv[1] == "--force")
    )

    if not is_manual:
        # Check active window
        in_window, window_name = is_within_active_posting_window(now_ist)
        if not in_window:
            print(f"[SKIP] Currently in {window_name}. No posting outside active windows.")
            return

        # Check spacing from last publish
        if published:
            last_pub = published[-1]
            last_time_str = last_pub.get("published_at_ist", "")
            last_dt = parse_ist_time_str(last_time_str)
            if last_dt:
                now_naive = now_ist.replace(tzinfo=None)
                diff_minutes = (now_naive - last_dt).total_seconds() / 60.0
                # Only enforce spacing for same-day posts
                if diff_minutes >= 0 and diff_minutes < MIN_GAP_MINUTES:
                    wait_left = int(MIN_GAP_MINUTES - diff_minutes)
                    print(f"[SPACING] Last post {int(diff_minutes)}m ago. Need {wait_left}m more gap.")
                    return

    # ── Find the first post with a WORKING video URL ──
    target_idx = None
    target_post = None

    for idx, post in enumerate(pending):
        video_url = post.get("public_video_url", "")
        post_id = post.get("id", "unknown")
        fail_count = post.get("_fail_count", 0)

        print(f"[CHECK #{idx+1}] {post_id} | URL: {video_url[:70]}...")

        # If this post already failed too many times, skip it permanently
        if fail_count >= MAX_FAIL_COUNT:
            headline = post.get("headline", "")[:40].replace("\n", " ")
            print(f"  -> SKIPPING (failed {fail_count} times). Moving to dead_posts.")
            # Move to a dead_posts list so it doesn't block the queue
            dead = queue_data.setdefault("dead_posts", [])
            post["status"] = "DEAD_URL"
            post["death_reason"] = "Video URL expired and could not be re-hosted"
            dead.append(post)
            pending.pop(idx)
            # Save immediately so we don't re-process
            queue_data["pending_posts"] = pending
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
            send_telegram_alert(
                f"⚠️ <b>Dead Post Removed</b>\n\n"
                f"Post <code>{post_id}</code> removed from queue.\n"
                f"Reason: Video URL expired after {fail_count} failed attempts.\n"
                f"Title: {headline}"
            )
            # Recurse to try the next post
            process_queue(force=force)
            return

        # Check if URL is still alive
        if is_video_url_alive(video_url):
            print(f"  -> URL is ALIVE. Proceeding to publish.")
            target_idx = idx
            target_post = post
            break
        else:
            print(f"  -> URL is DEAD/EXPIRED. Incrementing fail counter.")
            post["_fail_count"] = fail_count + 1
            # Save the updated fail count
            queue_data["pending_posts"] = pending
            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
            # Try next post in queue instead of blocking
            continue

    if target_post is None:
        print("\n[ALL URLS DEAD] Every pending post has a dead/expired video URL.")
        send_telegram_alert(
            "🚨 <b>All Video URLs Expired!</b>\n\n"
            "Queue me sabhi pending posts ke video links expire ho gaye hain.\n"
            "Antigravity me workflow run karke nayi reels generate aur queue me add karein. 🔄"
        )
        commit_and_push_queue()
        return

    # ── Pop the target post and publish ──
    pending.pop(target_idx)
    post_id = target_post.get("id", "unknown")
    headline = target_post.get("headline", "")
    caption = target_post.get("caption", "")
    video_url = target_post.get("public_video_url", "")

    print(f"\n{'─'*50}")
    print(f"Publishing Reel:")
    print(f"  ID:       {post_id}")
    print(f"  Headline: {headline[:60].replace(chr(10), ' ')}...")
    print(f"  Video:    {video_url}")
    print(f"{'─'*50}\n")

    media_id = create_and_publish_reel(video_url, caption)

    if media_id:
        target_post["status"] = "PUBLISHED"
        target_post["published_at_ist"] = time_str
        target_post["ig_media_id"] = media_id
        target_post["published_by"] = "GitHub Actions Cloud Runner"
        # Clean internal fields
        target_post.pop("_fail_count", None)
        published.append(target_post)

        queue_data["pending_posts"] = pending
        queue_data["published_posts"] = published

        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)

        remaining = len(pending)
        print(f"\n[OK] Queue Updated: {remaining} pending posts remaining.")

        clean_title = headline.replace('\n', ' ')
        send_telegram_alert(
            f"🎉 <b>Instagram Reel Live</b>\n\n"
            f"🕒 <b>Published</b>: <code>{time_str}</code>\n"
            f"📰 <b>Title</b>: {clean_title}\n"
            f"🆔 <b>Media ID</b>: <code>{media_id}</code>\n\n"
            f"📊 <b>Queue Remaining</b>: <b>{remaining} Posts</b>"
        )

        if remaining == 0:
            send_telegram_alert(
                "🔔 <b>Queue Exhausted</b>\n\n"
                "Sabhi reels publish ho chuki hain!\n"
                "Antigravity me workflow run karke queue refill karein. 🚀"
            )

        commit_and_push_queue()
    else:
        print("[FAIL] Publishing failed. Incrementing fail counter and returning to queue.")
        target_post["_fail_count"] = target_post.get("_fail_count", 0) + 1
        pending.insert(target_idx, target_post)
        queue_data["pending_posts"] = pending
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)
        commit_and_push_queue()


def commit_and_push_queue():
    try:
        subprocess.run(
            ["git", "config", "user.name", "github-actions[bot]"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.run(
            ["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        subprocess.run(
            ["git", "add", QUEUE_FILE],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        result = subprocess.run(
            ["git", "commit", "-m", "chore: update queue state after cloud publish [skip ci]"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            subprocess.run(
                ["git", "push"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30
            )
            print("[OK] Queue state committed and pushed to repository.")
        else:
            print("[INFO] No changes to commit.")
    except Exception as e:
        print(f"Git sync error: {e}")


if __name__ == "__main__":
    process_queue()
