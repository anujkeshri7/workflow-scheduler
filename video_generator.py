import os
import subprocess
import json
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from music_fetcher import fetch_trending_audio

MUSIC_MAP = {
    "breaking": "breaking_alert.mp3",
    "controversy": "breaking_alert.mp3",
    "politics": "politics_anthem.mp3",
    "business": "business_hustle.mp3",
    "tech": "cyber_synth.mp3",
    "robotics": "cyber_synth.mp3",
    "drama": "cinematic_drama.mp3",
    "film": "cinematic_drama.mp3",
    "sports": "business_hustle.mp3",
    "cricket": "business_hustle.mp3",
    "athletics": "politics_anthem.mp3"
}

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")

def get_audio_track_for_post(item):
    # 0. Check explicit direct audio file path
    direct_audio = item.get("audio_path")
    if direct_audio and os.path.exists(direct_audio):
        print(f"[OK] Applied direct real song: {os.path.basename(direct_audio)}")
        return direct_audio

    # 1. Check if explicit custom music query or song is requested
    music_query = item.get("music_query") or item.get("song_name")
    if music_query:
        print(f"Checking trending audio for query: '{music_query}'...")
        custom_audio = fetch_trending_audio(music_query, duration=8.5)
        if custom_audio and os.path.exists(custom_audio):
            print(f"[OK] Applied custom trending audio: {os.path.basename(custom_audio)}")
            return custom_audio

    # 2. Check category keywords against preset library
    category = item.get("category", "").lower()
    for key, track in MUSIC_MAP.items():
        if key in category:
            path = os.path.join(MUSIC_DIR, track)
            if os.path.exists(path):
                print(f"[OK] Applied category preset audio: {track}")
                return path
                
    # 3. Check template against preset library
    template = item.get("template", "").lower()
    track = MUSIC_MAP.get(template, "default.mp3")
    path = os.path.join(MUSIC_DIR, track)
    if os.path.exists(path):
        print(f"[OK] Applied template preset audio: {track}")
        return path
        
    return os.path.join(MUSIC_DIR, "default.mp3")


def create_reel_video(image_path, audio_path, output_mp4, duration=8.5):
    """
    Converts 1080x1350 image post into a 9:16 (1080x1920) Fullscreen Instagram Reel.
    - Blurred, darkened 1080x1920 background layer
    - Centered crisp 1080x1350 news card
    - Matched audio track with smooth fades
    """
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return False
        
    if not os.path.exists(audio_path):
        audio_path = os.path.join(MUSIC_DIR, "default.mp3")
        
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)
    
    filter_complex = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "gblur=sigma=32,eq=brightness=-0.25:contrast=0.85[bg];"
        "[0:v]scale=1080:1350[fg];"
        "[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2[v];"
        "[1:a]afade=t=in:ss=0:d=0.4,afade=t=out:st=" + str(duration - 1.5) + ":d=1.5[a]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(duration),
        output_mp4
    ]
    
    print(f"Rendering 9:16 Reel: {os.path.basename(image_path)} -> {os.path.basename(output_mp4)}...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0 and os.path.exists(output_mp4):
        size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
        print(f"[OK] Rendered Reel Video: {output_mp4} ({size_mb:.2f} MB)")
        return True
    else:
        print(f"[FAIL] FFmpeg error: {res.stderr.decode('utf-8', errors='ignore')}")
        return False


def generate_reels_from_data_file(data_file="daily_news_data.json"):
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        return []
        
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    rendered_videos = []
    for idx, post in enumerate(data.get("posts", []), 1):
        img_path = post.get("out_path", "")
        if not img_path or not os.path.exists(img_path):
            img_path = post.get("image_path", "")
            
        out_dir = os.path.dirname(img_path)
        base_name = f"news{idx}_reel.mp4"
        video_out = os.path.join(out_dir, base_name)
        
        audio_track = get_audio_track_for_post(post)
        success = create_reel_video(img_path, audio_track, video_out, duration=8.5)
        if success:
            post["video_path"] = video_out
            rendered_videos.append(video_out)
            
    # Save back updated json with video paths
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return rendered_videos


if __name__ == "__main__":
    videos = generate_reels_from_data_file()
    print(f"Total Reels Generated: {len(videos)}")
