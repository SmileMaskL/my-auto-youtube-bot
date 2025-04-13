import os
import pickle
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

def upload_video_to_youtube(video_file, title, description):
    try:
        creds = Credentials(
            token=None,
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
        )
        if not creds.valid and creds.refresh_token:
            creds.refresh(Request())

        youtube = build("youtube", "v3", credentials=creds)

        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["트렌드", "뉴스", "AI", "자동화"],
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": "public"
            }
        }

        media_body = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype='video/*')

        upload_request = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media_body
        )
        response = upload_request.execute()
        print("✅ YouTube 업로드 완료:", response["id"])

    except HttpError as e:
        print(f"❌ YouTube 업로드 오류: {e}")

