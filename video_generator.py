import os
import subprocess
import json
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "assets", "music")
DEFAULT_CLIP_PATH = os.path.join(os.path.dirname(__file__), "clip.mp4")


def get_clip_duration(clip_path):
    """Get duration of video clip in seconds using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            clip_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return float(res.stdout.strip())
    except Exception as e:
        print(f"Warning: Could not probe clip duration: {e}")
    return 7.1


def create_reel_video(image_path, audio_path=None, output_mp4=None, clip_path=None, duration=None, mix_bg_music=False):
    """
    Creates a 9:16 (1080x1920) Instagram Reel with split layout:
    - UPPER PORTION (0 to 1350 px): 1080x1350 Crisp News Graphic Card
    - BOTTOM PORTION (1350 to 1920 px): 1080x570 Video Clip (e.g. Speed reaction)
    - AUDIO: Video Clip audio at 100% (volume=1.0) with smooth fade-in and fade-out.
             Optional background music mixed at lower volume if mix_bg_music=True.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}")
        return False

    if not output_mp4:
        output_mp4 = image_path.replace(".png", "_reel.mp4")

    os.makedirs(os.path.dirname(os.path.abspath(output_mp4)), exist_ok=True)

    # Resolve clip path
    if not clip_path or not os.path.exists(clip_path):
        if os.path.exists(DEFAULT_CLIP_PATH):
            clip_path = DEFAULT_CLIP_PATH
        else:
            clip_path = None

    # Determine duration
    if duration is None:
        if clip_path and os.path.exists(clip_path):
            clip_dur = get_clip_duration(clip_path)
            # Default to clip duration (max 10s for snappy retention)
            duration = min(clip_dur, 7.5)
        else:
            duration = 7.5

    fade_out_start = max(0.5, duration - 0.8)

    # Case 1: Split layout with Video Clip at bottom
    if clip_path and os.path.exists(clip_path):
        print(f"Applying Split Layout (Top Post + Bottom Clip: {os.path.basename(clip_path)})...")

        if mix_bg_music and audio_path and os.path.exists(audio_path):
            # Mix clip audio at 50% + bg music at 35%
            filter_complex = (
                f"color=c=black:s=1080x1920:d={duration}[base];"
                f"[0:v]scale=1080:1350[top_post];"
                f"[1:v]scale=1080:570:force_original_aspect_ratio=increase,crop=1080:570[bottom_clip];"
                f"[base][top_post]overlay=x=0:y=0[temp];"
                f"[temp][bottom_clip]overlay=x=0:y=1350[v];"
                f"[1:a]volume=0.50[a_clip];"
                f"[2:a]volume=0.35,afade=t=in:ss=0:d=0.02,afade=t=out:st={fade_out_start}:d=0.8[a_bg];"
                f"[a_clip][a_bg]amix=inputs=2:duration=first:dropout_transition=2[a]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-ss", "00:00:00", "-i", clip_path,
                "-i", audio_path,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                output_mp4
            ]
        else:
            # 100% Clip audio (Standard reference style)
            filter_complex = (
                f"color=c=black:s=1080x1920:d={duration}[base];"
                f"[0:v]scale=1080:1350[top_post];"
                f"[1:v]scale=1080:570:force_original_aspect_ratio=increase,crop=1080:570[bottom_clip];"
                f"[base][top_post]overlay=x=0:y=0[temp];"
                f"[temp][bottom_clip]overlay=x=0:y=1350[v];"
                f"[1:a]volume=1.0,afade=t=in:ss=0:d=0.02,afade=t=out:st={fade_out_start}:d=0.8[a]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-ss", "00:00:00", "-i", clip_path,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                output_mp4
            ]

    # Case 2: Fallback (Blurred background with full post card if no clip provided)
    else:
        if not audio_path or not os.path.exists(audio_path):
            audio_path = os.path.join(MUSIC_DIR, "default.mp3")

        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            "gblur=sigma=32,eq=brightness=-0.25:contrast=0.85[bg];"
            "[0:v]scale=1080:1350[fg];"
            "[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2[v];"
            f"[1:a]afade=t=in:ss=0:d=0.02,afade=t=out:st={fade_out_start}:d=0.8[a]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "fast",
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

        clip_path = post.get("clip_path") or DEFAULT_CLIP_PATH
        audio_track = post.get("audio_path")

        success = create_reel_video(
            image_path=img_path,
            audio_path=audio_track,
            output_mp4=video_out,
            clip_path=clip_path,
            duration=7.1,
            mix_bg_music=False
        )
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
