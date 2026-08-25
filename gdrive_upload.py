import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'
FOLDER_ID = '1N6lwSoKepV-_zPFH-QIYOET9Z-sioWCM'

def upload_to_drive(file_paths):
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Failed to authenticate with Google Drive: {e}")
        return

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"File not found, skipping: {file_path}")
            continue
            
        file_name = os.path.basename(file_path)
        print(f"Uploading {file_name} to Google Drive...")
        
        file_metadata = {
            'name': file_name,
            'parents': [FOLDER_ID]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        
        try:
            file = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
            print(f"✅ Successfully uploaded {file_name}. File ID: {file.get('id')}")
        except Exception as e:
            print(f"Error uploading {file_name}: {e}")

if __name__ == '__main__':
    # Manual test execution for the current generated files
    files = [
        r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\news1_final.png",
        r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\news2_final.png",
        r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\news3_final.png",
        r"C:\Users\anujk\.gemini\antigravity\brain\f4819205-6f5e-4104-b950-3022c5d56d1a\daily_schedule_output.md"
    ]
    upload_to_drive(files)
