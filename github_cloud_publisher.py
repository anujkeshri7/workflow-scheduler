import os
import json
import time
import datetime
import requests
import re
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
DATA_FILE = "daily_news_data.json"
GRAPH_VERSION = "v19.0"

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Telegram alert error: {e}")

def determine_post_index_by_time():
    """
    Determines which post to publish based on current IST time:
    - ~06:30 AM IST -> Post 1 (index 0)
    - ~07:10 AM IST -> Post 2 (index 1)
    - ~08:00 AM IST -> Post 3 (index 2)
    """
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = datetime.datetime.now(tz_ist)
    hour = now_ist.hour
    minute = now_ist.minute
    total_mins = hour * 60 + minute

    print(f"Current Cloud Runner IST Time: {now_ist.strftime('%Y-%m-%d %I:%M %p')}")

    # Slot 1: Around 06:30 AM (6:15 - 6:50) -> mins: 375 - 410
    if 375 <= total_mins <= 415:
        return 0
    # Slot 2: Around 07:10 AM (6:55 - 7:35) -> mins: 415 - 455
    elif 416 <= total_mins <= 455:
        return 1
    # Slot 3: Around 08:00 AM (7:40 - 8:30) -> mins: 460 - 510
    elif 456 <= total_mins <= 510:
        return 2
    else:
        # Default or fallback
        return 0

def publish_single_post_to_instagram(post_idx):
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found.")
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts", [])
    if post_idx >= len(posts):
        print(f"Error: Post index {post_idx} out of range (total posts: {len(posts)})")
        return False

    post = posts[post_idx]
    post_num = post_idx + 1
    caption = post.get("caption", "")
    clean_caption = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)<\/a>', r'\2 (\1)', caption)
    
    # Check public video URL or host on the fly
    public_video_url = post.get("public_video_url")
    if not public_video_url:
        # Try hosting local video if available in runner
        video_path = post.get("video_path")
        if video_path and os.path.exists(video_path):
            from video_hoster import upload_video_to_public_host
            public_video_url = upload_video_to_public_host(video_path)
            
    if not public_video_url:
        print(f"Error: No public video URL available for Post {post_num}.")
        return False

    print(f"\n=======================================================")
    print(f"Publishing Post #{post_num} to Instagram Reels via Cloud Runner")
    print(f"=======================================================\n")

    # Step 1: Create Container
    c_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media"
    c_payload = {
        'media_type': 'REELS',
        'video_url': public_video_url,
        'caption': clean_caption,
        'access_token': META_TOKEN
    }
    
    c_res = requests.post(c_url, data=c_payload, timeout=30).json()
    container_id = c_res.get('id')
    if not container_id:
        print(f"[FAIL] Container error: {c_res}")
        send_telegram_alert(f"❌ <b>Cloud Scheduler Failed</b>: Post #{post_num} container creation error: {c_res}")
        return False

    print(f"[OK] Container ID: {container_id}. Waiting for processing...")

    # Step 2: Poll Processing
    s_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}"
    for attempt in range(1, 16):
        s_res = requests.get(s_url, params={'fields': 'status_code', 'access_token': META_TOKEN}, timeout=20).json()
        status = s_res.get('status_code', '').upper()
        if status == 'FINISHED':
            print(f"[OK] Processing Finished ({attempt * 5}s)!")
            break
        elif status in ['ERROR', 'EXPIRED']:
            print(f"[FAIL] Processing error: {s_res}")
            return False
        time.sleep(5)

    # Step 3: Publish Live
    p_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media_publish"
    p_res = requests.post(p_url, data={'creation_id': container_id, 'access_token': META_TOKEN}, timeout=30).json()
    media_id = p_res.get('id')
    
    if media_id:
        print(f"[SUCCESS] Post #{post_num} PUBLISHED LIVE! Instagram Media ID: {media_id}")
        send_telegram_alert(
            f"🎉 <b>Instagram Reel Live</b>\n\n"
            f"Post #{post_num} has been successfully published to Instagram!\n"
            f"<b>Headline</b>: {post.get('headline', '').replace(chr(10), ' ')}\n"
            f"<b>Media ID</b>: <code>{media_id}</code>"
        )
        return True
    else:
        print(f"[FAIL] Media publish error: {p_res}")
        send_telegram_alert(f"❌ <b>Publish Error</b> for Post #{post_num}: {p_res}")
        return False

if __name__ == "__main__":
    env_post_idx = os.getenv("POST_INDEX")
    if env_post_idx is not None and env_post_idx.isdigit():
        target_idx = int(env_post_idx)
    else:
        target_idx = determine_post_index_by_time()

    print(f"Targeting Post Index: {target_idx} (Post #{target_idx + 1})")
    publish_single_post_to_instagram(target_idx)
