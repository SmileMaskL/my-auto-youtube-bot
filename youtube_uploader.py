import os
import logging
import time
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
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
        self.retry_delay = 5

    def _get_credentials(self):
        """Google API 자격증명 가져오기"""
        creds = None
        creds_json = os.getenv('GOOGLE_CREDS')
        
        if creds_json:
            try:
                creds = Credentials.from_authorized_user_info(info=json.loads(creds_json))
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                return creds
            except Exception as e:
                logging.error(f"환경 변수 자격증명 로드 실패: {e}")

        # 환경 변수 실패 시 파일 시도
        secrets_file = 'client_secrets.json'
        if os.path.exists(secrets_file):
            try:
                flow = InstalledAppFlow.from_client_secrets_file(secrets_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
                return creds
            except Exception as e:
                logging.error(f"파일 자격증명 로드 실패: {e}")

        logging.error("Google API 자격증명을 가져올 수 없습니다.")
        return None

    def _get_youtube_service(self):
        """YouTube 서비스 빌드"""
        if not self.credentials:
            raise ValueError("유효한 자격증명이 없습니다.")
        return build(self.API_SERVICE_NAME, self.API_VERSION, credentials=self.credentials)

    def upload_video(self, video_path: str, title: str, description: str, 
                   thumbnail_path: Optional[str] = None) -> Optional[str]:
        """동영상 업로드"""
        if not os.path.exists(video_path):
            logging.error(f"비디오 파일을 찾을 수 없습니다: {video_path}")
            return None

        for attempt in range(self.max_retries):
            if not quota_manager.check_quota('youtube'):
                logging.error("YouTube API 일일 쿼터 초과")
                return None

            try:
                body = {
                    'snippet': {
                        'title': title,
                        'description': description,
                        'tags': ['AI', '자동생성', '쇼츠'],
                        'categoryId': '28'  # 과학기술
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False,
                        'embeddable': True
                    }
                }

                media = MediaFileUpload(
                    video_path,
                    mimetype='video/mp4',
                    chunksize=1024*1024,
                    resumable=True
                )

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
                quota_manager.update_usage('youtube', 1600)  # 비디오 업로드 쿼터

                # 썸네일 업로드
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self._upload_thumbnail(video_id, thumbnail_path)

                # 댓글 추가
                self._add_comment(video_id, "이 영상은 AI로 자동 생성되었습니다. 👍 구독과 좋아요 부탁드립니다!")

                logging.info(f"동영상 업로드 성공! ID: {video_id}")
                return video_id

            except Exception as e:
                logging.error(f"시도 {attempt + 1} 실패: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))

        return None

    def _upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """썸네일 업로드"""
        try:
            media = MediaFileUpload(thumbnail_path, mimetype='image/jpeg')
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logging.info(f"썸네일 업로드 성공: {video_id}")
        except Exception as e:
            logging.error(f"썸네일 업로드 실패: {str(e)}")

    def _add_comment(self, video_id: str, text: str):
        """동영상에 댓글 추가"""
        try:
            self.youtube.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': text
                            }
                        }
                    }
                }
            ).execute()
            logging.info(f"댓글 추가 성공: {video_id}")
        except Exception as e:
            logging.error(f"댓글 추가 실패: {str(e)}")

# YouTube 업로더 인스턴스
youtube_uploader = YouTubeUploader()

if __name__ == "__main__":
    test_video = "static/videos/test_video.mp4"
    test_thumbnail = "static/thumbnails/test_thumbnail.jpg"
    
    if os.path.exists(test_video):
        try:
            video_id = youtube_uploader.upload_video(
                video_path=test_video,
                title="테스트 동영상",
                description="이 동영상은 YouTube 업로더 테스트용입니다.",
                thumbnail_path=test_thumbnail if os.path.exists(test_thumbnail) else None
            )
            if video_id:
                print(f"업로드 성공! 동영상 ID: {video_id}")
                print(f"영상 링크: https://youtu.be/{video_id}")
        except Exception as e:
            print(f"업로드 실패: {e}")
    else:
        print("테스트 비디오 파일이 없습니다. 먼저 비디오를 생성하세요.")
