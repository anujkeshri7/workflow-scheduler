import subprocess
import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")
os.makedirs(MUSIC_DIR, exist_ok=True)

TRACKS = {
    # 1. Breaking Alert: Pulsing alarm sub-bass + urgent rhythmic beat (8.5s)
    "breaking_alert.mp3": [
        "-f", "lavfi", "-i", "anoisesrc=d=8.5:c=pink:r=44100:a=0.06",
        "-f", "lavfi", "-i", "aevalsrc='sin(140*2*PI*t)*0.35+sin(280*2*PI*t)*0.2':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(880*2*PI*t)*gt(mod(t,0.5),0.4)*0.2+sin(1760*2*PI*t)*gt(mod(t,0.25),0.2)*0.1':d=8.5:s=44100",
        "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3,volume=2.2,afade=t=in:ss=0:d=0.5,afade=t=out:st=7.0:d=1.5"
    ],
    # 2. Business Hustle: Upbeat rhythmic chord hits + bass groove (8.5s)
    "business_hustle.mp3": [
        "-f", "lavfi", "-i", "aevalsrc='sin(220*2*PI*t)*gt(mod(t,0.5),0.25)*0.3+sin(440*2*PI*t)*gt(mod(t,0.25),0.15)*0.15':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(110*2*PI*t)*gt(mod(t,1.0),0.3)*0.4+sin(55*2*PI*t)*0.25':d=8.5:s=44100",
        "-f", "lavfi", "-i", "anoisesrc=d=8.5:c=white:r=44100:a=0.03",
        "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3,volume=2.0,afade=t=in:ss=0:d=0.4,afade=t=out:st=7.0:d=1.5"
    ],
    # 3. Cyber Synth: Sci-Fi Arpeggio + sub-frequencies (8.5s)
    "cyber_synth.mp3": [
        "-f", "lavfi", "-i", "aevalsrc='sin(330*2*PI*t)*gt(mod(t*4,1),0.5)*0.25+sin(660*2*PI*t)*gt(mod(t*8,1),0.4)*0.15':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(82.4*2*PI*t)*0.4+sin(164.8*2*PI*t)*0.3':d=8.5:s=44100",
        "-filter_complex", "[0:a][1:a]amix=inputs=2,volume=2.4,afade=t=in:ss=0:d=0.5,afade=t=out:st=7.0:d=1.5"
    ],
    # 4. Politics Anthem: Deep cinematic brass & resonant chords (8.5s)
    "politics_anthem.mp3": [
        "-f", "lavfi", "-i", "aevalsrc='sin(146.8*2*PI*t)*0.35+sin(220*2*PI*t)*0.3+sin(293.6*2*PI*t)*0.25':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(73.4*2*PI*t)*0.45':d=8.5:s=44100",
        "-filter_complex", "[0:a][1:a]amix=inputs=2,volume=2.5,afade=t=in:ss=0:d=0.6,afade=t=out:st=6.8:d=1.7"
    ],
    # 5. Cinematic Drama: Emotional strings & crescendo (8.5s)
    "cinematic_drama.mp3": [
        "-f", "lavfi", "-i", "aevalsrc='sin(174.6*2*PI*t)*0.3+sin(261.6*2*PI*t)*0.25+sin(349.2*2*PI*t)*0.2':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(65.4*2*PI*t)*0.4':d=8.5:s=44100",
        "-filter_complex", "[0:a][1:a]amix=inputs=2,volume=2.4,afade=t=in:ss=0:d=0.8,afade=t=out:st=6.8:d=1.7"
    ],
    # 6. Default News Track (8.5s)
    "default.mp3": [
        "-f", "lavfi", "-i", "aevalsrc='sin(196*2*PI*t)*0.3+sin(293.6*2*PI*t)*0.25+sin(392*2*PI*t)*0.2':d=8.5:s=44100",
        "-f", "lavfi", "-i", "aevalsrc='sin(98*2*PI*t)*0.4':d=8.5:s=44100",
        "-filter_complex", "[0:a][1:a]amix=inputs=2,volume=2.2,afade=t=in:ss=0:d=0.5,afade=t=out:st=7.0:d=1.5"
    ]
}

def generate_presets():
    for filename, ffmpeg_args in TRACKS.items():
        out_path = os.path.join(MUSIC_DIR, filename)
        cmd = ["ffmpeg", "-y"] + ffmpeg_args + ["-b:a", "192k", out_path]
        print(f"Generating audio preset: {filename}...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            print(f"[OK] Generated: {filename} ({os.path.getsize(out_path)} bytes)")
        else:
            print(f"[FAIL] Error generating {filename}: {res.stderr.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    generate_presets()
