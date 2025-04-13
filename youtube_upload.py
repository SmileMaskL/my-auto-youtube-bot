import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError

def upload_video_to_youtube(file_path, title, description):
    try:
        # 구글 인증 정보
        credentials = Credentials(
            token=None,
            refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
        )

        # 유튜브 API 객체 생성
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)

        # 업로드할 비디오 정보
        request_body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["트렌드", "뉴스", "자동 생성"],
                "categoryId": "25",  # News & Politics
            },
            "status": {
                "privacyStatus": "public",  # 공개 설정
            }
        }

        # 파일 경로 절대경로로 변환
        full_path = os.path.abspath(file_path)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {full_path}")

        # 업로드 실행
        media = MediaFileUpload(full_path, mimetype="video/mp4", resumable=True)
        response = youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        ).execute()

        print(f"✅ 유튜브 업로드 완료: https://youtu.be/{response['id']}")

    except RefreshError as e:
        print(f"❌ 인증 실패: {e}")
    except Exception as e:
        print(f"❌ 업로드 중 오류 발생: {e}")

