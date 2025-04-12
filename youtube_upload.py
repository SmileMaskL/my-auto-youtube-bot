from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import os
import time

def upload_video(video_path, title, description, tags):
    # 필수 환경 변수 검증
    required_env_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'GOOGLE_REFRESH_TOKEN'
    ]
    missing = [var for var in required_env_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"⚠️ 필수 환경 변수 누락: {', '.join(missing)}")

    # 3회 재시도 로직
    for attempt in range(3):
        try:
            # Google 인증 정보 생성
            creds = Credentials(
                token=None,
                refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
            )
            
            # YouTube API 초기화
            youtube = build("youtube", "v3", credentials=creds)
            
            # 메타데이터 설정 (YouTube 정책 준수)
            request_body = {
                "snippet": {
                    "categoryId": "22",
                    "title": title[:95] + "..." if len(title) > 100 else title,
                    "description": description[:4500],
                    "tags": tags[:30]
                },
                "status": {"privacyStatus": "public"}
            }
            
            # 영상 업로드
            media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
            response = youtube.videos().insert(
                part="snippet,status",
                body=request_body,
                media_body=media
            ).execute()
            
            print(f"✅ 업로드 성공! 영상 URL: https://youtu.be/{response['id']}")
            return
        except HttpError as e:
            print(f"⚠️ YouTube API 오류 ({attempt+1}/3): {str(e)[:100]}")
            time.sleep(10)
        except Exception as e:
            print(f"⚠️ 업로드 실패 ({attempt+1}/3): {str(e)[:100]}")
            time.sleep(10)
    print("🚨 모든 업로드 시도 실패")
