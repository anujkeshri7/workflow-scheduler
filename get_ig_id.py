import os
import urllib.request
import json
from dotenv import load_dotenv
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

load_dotenv()
token = os.getenv('META_ACCESS_TOKEN')

if not token or token == 'your_token_here':
    print("ERROR: META_ACCESS_TOKEN not found in .env file.")
    exit(1)

print("Checking Meta Graph API for connected pages...")

url = f"https://graph.facebook.com/v19.0/me/accounts?fields=name,instagram_business_account&access_token={token}"
req = urllib.request.Request(url)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read())
        
        pages = data.get('data', [])
        if not pages:
            print("\nWARNING: No Facebook Pages found connected to this access token.")
            print("Did you select your Facebook Page when generating the token?")
        else:
            for page in pages:
                page_name = page.get('name')
                ig_account = page.get('instagram_business_account')
                
                print(f"\nFound Facebook Page: '{page_name}'")
                if ig_account:
                    ig_id = ig_account.get('id')
                    print(f"✅ SUCCESS! Connected Instagram ID found: {ig_id}")
                    print("You can copy this ID into your .env file!")
                else:
                    print("❌ ERROR: No Instagram Business Account is linked to this Facebook Page.")
                    print("Please open the Instagram app -> Settings -> Business Tools -> Connect or Create a Facebook Page, and ensure it is linked to THIS specific page.")

except Exception as e:
    print(f"API Error: {e}")
