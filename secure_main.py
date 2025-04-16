import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from secure_generate_script import generate_script
from secure_generate_audio import text_to_speech
from secure_generate_video import VideoGenerator
from youtube_uploader import YouTubeUploader
from google_auth import get_authenticated_service
from quota_manager import quota_manager
from openai_rotate import openai_manager

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)

class AutoBot:
    def __init__(self):
        self.video_gen = VideoGenerator()
        self.youtube = None
        
    def initialize_services(self):
        """모든 서비스 초기화"""
        try:
            # Google 인증
            self.youtube = get_authenticated_service()
            logging.info("✅ Services initialized successfully")
        except Exception as e:
            logging.critical(f"🚨 Service initialization failed: {str(e)}")
            sys.exit(1)

    def production_cycle(self):
        """전체 제작 사이클"""
        try:
            # 1. 스크립트 생성
            script = generate_script()
            if not script:
                raise ValueError("Empty script generated")
                
            # 2. 음성 생성
            audio_path = text_to_speech(script)
            
            # 3. 영상 생성
            video_path, thumbnail_path = self.video_gen.create(
                script, 
                audio_path,
                is_shorts=True
            )
            
            # 4. 업로드 실행
            uploader = YouTubeUploader(self.youtube)
            video_id = uploader.upload_video(
                video_path,
                title=script[:100],
                description=script,
                thumbnail_path=thumbnail_path
            )
            
            # 5. 포스트 프로세싱
            uploader.post_comment(video_id, "🤖 이 영상은 AI 자동 생성되었습니다!")
            logging.info(f"📌 Uploaded: https://youtu.be/{video_id}")
            
            return True
            
        except Exception as e:
            logging.error(f"🔴 Production failed: {str(e)}")
            return False

def main(auto_mode=False):
    bot = AutoBot()
    bot.initialize_services()
    
    if auto_mode:
        logging.info("🚀 Starting FULL AUTOMATION MODE")
        success = bot.production_cycle()
        quota_manager.log_status()
        sys.exit(0 if success else 1)
    else:
        logging.info("👋 Manual mode activated")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true')
    args = parser.parse_args()
    main(args.auto)

