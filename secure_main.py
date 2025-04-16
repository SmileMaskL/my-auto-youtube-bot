import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from openai_rotator import key_rotator
from youtube_manager import YouTubeAutomator
from video_engine import VideoGenerator
from audio_engine import TextToSpeechConverter
from thumbnail_generator import ThumbnailCreator

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

class UltimateAutoBot:
    def __init__(self):
        self.youtube = YouTubeAutomator()
        self.video_gen = VideoGenerator()
        self.tts = TextToSpeechConverter()
        self.thumbnail = ThumbnailCreator()
        self._setup_dirs()

    def _setup_dirs(self):
        """디렉토리 초기화"""
        os.makedirs('static/videos', exist_ok=True)
        os.makedirs('static/audio', exist_ok=True)
        os.makedirs('static/thumbnails', exist_ok=True)
        os.makedirs('logs', exist_ok=True)

    def _generate_content(self) -> str:
        """AI 콘텐츠 생성"""
        # 실제 구현 필요 (예: GPT-4 호출)
        return "이것은 샘플 콘텐츠입니다. 실제 구현에서 교체하세요."

    def run_pipeline(self):
        """에러 없는 전체 프로세스"""
        try:
            # 1. 콘텐츠 생성
            content = self._generate_content()
            
            # 2. 음성 변환
            audio_path = self.tts.text_to_speech(content)
            
            # 3. 영상 생성
            video_path = self.video_gen.create_shorts(
                audio_path=audio_path,
                duration=int(os.getenv('SHORTS_DURATION', 60))
            )
            
            # 4. 썸네일 생성
            thumbnail_path = self.thumbnail.generate(video_path)
            
            # 5. 유튜브 업로드
            self.youtube.upload(
                video_path=video_path,
                title=f"{content[:95]}... #shorts",
                thumbnail_path=thumbnail_path,
                comment="🤖 AI가 생성한 콘텐츠"
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
        bot = UltimateAutoBot()
        success = bot.run_pipeline()
        sys.exit(0 if success else 1)

