from screenshot_downloader import capture_screenshot
import os

out_dir = r"C:\Users\anujk\.gemini\antigravity\brain\368cc599-bca5-425c-bab2-a6e2cde8bfae"

targets = [
    ("https://nasa.gov", os.path.join(out_dir, "nasa_return.jpg")),
    ("https://unesco.org", os.path.join(out_dir, "mount_olympus.jpg")),
    ("https://theguardian.com", os.path.join(out_dir, "europe_wildfire.jpg"))
]

for url, path in targets:
    print(f"Capturing World News screenshot from {url} to {path}...")
    capture_screenshot(url, path)
