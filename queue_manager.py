import os
import json
import hashlib
import datetime
import subprocess
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from video_hoster import upload_video_to_public_host

QUEUE_FILE = "posts_queue.json"
DATA_FILE = "daily_news_data.json"

def get_post_id(headline, caption):
    data = f"{headline}:{caption}".encode('utf-8')
    return "post_" + hashlib.md5(data).hexdigest()[:12]

def add_batch_to_queue(data_file=DATA_FILE):
    """
    Reads daily_news_data.json, hosts any local video, and appends to posts_queue.json.
    """
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        return 0

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load existing queue or create new
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                queue_data = json.load(f)
        except Exception:
            queue_data = {"queue_version": "1.0", "pending_posts": [], "published_posts": []}
    else:
        queue_data = {"queue_version": "1.0", "pending_posts": [], "published_posts": []}

    pending = queue_data.get("pending_posts", [])
    published = queue_data.get("published_posts", [])

    # Set of existing IDs to prevent duplicates
    existing_ids = {p.get("id") for p in pending} | {p.get("id") for p in published}

    added_count = 0
    tz_ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_str = datetime.datetime.now(tz_ist).strftime("%Y-%m-%d %I:%M %p IST")

    print(f"\n=======================================================")
    print(f"Adding Batch from {data_file} into Master Queue ({QUEUE_FILE})")
    print(f"=======================================================\n")

    for idx, post in enumerate(data.get("posts", []), 1):
        headline = post.get("headline", "")
        caption = post.get("caption", "")
        post_id = get_post_id(headline, caption)

        if post_id in existing_ids:
            print(f"[Post {idx}] Already in queue / published (ID: {post_id}). Skipping duplicate.")
            continue

        # Ensure video is hosted online
        public_url = post.get("public_video_url")
        if not public_url:
            v_path = post.get("video_path")
            if v_path and os.path.exists(v_path):
                public_url = upload_video_to_public_host(v_path)
                post["public_video_url"] = public_url

        if not public_url:
            print(f"[Post {idx}] Warning: No video URL available for post. Skipping.")
            continue

        queue_item = {
            "id": post_id,
            "template": post.get("template", "default"),
            "category": post.get("category", "NEWS"),
            "headline": headline,
            "subheadline": post.get("subheadline", ""),
            "highlighted_fact": post.get("highlighted_fact", ""),
            "caption": caption,
            "public_video_url": public_url,
            "created_at_ist": now_str,
            "status": "PENDING"
        }

        pending.append(queue_item)
        existing_ids.add(post_id)
        added_count += 1
        print(f"[Post {idx}] ✅ Added to Queue (ID: {post_id}) | Title: {headline[:30]}...")

    queue_data["pending_posts"] = pending
    queue_data["published_posts"] = published

    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    print(f"\nQueue Updated: +{added_count} posts added.")
    print(f"📊 Current Queue Status: {len(pending)} PENDING | {len(published)} PUBLISHED\n")

    # Update daily_news_data.json as well
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Auto sync with Git repository
    sync_queue_to_git()
    return added_count


def sync_queue_to_git():
    """
    Automatically commits and pushes posts_queue.json and daily_news_data.json to GitHub.
    """
    try:
        subprocess.run(["git", "add", "posts_queue.json", "daily_news_data.json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "commit", "-m", "chore: update queue with new news batch"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = subprocess.run(["git", "push", "origin", "main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        if res.returncode == 0:
            print("🚀 Queue automatically synced & pushed to GitHub main branch!")
        else:
            print(f"[Note] Git push pending credentials. Run 'git push -u origin main' in terminal if needed.")
    except Exception as e:
        print(f"[Note] Git sync error: {e}")

if __name__ == "__main__":
    add_batch_to_queue()
