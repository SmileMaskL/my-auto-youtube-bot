import os
import logging
import argparse
from dotenv import load_dotenv
from openai_rotate import key_manager
from youtube_manager import YouTubeAutomator

# 환경 초기화
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('debug.log', mode='w'),
        logging.StreamHandler()
    ]
)

class AutoUploader:
    def __init__(self):
        self.youtube = YouTubeAutomator()
        self._check_directories()
        
    def _check_directories(self):
        """폴더 구조 생성"""
        required = ['static/videos', 'static/audio', 'temp']
        for path in required:
            os.makedirs(path, exist_ok=True)
            os.chmod(path, 0o755)

    def full_process(self):
        """에러 없는 전체 파이프라인"""
        try:
            # 1. 콘텐츠 생성
            content = self._generate_content()
            
            # 2. 멀티미디어 제작
            video_path = self._create_video(content)
            
            # 3. 유튜브 업로드
            self.youtube.upload(
                file_path=video_path,
                title=f"{content[:95]}... #shorts",
                description="AI 자동 생성 콘텐츠 🤖"
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
        AutoUploader().full_process()

