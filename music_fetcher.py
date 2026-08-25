import os
import subprocess
import hashlib
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CUSTOM_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music", "custom")
PRESET_MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")
os.makedirs(CUSTOM_MUSIC_DIR, exist_ok=True)

def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

def fetch_trending_audio(query, duration=8.5, start_offset=30):
    """
    Searches for trending song/music query online, extracts audio,
    and trims a clean 8.5s clip with fades.
    Falls back gracefully if download fails.
    """
    if not query:
        return None

    safe_name = sanitize_filename(query)[:40].strip().replace(' ', '_').lower()
    out_trimmed_mp3 = os.path.join(CUSTOM_MUSIC_DIR, f"{safe_name}.mp3")

    # If already downloaded and cached, return immediately
    if os.path.exists(out_trimmed_mp3) and os.path.getsize(out_trimmed_mp3) > 10000:
        print(f"[OK] Using cached trending audio: {safe_name}.mp3")
        return out_trimmed_mp3

    print(f"Searching and downloading trending audio: '{query}'...")
    raw_temp_mp3 = os.path.join(CUSTOM_MUSIC_DIR, f"temp_{safe_name}.%(ext)s")

    # yt-dlp command to search and fetch top 1 result audio
    cmd_download = [
        "yt-dlp",
        f"ytsearch1:{query}",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "192k",
        "-o", raw_temp_mp3,
        "--no-playlist",
        "--quiet",
        "--no-warnings",
        "--max-filesize", "20M"
    ]

    try:
        res = subprocess.run(cmd_download, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        raw_file = os.path.join(CUSTOM_MUSIC_DIR, f"temp_{safe_name}.mp3")
        
        if os.path.exists(raw_file):
            # Trim best section (8.5s) with smooth fades
            cmd_trim = [
                "ffmpeg", "-y",
                "-ss", str(start_offset),
                "-i", raw_file,
                "-t", str(duration),
                "-af", f"afade=t=in:ss=0:d=0.5,afade=t=out:st={duration - 1.5}:d=1.5",
                "-b:a", "192k",
                out_trimmed_mp3
            ]
            subprocess.run(cmd_trim, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Clean up temp raw file
            try:
                os.remove(raw_file)
            except Exception:
                pass
                
            if os.path.exists(out_trimmed_mp3):
                print(f"[SUCCESS] Downloaded & trimmed audio: {safe_name}.mp3")
                return out_trimmed_mp3
    except Exception as e:
        print(f"[Notice] Online music fetch notice: {e}, falling back to preset.")

    return None

if __name__ == "__main__":
    test_query = "Chak De India Title Song audio"
    path = fetch_trending_audio(test_query)
    print("Fetched Audio Path:", path)
