import os
import json
import requests
import datetime
from dotenv import load_dotenv
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()
META_TOKEN = os.getenv('META_ACCESS_TOKEN')
IG_ACCOUNT_ID = os.getenv('IG_ACCOUNT_ID')

def diagnose_setup():
    print("\n=======================================================")
    print("      Instagram & Meta API Diagnostic Checker")
    print("=======================================================\n")
    
    # 1. Check .env existence and variables
    if not os.path.exists(".env"):
        print("[ERROR] .env file not found in current directory.")
        return False
        
    print(f"1. Checking Environment Variables in .env:")
    print(f"   - IG_ACCOUNT_ID    : {'[SET] ' + str(IG_ACCOUNT_ID) if IG_ACCOUNT_ID else '[MISSING]'}")
    print(f"   - META_ACCESS_TOKEN: {'[SET] ' + META_TOKEN[:15] + '...' if META_TOKEN else '[MISSING]'}")
    
    if not META_TOKEN:
        print("\n[ACTION REQUIRED] Please add your META_ACCESS_TOKEN in .env")
        return False
        
    # 2. Test Token Validity & Permissions with Graph API
    print("\n2. Querying Meta Graph API for Token Status...")
    try:
        res = requests.get(f"https://graph.facebook.com/v19.0/me?fields=id,name&access_token={META_TOKEN}", timeout=15)
        data = res.json()
        
        if 'error' in data:
            err = data['error']
            msg = err.get('message', '')
            code = err.get('code')
            subcode = err.get('error_subcode')
            
            print(f"\n[X] Meta Token Invalid or Expired:")
            print(f"    Code: {code} (Subcode: {subcode})")
            print(f"    Message: {msg}")
            
            print("\n-------------------------------------------------------")
            print("  HOW TO GET A FRESH META ACCESS TOKEN (2-Minute Steps)")
            print("-------------------------------------------------------")
            print("1. Go to Meta Graph API Explorer: https://developers.facebook.com/tools/explorer/")
            print("2. In 'Meta App', select your App.")
            print("3. In 'User or Page', select your connected Facebook Page (Page Access Token).")
            print("4. In 'Permissions', ensure you add:")
            print("   - instagram_basic")
            print("   - instagram_content_publish")
            print("   - pages_show_list")
            print("   - pages_read_engagement")
            print("5. Click 'Generate Access Token'.")
            print("6. (Optional for 60-Day Token) Go to Access Token Debugger:")
            print("   https://developers.facebook.com/tools/debug/accesstoken/")
            print("   Paste token and click 'Extend Access Token'.")
            print("7. Paste the generated token into your .env file as:")
            print("   META_ACCESS_TOKEN=<your_new_token>")
            print("-------------------------------------------------------\n")
            return False
            
        print(f"[OK] Token is VALID! Connected User/Entity: '{data.get('name')}' (ID: {data.get('id')})")
        
        # 3. Check Connected Pages and Instagram Business Account
        print("\n3. Checking Linked Facebook Pages & Instagram Business ID...")
        p_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?fields=name,instagram_business_account&access_token={META_TOKEN}", timeout=15)
        p_data = p_res.json()
        
        pages = p_data.get('data', [])
        if not pages:
            print("   [WARNING] No Facebook Pages found for this token. Make sure you use a Page Access Token.")
        else:
            for p in pages:
                p_name = p.get('name')
                ig_biz = p.get('instagram_business_account')
                print(f"   - Found Page: '{p_name}'")
                if ig_biz:
                    ig_id = ig_biz.get('id')
                    print(f"     [OK] Linked Instagram Business ID: {ig_id}")
                    if str(ig_id) == str(IG_ACCOUNT_ID):
                        print("     [MATCH] Matches IG_ACCOUNT_ID in .env!")
                    else:
                        print(f"     [UPDATE] Update .env with: IG_ACCOUNT_ID={ig_id}")
                else:
                    print("     [X] No Instagram Business Account linked to this page.")
                    
        print("\n[SUCCESS] Meta Graph API Setup is ready for Auto-Publishing and Cloud Scheduling!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to connect to Meta API: {e}")
        return False

if __name__ == "__main__":
    diagnose_setup()
