import requests
import os

images = {
    "ishan_kishan_zim.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Ishan_Kishan_promoting_Brahmastra.jpg/800px-Ishan_Kishan_promoting_Brahmastra.jpg",
    "jasprit_bumrah_injury.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Jasprit_Bumrah_%28cropped%29.jpg/800px-Jasprit_Bumrah_%28cropped%29.jpg",
    "bcci_review_cricket.jpg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Wankhede_Stadium_Panorama_IPL_2023.jpg/1280px-Wankhede_Stadium_Panorama_IPL_2023.jpg"
}

out_dir = r"C:\Users\anujk\.gemini\antigravity\brain\368cc599-bca5-425c-bab2-a6e2cde8bfae"

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for filename, url in images.items():
    dest_path = os.path.join(out_dir, filename)
    print(f"Downloading {filename} from {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            with open(dest_path, 'wb') as f:
                f.write(r.content)
            print(f"Successfully saved to {dest_path}")
        else:
            print(f"Failed with status code {r.status_code}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
