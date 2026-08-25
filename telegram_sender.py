import os
import sys
import time
import json
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
DATA_FILE = "daily_news_data.json"
LOCK_FILE = ".telegram_sender.lock"
HISTORY_FILE = ".sent_posts_history.json"

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        try:
            mtime = os.path.getmtime(LOCK_FILE)
            if time.time() - mtime < 300:
                print("Lockfile active. Another process is currently sending to Telegram. Exiting to prevent duplicates.")
                return False
        except Exception:
            pass
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass

def load_sent_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sent_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save sent history: {e}")

def get_post_hash(image_path, caption):
    data = f"{image_path}:{caption}".encode('utf-8')
    return hashlib.md5(data).hexdigest()

def is_already_sent(image_path, caption):
    history = load_sent_history()
    post_key = get_post_hash(image_path, caption)
    if post_key in history:
        sent_time = history[post_key].get("timestamp", 0)
        # Suppress duplicate sends within 12 hours (43200 seconds)
        if time.time() - sent_time < 43200:
            return True
    return False

def record_sent_post(image_path, caption):
    history = load_sent_history()
    post_key = get_post_hash(image_path, caption)
    history[post_key] = {
        "timestamp": time.time(),
        "image": os.path.basename(image_path)
    }
    save_sent_history(history)

def send_to_telegram(image_path, caption, video_path=None):
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Missing Telegram credentials in .env")
        return False

    # Check if video is available to send
    if video_path and os.path.exists(video_path):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"
        file_to_send = video_path
        file_field = 'video'
    elif os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        file_to_send = image_path
        file_field = 'photo'
    else:
        print(f"Error: Neither image nor video found ({image_path})")
        return False

    # STRICT CHECK: Do not re-send the exact same post if already delivered
    if is_already_sent(file_to_send, caption):
        print(f"SKIP (DUPLICATE PREVENTED): {os.path.basename(file_to_send)} was already delivered to Telegram!")
        return True

    try:
        with open(file_to_send, 'rb') as media_file:
            payload = {
                'chat_id': CHAT_ID,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            files = {
                file_field: media_file
            }
            response = requests.post(url, data=payload, files=files, timeout=120)
            
            if response.status_code == 200:
                print(f"SUCCESS: Sent {os.path.basename(file_to_send)} to Telegram!")
                record_sent_post(file_to_send, caption)
                return True
            else:
                print(f"FAILED to send {os.path.basename(file_to_send)}: Status {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Error connecting to Telegram API for {os.path.basename(file_to_send)}: {e}")
        return False

if __name__ == '__main__':
    if not acquire_lock():
        sys.exit(0)
        
    try:
        if not os.path.exists(DATA_FILE):
            print(f"Error: {DATA_FILE} not found.")
            sys.exit(1)
            
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        posts = data.get("posts", [])
        total_posts = len(posts)
        print(f"Starting strictly sequential Telegram delivery for {total_posts} posts...")
        
        for idx, item in enumerate(posts, 1):
            out_path = item.get("out_path")
            video_path = item.get("video_path")
            caption = item.get("caption", "Trending News Update")
            
            target_file = video_path if (video_path and os.path.exists(video_path)) else out_path
            print(f"\n[Post {idx}/{total_posts}] Preparing delivery for {os.path.basename(target_file if target_file else '')}...")
            
            if target_file and os.path.exists(target_file):
                # Check if already delivered
                if is_already_sent(target_file, caption):
                    print(f"[Post {idx}/{total_posts}] Already delivered previously. Skipping to prevent duplicate!")
                    continue

                success = False
                attempts = 0
                max_attempts = 3
                
                while not success and attempts < max_attempts:
                    attempts += 1
                    print(f"[Post {idx}/{total_posts}] Sending attempt {attempts}...")
                    success = send_to_telegram(out_path, caption, video_path=video_path)
                    
                    if not success and attempts < max_attempts:
                        print(f"[Post {idx}/{total_posts}] Retrying in 5 seconds...")
                        time.sleep(5)
                
                if success:
                    print(f"[Post {idx}/{total_posts}] Confirmed delivered to Telegram.")
                else:
                    print(f"[Post {idx}/{total_posts}] Delivery failed after {max_attempts} attempts. Aborting workflow.")
                    break
            else:
                print(f"[Post {idx}/{total_posts}] Skipping: Media file not found at {out_path}")
            
            if idx < total_posts:
                print(f"[Post {idx}/{total_posts}] Success confirmed! Waiting 3s safe buffer before Post {idx+1}...")
                time.sleep(3)
                
        print("\nAll processing completed for Telegram delivery.")
    finally:
        release_lock()
