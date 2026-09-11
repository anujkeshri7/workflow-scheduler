"""
instant_publisher.py  —  Local Instagram Publisher (no GitHub scheduler needed)

USAGE:
  python instant_publisher.py               -> publish post #1 from daily batch, save 2 & 3 locally
  python instant_publisher.py --remaining   -> publish next post from local_pending_posts.json
  python instant_publisher.py --status      -> show remaining local posts
"""
import os, sys, json, time, datetime, re, requests
from dotenv import load_dotenv
load_dotenv()

META_TOKEN = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GRAPH_VERSION = "v19.0"
DATA_FILE = "daily_news_data.json"
PENDING_FILE = "local_pending_posts.json"

def ist():
    tz = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %I:%M %p IST")

def telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML",
                  "disable_web_page_preview": True}, timeout=20)
    except: pass

def upload_video(path):
    from video_hoster import upload_video_to_public_host
    if not path or not os.path.exists(path):
        print(f"[ERROR] Video not found: {path}"); return None
    return upload_video_to_public_host(path)

def publish_reel(video_url, caption):
    if not META_TOKEN or not IG_ACCOUNT_ID:
        print("[ERROR] META credentials missing in .env"); return None
    clean = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', r'\2 (\1)', caption)
    print("  [1/3] Creating container...")
    c = requests.post(f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media",
        data={"media_type":"REELS","video_url":video_url,"caption":clean,
              "access_token":META_TOKEN}, timeout=30).json()
    cid = c.get("id")
    if not cid:
        print(f"  [FAIL] {c}"); return None
    print(f"  [OK] Container {cid} — polling...")
    for i in range(1,19):
        s = requests.get(f"https://graph.facebook.com/{GRAPH_VERSION}/{cid}",
            params={"fields":"status_code","access_token":META_TOKEN}, timeout=20).json()
        st = s.get("status_code","").upper()
        if st == "FINISHED": print(f"  [OK] Ready ({i*5}s)"); break
        if st in ["ERROR","EXPIRED"]: print(f"  [FAIL] {s}"); return None
        time.sleep(5)
    print("  [3/3] Publishing live...")
    p = requests.post(f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_ACCOUNT_ID}/media_publish",
        data={"creation_id":cid,"access_token":META_TOKEN}, timeout=30).json()
    mid = p.get("id")
    if mid: print(f"  [SUCCESS] Live! Media ID: {mid}"); return mid
    print(f"  [FAIL] {p}"); return None

def load_pending():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def save_pending(posts):
    with open(PENDING_FILE,"w",encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

def show_status():
    pending = load_pending()
    print("\n" + "="*55)
    if not pending:
        print("  No local pending posts. Run workflow to create new ones.")
    else:
        print(f"  {len(pending)} post(s) waiting locally:\n")
        for i,p in enumerate(pending,1):
            h = p.get("headline","").replace("\n"," ")[:55]
            print(f"  [{i}] {h}")
    print("="*55 + "\n")
    return len(pending)

def publish_first_from_daily():
    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] {DATA_FILE} not found. Run workflow first."); return
    with open(DATA_FILE,"r",encoding="utf-8") as f: data = json.load(f)
    posts = data.get("posts",[])
    if not posts: print("[ERROR] No posts in data file"); return

    print(f"\n{'='*55}\n  INSTANT PUBLISHER  |  {ist()}\n{'='*55}")

    first = posts[0]
    headline = first.get("headline","").replace("\n"," ")
    video_path = first.get("video_path","")
    caption = first.get("caption","")
    print(f"\n Publishing Post #1: {headline[:55]}")

    url = upload_video(video_path)
    if not url: print("[FAIL] Upload failed. Aborting."); return
    print(f"  CDN URL: {url}")
    first["public_video_url"] = url

    mid = publish_reel(url, caption)
    if not mid: print("[FAIL] Instagram publish failed."); return

    first["ig_media_id"] = mid
    first["published_at_ist"] = ist()
    first["status"] = "PUBLISHED"
    data["posts"][0] = first
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    telegram(f"<b>Instagram Reel Live!</b>\n\n<b>{headline}</b>\nMedia ID: <code>{mid}</code>\n{ist()}")

    remaining = posts[1:]
    existing = load_pending()
    save_pending(existing + remaining)

    print(f"\n{'='*55}")
    print(f"  POST #1 PUBLISHED LIVE ON INSTAGRAM!")
    count = len(remaining)
    if count:
        print(f"  {count} post(s) saved locally (not published):")
        for i,p in enumerate(remaining,2):
            h = p.get("headline","").replace("\n"," ")[:55]
            print(f"    Post #{i}: {h}")
        print(f"\n  Say 'publish 2nd' or 'publish remaining' in chat to post next.")
    print("="*55 + "\n")

def publish_next_pending():
    pending = load_pending()
    if not pending:
        print("\n[INFO] No local pending posts. Run new workflow.\n"); return False
    post = pending[0]
    rest = pending[1:]
    headline = post.get("headline","").replace("\n"," ")
    video_path = post.get("video_path","")
    caption = post.get("caption","")
    print(f"\n{'='*55}\n  Publishing Next Pending Post  |  {ist()}\n{'='*55}")
    print(f"\n  {headline[:55]}")

    url = upload_video(video_path)
    if not url: print("[FAIL] Upload failed."); return False
    print(f"  CDN: {url}")
    mid = publish_reel(url, caption)
    if not mid: print("[FAIL] Instagram publish failed."); return False

    post["ig_media_id"] = mid; post["published_at_ist"] = ist(); post["status"] = "PUBLISHED"
    save_pending(rest)
    telegram(f"<b>Instagram Reel Live!</b>\n\n<b>{headline}</b>\nMedia ID: <code>{mid}</code>\n{ist()}")
    print(f"\n  PUBLISHED! {len(rest)} post(s) still remaining locally.")
    if rest:
        for i,p in enumerate(rest,1):
            h = p.get("headline","").replace("\n"," ")[:50]
            print(f"    [{i}] {h}")
    print("="*55 + "\n"); return True

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv)>1 else ""
    if mode == "--status":   show_status()
    elif mode == "--remaining": show_status() or 1; publish_next_pending()
    else: publish_first_from_daily()
