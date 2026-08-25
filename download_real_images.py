import requests
import os

images = {
    "real_news1.jpg": "https://upload.wikimedia.org/wikipedia/commons/7/74/Ranbir_Kapoor_promoting_Brahmastra.jpg",
    "real_news2.jpg": "https://upload.wikimedia.org/wikipedia/commons/9/90/Prabhas_at_Saaho_Pre_Release_Event.jpg",
    "real_news3.jpg": "https://upload.wikimedia.org/wikipedia/commons/7/75/Mohanlal_Viswanathan_Nair_BNC.jpg"
}

out_dir = r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a"

for filename, url in images.items():
    print(f"Downloading {filename}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(os.path.join(out_dir, filename), 'wb') as f:
                f.write(response.content)
            print("Success.")
        else:
            print(f"Failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
