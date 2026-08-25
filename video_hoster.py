import os
import requests
import time
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def upload_video_to_public_host(file_path):
    """
    Uploads MP4 video to high-speed public host and returns direct HTTPS URL for Meta API.
    Uses Catbox as primary, with Tmpfiles & Litepub as automatic fallbacks.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Hosting {filename} ({file_size_mb:.2f} MB) online for Meta Graph API...")

    # Strategy 1: Catbox.moe (Fast, reliable direct CDN)
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=30
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                public_url = res.text.strip()
                print(f"[OK] Video hosted successfully on Catbox: {public_url}")
                return public_url
    except Exception as e:
        print(f"[Catbox Error]: {e}, trying fallback...")

    # Strategy 2: Tmpfiles.org
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": f},
                timeout=30
            )
            if res.status_code == 200:
                data = res.json()
                raw_url = data.get("data", {}).get("url", "")
                if raw_url:
                    public_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    print(f"[OK] Video hosted successfully on Tmpfiles: {public_url}")
                    return public_url
    except Exception as e:
        print(f"[Tmpfiles Error]: {e}, trying fallback...")

    print("[FAIL] Failed to upload video to public host.")
    return None

if __name__ == "__main__":
    test_video = r"C:\Users\anujk\.gemini\antigravity\brain\7b4b9559-4f47-4289-86db-8faa5758ca67\news1_reel.mp4"
    if os.path.exists(test_video):
        url = upload_video_to_public_host(test_video)
        print("Final Direct URL:", url)
