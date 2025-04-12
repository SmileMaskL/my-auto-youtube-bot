import os
import base64
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

def get_authenticated_service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )
    return build('youtube', 'v3', credentials=creds)

def upload_video(file_path, title, description):
    youtube = get_authenticated_service()

    request_body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['트렌드', 'shorts', '뉴스', '이슈'],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)

    print("📤 유튜브에 업로드 중...")
    response = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    ).execute()

    print("✅ 업로드 완료: ", response.get("id"))

