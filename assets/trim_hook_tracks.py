import subprocess
import os

CUSTOM_DIR = os.path.join(os.path.dirname(__file__), "music", "custom")
os.makedirs(CUSTOM_DIR, exist_ok=True)

TRACKS = [
    # 1. KGF Action Hook (Starts directly on the loud gun/brass beat drop)
    {
        "src": os.path.join(CUSTOM_DIR, "kgf_action_theme.mp3"),
        "out": os.path.join(CUSTOM_DIR, "hook_kgf_action.mp3"),
        "ss": 19.5,
        "duration": 8.5,
        "volume": "volume=1.5"
    },
    # 2. Cyberpunk Future Tech Beat (Starts directly on the loud synth bass drop)
    {
        "src": os.path.join(CUSTOM_DIR, "cyber_future_tech.mp3"),
        "out": os.path.join(CUSTOM_DIR, "hook_cyber_tech.mp3"),
        "ss": 45.0,
        "duration": 8.5,
        "volume": "volume=1.6"
    },
    # 3. A.R. Rahman Vande Mataram (Starts directly on the high-energy "Vande Mataram" chorus)
    {
        "src": os.path.join(CUSTOM_DIR, "ar_rahman_vande_mataram.mp3"),
        "out": os.path.join(CUSTOM_DIR, "hook_vande_mataram.mp3"),
        "ss": 58.0,
        "duration": 8.5,
        "volume": "volume=1.4"
    }
]

def make_hooks():
    for t in TRACKS:
        if not os.path.exists(t["src"]):
            print(f"Missing {t['src']}")
            continue
            
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(t["ss"]),
            "-i", t["src"],
            "-t", str(t["duration"]),
            "-af", f"{t['volume']},afade=t=in:ss=0:d=0.05,afade=t=out:st=7.2:d=1.3",
            "-b:a", "192k",
            t["out"]
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and os.path.exists(t["out"]):
            print(f"[OK] Created instant beat-drop hook: {os.path.basename(t['out'])} ({os.path.getsize(t['out'])} bytes)")
        else:
            print(f"[FAIL] Error: {res.stderr.decode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    make_hooks()
