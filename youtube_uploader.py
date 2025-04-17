import os
import json
import logging
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from quota_manager import quota_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/youtube_upload.log'),
        logging.StreamHandler()
    ]
)

class YouTubeUploader:
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    API_SERVICE_NAME = 'youtube'
    API_VERSION = 'v3'
    
    def __init__(self):
        self.credentials = self._get_credentials()
        self.youtube = self._get_youtube_service()
        self.max_retries = 3

    def _get_credentials(self):
        """자격증명 로드 (수정된 버전)"""
        try:
            creds_json = os.getenv('GOOGLE_CREDS')
            if creds_json:
                return Credentials.from_authorized_user_info(json.loads(creds_json), self.SCOPES)
            
            secrets_json = os.getenv('YOUTUBE_CLIENT_SECRETS_JSON')
            if secrets_json:
                return Credentials.from_authorized_user_info(json.loads(secrets_json), self.SCOPES)
                
            raise ValueError("No valid credentials found")
        except Exception as e:
            logging.error(f"자격증명 로드 실패: {e}")
            raise

    def _get_youtube_service(self):
        """YouTube 서비스 생성"""
        if not self.credentials:
            raise ValueError("유효한 자격증명이 없습니다")
        return build(self.API_SERVICE_NAME, self.API_VERSION, credentials=self.credentials)

    def upload_video(self, video_path: str, title: str, description: str, thumbnail_path: str) -> str:
        """업로드 로직 (에러 처리 강화)"""
        for attempt in range(1, self.max_retries+1):
            try:
                if not quota_manager.check_quota('youtube'):
                    raise RuntimeError("YouTube API quota exceeded")
                
                body = {
                    'snippet': {
                        'title': title[:100],  # 제한 길이 적용
                        'description': description[:5000],
                        'tags': ['AI', '자동생성', '쇼츠'],
                        'categoryId': '28'
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False
                    }
                }

                media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True)
                request = self.youtube.videos().insert(
                    part='snippet,status',
                    body=body,
                    media_body=media
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        logging.info(f"업로드 진행률: {int(status.progress() * 100)}%")

                video_id = response['id']
                self._upload_thumbnail(video_id, thumbnail_path)
                self._add_comment(video_id, "이 영상은 AI로 자동 생성되었습니다. 👍")
                
                quota_manager.update_usage('youtube', 1600)
                return video_id

            except Exception as e:
                logging.warning(f"시도 {attempt} 실패: {str(e)}")
                if attempt == self.max_retries:
                    raise
                time.sleep(attempt * 5)

youtube_uploader = YouTubeUploader()
