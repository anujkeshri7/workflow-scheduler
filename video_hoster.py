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


def upload_to_github_release(file_path, repo="anujkeshri7/workflow-scheduler"):
    """
    Upload video to GitHub Releases as an asset.
    This gives a PERMANENT direct download URL that never expires.
    Requires GITHUB_TOKEN in environment (auto-available in Actions).
    """
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        return None

    filename = os.path.basename(file_path)
    tag = f"media-{int(time.time())}"

    # Create a release
    try:
        r = requests.post(
            f"https://api.github.com/repos/{repo}/releases",
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json"
            },
            json={
                "tag_name": tag,
                "name": f"Media Asset {filename}",
                "body": "Auto-uploaded media asset for Instagram Reel",
                "draft": False,
                "prerelease": False
            },
            timeout=30
        )
        if r.status_code not in (200, 201):
            return None
        upload_url = r.json()["upload_url"].split("{")[0]

        # Upload the asset
        with open(file_path, "rb") as f:
            r2 = requests.post(
                f"{upload_url}?name={filename}",
                headers={
                    "Authorization": f"token {token}",
                    "Content-Type": "video/mp4"
                },
                data=f,
                timeout=120
            )
            if r2.status_code in (200, 201):
                dl_url = r2.json().get("browser_download_url", "")
                if dl_url:
                    print(f"[OK] Hosted on GitHub Releases (PERMANENT): {dl_url}")
                    return dl_url
    except Exception as e:
        print(f"[GitHub Release Error]: {e}")
    return None


def upload_to_catbox(file_path):
    """Catbox.moe - fast CDN but files MAY expire after ~30 days of no access."""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://catbox.moe/user/api.php",
                data={"reqtype": "fileupload"},
                files={"fileToUpload": f},
                timeout=60
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                print(f"[OK] Hosted on Catbox: {url}")
                return url
    except Exception as e:
        print(f"[Catbox Error]: {e}")
    return None


def upload_to_litterbox(file_path, duration="72h"):
    """Litterbox - temporary host by catbox team, explicit duration (1h, 12h, 24h, 72h)."""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://litterbox.catbox.moe/resources/internals/api.php",
                data={"reqtype": "fileupload", "time": duration},
                files={"fileToUpload": f},
                timeout=60
            )
            if res.status_code == 200 and res.text.strip().startswith("http"):
                url = res.text.strip()
                print(f"[OK] Hosted on Litterbox ({duration}): {url}")
                return url
    except Exception as e:
        print(f"[Litterbox Error]: {e}")
    return None


def upload_to_tmpfiles(file_path):
    """Tmpfiles.org - files expire after ~60 minutes. UNRELIABLE for scheduled posts."""
    try:
        with open(file_path, "rb") as f:
            res = requests.post(
                "https://tmpfiles.org/api/v1/upload",
                files={"file": f},
                timeout=60
            )
            if res.status_code == 200:
                data = res.json()
                raw_url = data.get("data", {}).get("url", "")
                if raw_url:
                    url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                    print(f"[OK] Hosted on Tmpfiles (TEMP ~1hr): {url}")
                    return url
    except Exception as e:
        print(f"[Tmpfiles Error]: {e}")
    return None


def upload_video_to_public_host(file_path):
    """
    Upload video to a public host and return a direct HTTPS URL.
    
    Priority order:
    1. GitHub Releases (PERMANENT, best for scheduled publishing)
    2. Catbox (long-lived, may expire after ~30 days inactivity)
    3. Litterbox 72h (guaranteed 3 days)
    4. Tmpfiles (last resort, ~1 hour only)
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    filename = os.path.basename(file_path)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Hosting {filename} ({file_size_mb:.2f} MB) online for Meta Graph API...")

    # 1. Try GitHub Releases first (permanent)
    url = upload_to_github_release(file_path)
    if url:
        return url

    # 2. Try Catbox
    url = upload_to_catbox(file_path)
    if url:
        return url

    # 3. Try Litterbox with 72h duration
    url = upload_to_litterbox(file_path, "72h")
    if url:
        return url

    # 4. Last resort: Tmpfiles
    url = upload_to_tmpfiles(file_path)
    if url:
        return url

    print("[FAIL] All hosting providers failed.")
    return None


if __name__ == "__main__":
    test_video = r"C:\Users\anujk\.gemini\antigravity\brain\7b4b9559-4f47-4289-86db-8faa5758ca67\news1_reel.mp4"
    if os.path.exists(test_video):
        url = upload_video_to_public_host(test_video)
        print("Final Direct URL:", url)
