from screenshot_downloader import capture_screenshot
import os

out_dir = r"C:\Users\anujk\.gemini\antigravity\brain\368cc599-bca5-425c-bab2-a6e2cde8bfae"

targets = [
    ("https://openai.com", os.path.join(out_dir, "openai_gpt5.jpg")),
    ("https://www.anthropic.com", os.path.join(out_dir, "claude_opus5.jpg")),
    ("https://about.meta.com", os.path.join(out_dir, "meta_muse_spark.jpg"))
]

for url, path in targets:
    print(f"Capturing AI screenshot from {url} to {path}...")
    capture_screenshot(url, path)
