import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from openai_manager import key_manager
from youtube_uploader import YouTubeUploader
from video_generator import VideoGenerator
from audio_converter import TextToSpeech

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_bot.log'),
        logging.StreamHandler()
    ]
)

class AutoCreator:
    def __init__(self):
        self.uploader = YouTubeUploader()
        self.video_gen = VideoGenerator()
        self.tts = TextToSpeech()
        
    def full_pipeline(self):
        """에러 없는 전체 프로세스"""
        try:
            # 1. 콘텐츠 생성
            content = self._generate_content()
            
            # 2. 음성 변환
            audio_path = self.tts.text_to_speech(content)
            
            # 3. 영상 생성
            video_path = self.video_gen.create_shorts(
                audio_path=audio_path,
                duration=int(os.getenv('SHORTS_MAX_DURATION', 60))
            )
            
            # 4. 유튜브 업로드
            self.uploader.upload(
                file_path=video_path,
                title=f"{content[:95]}... #shorts",
                description="AI 자동 생성 콘텐츠 🚀"
            )
            return True
        except Exception as e:
            logging.error(f"🚨 치명적 오류: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true')
    args = parser.parse_args()
    
    if args.auto:
        AutoCreator().full_pipeline()

