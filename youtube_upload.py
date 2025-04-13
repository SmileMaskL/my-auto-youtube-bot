import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

CLIENT_SECRET_JSON = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


def upload_video(file_path, title, description):
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ["트렌드", "자동 콘텐츠"],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public'
        }
    }

    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
    request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
    response = request.execute()
    print("Video ID:", response.get("id"))
