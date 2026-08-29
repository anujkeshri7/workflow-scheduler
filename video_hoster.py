import os
import requests
import time
import sys
import json

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def upload_to_uguu(file_path):
    """
    Uguu.se - Fast, reliable direct video/mp4 CDN.
    Guaranteed direct link format: https://d.uguu.se/xxxxxx.mp4
    100% compatible with Meta Graph API video downloader.
    """
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://uguu.se/upload",
                files={"files[]": f},
                timeout=45
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("success") and data.get("files"):
                    url = data["files"][0]["url"]
                    print(f"[OK] Video hosted successfully on Uguu: {url}")
                    return url
    except Exception as e:
        print(f"[Uguu Host Error]: {e}, trying fallback...")
    return None


def upload_to_catbox(file_path):
    """Catbox.moe - Secondary CDN fallback."""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=45
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                print(f"[OK] Video hosted successfully on Catbox: {url}")
                return url
    except Exception as e:
        print(f"[Catbox Error]: {e}, trying fallback...")
    return None


def upload_to_litterbox(file_path, duration="72h"):
    """Litterbox - 72 hours guaranteed retention."""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": duration},
                files={"fileToUpload": f},
                timeout=45
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                print(f"[OK] Video hosted successfully on Litterbox ({duration}): {url}")
                return url
    except Exception as e:
        print(f"[Litterbox Error]: {e}")
    return None


def upload_video_to_public_host(file_path):
    """
    Uploads MP4 video to high-speed public host and returns direct HTTPS URL for Meta API.
    Multi-tier architecture:
    1. Uguu.se (Primary, verified Meta Graph API compatibility)
    2. Catbox.moe (Secondary)
    3. Litterbox (72h guaranteed)
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Hosting {filename} ({file_size_mb:.2f} MB) online for Meta Graph API...")

    # 1. Primary: Uguu
    url = upload_to_uguu(file_path)
    if url:
        return url

    # 2. Secondary: Catbox
    url = upload_to_catbox(file_path)
    if url:
        return url

    # 3. Tertiary: Litterbox 72h
    url = upload_to_litterbox(file_path, "72h")
    if url:
        return url

    print("[FAIL] Failed to upload video to all hosting providers.")
    return None


if __name__ == "__main__":
    test_video = r"C:\Users\anujk\.gemini\antigravity\brain\7b4b9559-4f47-4289-86db-8faa5758ca67\news1_reel.mp4"
    if os.path.exists(test_video):
        url = upload_video_to_public_host(test_video)
        print("Final Direct URL:", url)
