import os
import urllib.request
import urllib.parse
import json
import base64
from dotenv import load_dotenv
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

load_dotenv()
META_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

import requests

def upload_to_imgbb(image_path):
    print(f"Hosting image online for Meta API...")
    url = "https://envs.sh"
    
    try:
        with open(image_path, "rb") as file:
            files = {'file': file}
            res = requests.post(url, files=files)
            public_url = res.text.strip()
            if public_url.startswith("http"):
                return public_url
            else:
                print(f"Hosting Error: {public_url}")
                return None
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None

def publish_to_instagram(image_path, caption):
    if not IG_ACCOUNT_ID or IG_ACCOUNT_ID == 'your_id_here':
        print("ERROR: IG_ACCOUNT_ID is missing in .env file.")
        return False

    # 1. Bypass Image Host for this test and use a public URL
    # public_image_url = upload_to_imgbb(image_path)
    public_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Geneva_-_United_Nations_-_Palais_des_Nations.jpg/800px-Geneva_-_United_Nations_-_Palais_des_Nations.jpg"
    print(f"Using public image URL for test: {public_image_url}")

    # 2. Create the Media Container (Draft)
    print("Creating media container on Instagram...")
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    data = urllib.parse.urlencode({
        'image_url': public_image_url,
        'caption': caption,
        'access_token': META_TOKEN
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            res = json.loads(response.read())
            creation_id = res.get('id')
            print(f"Container created! ID: {creation_id}")
    except Exception as e:
        print(f"Meta API Error during container creation: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))
        return False

    # Wait a few seconds for Meta's servers to process the image URL
    time.sleep(5)

    # 3. Publish the Container
    print("Publishing container to feed...")
    publish_url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
    publish_data = urllib.parse.urlencode({
        'creation_id': creation_id,
        'access_token': META_TOKEN
    }).encode('utf-8')
    
    pub_req = urllib.request.Request(publish_url, data=publish_data)
    try:
        with urllib.request.urlopen(pub_req, context=ctx) as response:
            pub_res = json.loads(response.read())
            post_id = pub_res.get('id')
            print(f"✅ SUCCESS! Post published to Instagram! Post ID: {post_id}")
            return True
    except Exception as e:
        print(f"Meta API Error during publishing: {e}")
        if hasattr(e, 'read'):
            print(e.read().decode('utf-8'))
        return False

if __name__ == '__main__':
    # Test script if user runs it manually
    test_image = r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\daily_post_ready.png"
    test_caption = "Testing the official Meta API! 🚀 #news #test"
    
    if os.path.exists(test_image):
        publish_to_instagram(test_image, test_caption)
    else:
        print("Test image not found.")
