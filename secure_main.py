import os
import json
import logging
import time
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from trending import get_trending_topic
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_speech
from secure_generate_video import generate_video
from youtube_uploader import upload_video_to_youtube, log_upload
from quota_manager import quota_manager

# 환경 변수 설정
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='secure_log.txt',
    filemode='a'
)
logger = logging.getLogger(__name__)

def authenticate_youtube_api():
    """YouTube API 인증 및 서비스 객체 반환"""
    creds = None
    try:
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logger.info("Loaded existing credentials")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Starting new authentication flow")
                client_secret_json = os.getenv('YOUTUBE_CLIENT_SECRETS_JSON')
                if client_secret_json:
                    client_config = json.loads(client_secret_json)
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                else:
                    raise ValueError("Client secret not found in environment variables")
                
                if os.getenv('CI'):
                    logger.info("Running in CI environment")
                    token_json = os.getenv('GOOGLE_TOKEN_JSON')
                    if token_json:
                        creds = Credentials.from_authorized_user_info(json.loads(token_json))
                else:
                    creds = flow.run_local_server(port=8080, open_browser=False)

            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise

def main_workflow():
    """전체 자동화 워크플로우 실행"""
    logger.info("Starting automated workflow")
    
    try:
        # 1. 트렌드 주제 수집
        topic = get_trending_topic()
        logger.info(f"Selected trending topic: {topic}")
        
        # 2. 스크립트 생성
        script = generate_script(topic)
        logger.info(f"Generated script: {script[:100]}...")
        
        # 3. 오디오 생성
        audio_path = text_to_speech(
            text=script,
            voice_id=os.getenv('ELEVENLABS_VOICE_ID'),
            output_folder="static/audio"
        )
        logger.info(f"Generated audio: {audio_path}")
        
        # 4. 영상 생성
        video_path, thumbnail_path, duration = generate_video(
            topic_title=topic,
            audio_path=audio_path,
            output_folder="static/video"
        )
        logger.info(f"Generated video: {video_path}")
        
        # 5. 유튜브 업로드
        youtube = authenticate_youtube_api()
        video_id = upload_video_to_youtube(
            youtube=youtube,
            file_path=video_path,
            title=f"{topic} #Shorts",
            description=f"{script}\n\n{SHORTS_HASHTAGS}",
            thumbnail_path=thumbnail_path,
            is_shorts=True
        )
        logger.info(f"Uploaded video ID: {video_id}")
        
        # 6. 업로드 로깅
        log_upload(video_id, topic, script)
        logger.info("Workflow completed successfully")
        
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise

if __name__ == "__main__":
    main_workflow()

