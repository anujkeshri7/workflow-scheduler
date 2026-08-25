import os
import json
import time
import datetime
import requests
import re
import subprocess
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

META_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

QUEUE_FILE = "posts_queue.json"
GRAPH_VERSION = "v19.0"

def get_current_ist_time():
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(tz_ist)

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

def create_and_publish_reel(video_url, caption):
    """
    Creates Reel container on Meta API, waits for processing, and publishes live.
    """
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

def process_queue():
    now_ist = get_current_ist_time()
    time_str = now_ist.strftime('%Y-%m-%d %I:%M %p IST')
    
    print(f"\n=======================================================")
    print(f"Instagram Cloud Scheduler Triggered at {time_str}")
    print(f"=======================================================\n")

    if not os.path.exists(QUEUE_FILE):
        print(f"Error: {QUEUE_FILE} not found.")
        send_telegram_alert(f"⚠️ <b>Queue Missing Alert</b>\n\n<code>{QUEUE_FILE}</code> file repository me nahi mila.")
        return

    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue_data = json.load(f)

    pending = queue_data.get("pending_posts", [])
    published = queue_data.get("published_posts", [])

    # Case 1: Empty Queue
    if not pending:
        print(f"[EMPTY QUEUE] No pending posts found to publish for slot at {time_str}.")
        send_telegram_alert(
            f"⚠️ <b>Instagram Queue Empty Alert</b>\n\n"
            f"🕒 <b>Slot Time</b>: <code>{time_str}</code>\n\n"
            f"Queue me publish karne ke liye koi news reel nahi bachi hai.\n"
            f"Agle slot ke liye Antigravity me workflow run karke queue refill karein!"
        )
        return

    # Case 2: Pop First Item (FIFO)
    target_post = pending.pop(0)
    post_id = target_post.get("id", "unknown")
    headline = target_post.get("headline", "")
    caption = target_post.get("caption", "")
    video_url = target_post.get("public_video_url", "")

    print(f"Consuming Next Post from Queue:")
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
        send_telegram_alert(
            f"❌ <b>Publish Error Alert</b>\n\n"
            f"Slot <code>{time_str}</code> par Reel publish nahi ho payi. Post queue me safe hai aur agle trigger par retry hogi."
        )

def commit_and_push_queue():
    """
    Commits and pushes updated posts_queue.json in GitHub Actions environment.
    """
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
