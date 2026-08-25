import json
import time
import os
from telegram_sender import send_to_telegram

DATA_FILE = "daily_news_data.json"

if not os.path.exists(DATA_FILE):
    print(f"Error: {DATA_FILE} not found.")
    exit(1)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

posts = data.get("posts", [])

for i, item in enumerate(posts, 1):
    out_path = item.get("out_path")
    caption = item.get("caption", "AI News Update")
    
    print(f"--- Sending Post {i}/{len(posts)} to Telegram ---")
    if out_path and os.path.exists(out_path):
        success = send_to_telegram(out_path, caption)
        if success:
            print(f"SUCCESS: Post {i} delivered!")
        else:
            print(f"FAILED: Post {i}")
    else:
        print(f"Skipping Post {i}: File not found ({out_path})")
    
    if i < len(posts):
        print("Waiting 3 seconds before sending next post...")
        time.sleep(3)

print("All recreated AI posts sent one by one to Telegram!")
