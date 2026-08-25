import os
from instagrapi import Client
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()
USERNAME = os.getenv('IG_USERNAME')
PASSWORD = os.getenv('IG_PASSWORD')

def publish_to_instagram(image_path, caption):
    print(f"Logging in to Instagram as {USERNAME}...")
    cl = Client()
    
    try:
        cl.login(USERNAME, PASSWORD)
        print("Login successful!")
        
        print(f"Uploading image: {image_path}")
        media = cl.photo_upload(
            image_path,
            caption
        )
        print(f"Post successfully published! Media ID: {media.id}")
        return True
    except Exception as e:
        print(f"An error occurred while publishing: {e}")
        return False

if __name__ == '__main__':
    # This block is for testing.
    # Replace with a real test image path and caption when testing.
    test_image = r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\news1_ready.png"
    test_caption = "Testing automated posting! 🚀 #news #test"
    
    if os.path.exists(test_image) and PASSWORD != 'your_password_here':
        publish_to_instagram(test_image, test_caption)
    elif PASSWORD == 'your_password_here':
        print("Please update your IG_PASSWORD in the .env file first!")
    else:
        print(f"Test image not found at {test_image}")
