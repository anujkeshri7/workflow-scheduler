from screenshot_downloader import capture_screenshot
import os

out_dir = r"C:\Users\anujk\.gemini\antigravity\brain\368cc599-bca5-425c-bab2-a6e2cde8bfae"

targets = [
    ("https://www.espncricinfo.com", os.path.join(out_dir, "ishan_kishan_zim.jpg")),
    ("https://www.cricbuzz.com", os.path.join(out_dir, "jasprit_bumrah_injury.jpg")),
    ("https://www.bcci.tv", os.path.join(out_dir, "bcci_review_cricket.jpg"))
]

for url, path in targets:
    print(f"Capturing screenshot from {url} to {path}...")
    capture_screenshot(url, path)
