import os
import json
import time
import datetime
import requests
from dotenv import load_dotenv
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from video_hoster import upload_video_to_public_host

load_dotenv()
META_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
GRAPH_VERSION = "v19.0"

def get_morning_schedule_timestamps():
    """
    Returns Unix timestamps for tomorrow morning:
    - Post 1: 06:30 AM IST
    - Post 2: 07:10 AM IST
    - Post 3: 08:00 AM IST
    """
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(tz_ist)
    
    # If currently before 5:00 AM IST, schedule for today morning, otherwise tomorrow morning
    target_date = now.date() if now.hour < 5 else (now.date() + datetime.timedelta(days=1))
    
    t1 = datetime.datetime.combine(target_date, datetime.time(6, 30), tzinfo=tz_ist)
    t2 = datetime.datetime.combine(target_date, datetime.time(7, 10), tzinfo=tz_ist)
    t3 = datetime.datetime.combine(target_date, datetime.time(8, 0), tzinfo=tz_ist)
    
    return [int(t1.timestamp()), int(t2.timestamp()), int(t3.timestamp())]


def create_reel_container(video_url, caption, scheduled_unix_time=None):
    """
    Step 1: Creates an Instagram Reel container via Meta Graph API with optional cloud scheduling.
    """
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media"
    payload = {
        'media_type': 'REELS',
        'video_url': video_url,
        'caption': caption,
        'access_token': META_TOKEN
    }
    
    if scheduled_unix_time:
        payload['scheduled_publish_time'] = scheduled_unix_time

    try:
        res = requests.post(url, data=payload, timeout=30)
        res_data = res.json()
        if 'id' in res_data:
            container_id = res_data['id']
            print(f"[OK] Media Container Created! Container ID: {container_id}")
            return container_id
        else:
            print(f"[FAIL] Meta Container Creation Error: {res_data}")
            return None
    except Exception as e:
        print(f"[FAIL] Network error during container creation: {e}")
        return None


def wait_for_reel_processing(container_id, max_retries=15, poll_interval=5):
    """
    Step 2: Polls Meta Graph API until Reel video processing status is 'FINISHED'.
    """
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{container_id}"
    params = {
        'fields': 'status_code,status',
        'access_token': META_TOKEN
    }
    
    print(f"Waiting for Meta servers to process Reel container {container_id}...")
    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, params=params, timeout=20)
            data = res.json()
            status_code = data.get('status_code', '').upper()
            
            if status_code == 'FINISHED':
                print(f"[OK] Reel processing complete ({attempt * poll_interval}s)!")
                return True
            elif status_code in ['ERROR', 'EXPIRED']:
                print(f"[FAIL] Meta processing failed with status: {status_code} ({data})")
                return False
            else:
                print(f"Status: {status_code or 'IN_PROGRESS'} (check {attempt}/{max_retries})...")
                time.sleep(poll_interval)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(poll_interval)
            
    print("[FAIL] Processing timed out on Meta servers.")
    return False


def publish_reel_container(container_id):
    """
    Step 3: Publishes or locks the scheduled Reel container on Meta Cloud.
    """
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media_publish"
    payload = {
        'creation_id': container_id,
        'access_token': META_TOKEN
    }
    
    try:
        res = requests.post(url, data=payload, timeout=30)
        res_data = res.json()
        if 'id' in res_data:
            post_id = res_data['id']
            print(f"[SUCCESS] Reel successfully locked in Meta Cloud! Post ID: {post_id}")
            return post_id
        else:
            print(f"[FAIL] Meta Publishing Error: {res_data}")
            return None
    except Exception as e:
        print(f"[FAIL] Network error during publishing: {e}")
        return None


def schedule_morning_reels(data_file="daily_news_data.json"):
    """
    Schedules 3 Reels on Meta Cloud for tomorrow morning:
    - Post 1: 06:30 AM IST
    - Post 2: 07:10 AM IST
    - Post 3: 08:00 AM IST
    """
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        return False
        
    if not META_TOKEN or not IG_ACCOUNT_ID:
        print("[ERROR] META_ACCESS_TOKEN or IG_ACCOUNT_ID missing in .env")
        return False

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("posts", [])
    if not posts:
        print("No posts found to publish.")
        return False

    scheduled_times = get_morning_schedule_timestamps()

    print(f"\n=======================================================")
    print(f"Scheduling 3 Reels in Meta Cloud for Morning Slots")
    print(f"Slot 1: 06:30 AM IST | Slot 2: 07:10 AM IST | Slot 3: 08:00 AM IST")
    print(f"=======================================================\n")

    success_count = 0
    for idx, post in enumerate(posts):
        post_num = idx + 1
        video_path = post.get("video_path", "")
        caption = post.get("caption", "")
        
        import re
        clean_caption = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)<\/a>', r'\2 (\1)', caption)

        if not video_path or not os.path.exists(video_path):
            print(f"[Post {post_num}] Skipping - video not found: {video_path}")
            continue

        scheduled_time = scheduled_times[idx] if idx < len(scheduled_times) else (scheduled_times[-1] + 3600)
        time_str = datetime.datetime.fromtimestamp(
            scheduled_time,
            tz=datetime.timezone(datetime.timedelta(hours=5, minutes=30))
        ).strftime('%Y-%m-%d %I:%M %p IST')
        
        print(f"\n--- [Post {post_num}/{len(posts)}] Cloud Scheduling for {time_str} ---")

        # 1. Host video publicly
        public_video_url = upload_video_to_public_host(video_path)
        if not public_video_url:
            print(f"[Post {post_num}] Failed to host video, skipping.")
            continue

        # 2. Create Media Container with scheduled_publish_time
        container_id = create_reel_container(public_video_url, clean_caption, scheduled_time)
        if not container_id:
            continue

        # 3. Wait for video processing
        processed = wait_for_reel_processing(container_id)
        if not processed:
            continue

        # 4. Finalize Publish / Schedule on Meta Cloud
        post_id = publish_reel_container(container_id)
        if post_id:
            success_count += 1
            post["ig_post_id"] = post_id
            post["scheduled_at"] = time_str
            post["scheduled_timestamp"] = scheduled_time
            
        time.sleep(3)

    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nAll operations finished. Successfully Cloud-Scheduled: {success_count}/{len(posts)} Reels.")
    return success_count > 0


if __name__ == "__main__":
    schedule_morning_reels()
