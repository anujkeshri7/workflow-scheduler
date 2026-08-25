import os
import json
import time
import requests
from dotenv import load_dotenv
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from video_hoster import upload_video_to_public_host
from meta_reel_publisher import create_reel_container, wait_for_reel_processing, publish_reel_container

load_dotenv()
DATA_FILE = "daily_news_data.json"

def run_scheduled_job(post_index, delay_seconds):
    print(f"Scheduled worker started for Post {post_index + 1}. Waiting {delay_seconds} seconds ({delay_seconds//60} mins)...")
    time.sleep(delay_seconds)
    
    if not os.path.exists(DATA_FILE):
        return
        
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    posts = data.get("posts", [])
    if post_index >= len(posts):
        return
        
    post = posts[post_index]
    video_path = post.get("video_path", "")
    caption = post.get("caption", "")
    
    import re
    clean_caption = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)<\/a>', r'\2 (\1)', caption)
    
    print(f"\n[Timer Triggered] Publishing Scheduled Post {post_index + 1} to Instagram Reels...")
    public_url = upload_video_to_public_host(video_path)
    if not public_url:
        return
        
    cid = create_reel_container(public_url, clean_caption)
    if cid and wait_for_reel_processing(cid):
        pid = publish_reel_container(cid)
        if pid:
            post["ig_post_id"] = pid
            post["published_via"] = "Local Timer Scheduler"
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Successfully published scheduled Post {post_index + 1} (Media ID: {pid})")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        p_idx = int(sys.argv[1])
        d_sec = int(sys.argv[2])
        run_scheduled_job(p_idx, d_sec)
