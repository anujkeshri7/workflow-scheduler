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

def get_current_ist_time():
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(tz_ist)

def parse_ist_time_str(time_str):
    """
    Parses 'YYYY-MM-DD HH:MM AM/PM IST' into datetime object.
    """
    try:
        clean = time_str.replace(" IST", "").strip()
        return datetime.datetime.strptime(clean, "%Y-%m-%d %I:%M %p")
    except Exception:
        return None

def is_within_active_posting_window(now_ist):
    """
    Returns True if current time is inside one of the 3 active broadcasting windows:
    - Morning: 06:00 AM - 10:00 AM (mins 360 - 600)
    - Afternoon: 11:45 AM - 03:30 PM (mins 705 - 930)
    - Evening: 06:00 PM - 10:30 PM (mins 1080 - 1350)
    """
    total_mins = now_ist.hour * 60 + now_ist.minute
    
    # Morning: 06:00 to 10:00
    if 360 <= total_mins <= 600:
        return True, "Morning Window"
    # Afternoon: 11:45 to 15:30
    elif 705 <= total_mins <= 930:
        return True, "Afternoon Window"
    # Evening: 18:00 to 22:30
    elif 1080 <= total_mins <= 1350:
        return True, "Evening Window"
    else:
        return False, "Off-Hours / Night Window"

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Notice: Telegram credentials not set.")
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

def create_and_publish_reel(video_url, caption):
    if not META_TOKEN or not IG_ACCOUNT_ID:
        print("[ERROR] META_ACCESS_TOKEN or IG_ACCOUNT_ID missing in environment.")
        return None

    clean_caption = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)<\/a>', r'\2 (\1)', caption)

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
            print(f"[FAIL] Container creation failed: {c_res}")
            return None
        print(f"[OK] Container ID: {container_id}. Waiting for processing...")
    except Exception as e:
        print(f"Network error during container creation: {e}")
        return None

    # 2. Wait for Processing
    s_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}"
    for attempt in range(1, 16):
        try:
            s_res = requests.get(s_url, params={'fields': 'status_code', 'access_token': META_TOKEN}, timeout=20).json()
            status = s_res.get('status_code', '').upper()
            if status == 'FINISHED':
                print(f"[OK] Reel processing complete ({attempt * 5}s)!")
                break
            elif status in ['ERROR', 'EXPIRED']:
                print(f"[FAIL] Processing failed: {s_res}")
                return None
            time.sleep(5)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

    # 3. Publish Live
    p_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media_publish"
    try:
        p_res = requests.post(p_url, data={'creation_id': container_id, 'access_token': META_TOKEN}, timeout=30).json()
        media_id = p_res.get('id')
        if media_id:
            print(f"[SUCCESS] Reel successfully PUBLISHED LIVE! Instagram Media ID: {media_id}")
            return media_id
        else:
            print(f"[FAIL] Media publish error: {p_res}")
            return None
    except Exception as e:
        print(f"Network error during publishing: {e}")
        return None

def process_queue(force=False):
    now_ist = get_current_ist_time()
    time_str = now_ist.strftime('%Y-%m-%d %I:%M %p IST')
    
    print(f"\n=======================================================")
    print(f"Instagram Autonomous Cloud Scheduler Triggered at {time_str}")
    print(f"=======================================================\n")

    if not os.path.exists(QUEUE_FILE):
        print(f"Error: {QUEUE_FILE} not found.")
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)

    pending = queue_data.get("pending_posts", [])
    published = queue_data.get("published_posts", [])

    # Case 1: Empty Queue
    if not pending:
        print(f"[EMPTY QUEUE] No pending posts in queue.")
        return

    # Check if manual / forced trigger
    is_github_event = os.getenv("GITHUB_EVENT_NAME")
    is_manual = (is_github_event == "workflow_dispatch") or force or (len(sys.argv) > 1 and sys.argv[1] == "--force")

    if not is_manual:
        # Check active window
        in_window, window_name = is_within_active_posting_window(now_ist)
        if not in_window:
            print(f"[INFO] Currently in {window_name}. Sleeping until next active broadcasting window.")
            return

        # Check last published time for safe spacing
        if published:
            last_pub = published[-1]
            last_time_str = last_pub.get("published_at_ist", "")
            last_dt = parse_ist_time_str(last_time_str)
            if last_dt:
                now_naive = now_ist.replace(tzinfo=None)
                diff_minutes = (now_naive - last_dt).total_seconds() / 60.0
                if diff_minutes < MIN_GAP_MINUTES:
                    wait_left = int(MIN_GAP_MINUTES - diff_minutes)
                    print(f"[SPACING SAFEGUARD] Last post published {int(diff_minutes)}m ago. Waiting {wait_left}m more for safe interval.")
                    return

    # Pop First Item (FIFO)
    target_post = pending.pop(0)
    post_id = target_post.get("id", "unknown")
    headline = target_post.get("headline", "")
    caption = target_post.get("caption", "")
    video_url = target_post.get("public_video_url", "")

    print(f"Publishing Next Queued Reel:")
    print(f"ID: {post_id}")
    print(f"Headline: {headline[:50]}...")
    print(f"Video URL: {video_url}\n")

    if not video_url:
        print("Error: No public video URL in post object.")
        return

    # Execute Publishing on Instagram
    media_id = create_and_publish_reel(video_url, caption)

    if media_id:
        target_post["status"] = "PUBLISHED"
        target_post["published_at_ist"] = time_str
        target_post["ig_media_id"] = media_id
        target_post["published_by"] = "GitHub Actions Cloud Runner"
        published.append(target_post)

        queue_data["pending_posts"] = pending
        queue_data["published_posts"] = published

        # Save Queue File
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)

        remaining_count = len(pending)
        print(f"\n[OK] Queue Updated: {remaining_count} pending posts remaining.")

        # Send Telegram Success
        clean_title = headline.replace('\n', ' ')
        send_telegram_alert(
            f"🎉 <b>Instagram Reel Live</b>\n\n"
            f"🕒 <b>Published At</b>: <code>{time_str}</code>\n"
            f"📰 <b>Headline</b>: {clean_title}\n"
            f"🆔 <b>Instagram Media ID</b>: <code>{media_id}</code>\n\n"
            f"📊 <b>Remaining in Queue</b>: <b>{remaining_count} Posts</b>"
        )

        # Check if queue is now 0
        if remaining_count == 0:
            send_telegram_alert(
                f"🔔 <b>Queue Exhausted Reminder</b>\n\n"
                f"Aapki queue ke sabhi news reels Instagram par publish ho chuke hain!\n"
                f"Agle upcoming slots ke liye Antigravity me workflow run karke queue refill karein. 🚀"
            )

        # Commit and Push State to GitHub
        commit_and_push_queue()
    else:
        print("[FAIL] Publishing failed. Putting post back into queue.")
        pending.insert(0, target_post)
        queue_data["pending_posts"] = pending
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue_data, f, indent=2, ensure_ascii=False)

def commit_and_push_queue():
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "add", QUEUE_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "commit", "-m", "chore: update queue state after cloud publish [skip ci]"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "push"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[OK] Updated queue state successfully committed and pushed to repository.")
    except Exception as e:
        print(f"Git commit error in runner: {e}")

if __name__ == "__main__":
    process_queue()
