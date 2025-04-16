import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# 모듈 임포트
from openai_rotate import OpenAIKeyManager
from secure_generate_script import ScriptGenerator
from secure_generate_audio import AudioEngine
from secure_generate_video import VideoProducer
from youtube_manager import YouTubeAutomator
from quota_control import QuotaManager

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/youtube_bot.log'),
        logging.StreamHandler()
    ]
)

class MasterBot:
    def __init__(self):
        self.quota = QuotaManager()
        self.openai = OpenAIKeyManager()
        self.audio = AudioEngine()
        self.video = VideoProducer()
        self.youtube = YouTubeAutomator()

    def initialize(self):
        """시스템 초기화"""
        try:
            if not os.path.exists('static'):
                os.makedirs('static', exist_ok=True)
                os.chmod('static', 0o755)
            
            self.youtube.authenticate()
            logging.info("�� 시스템 초기화 완료")
            
        except Exception as e:
            logging.critical(f"💥 초기화 실패: {str(e)}")
            sys.exit(1)

    def full_cycle(self):
        """전체 제작 프로세스"""
        try:
            # 1. 스크립트 생성
            script = ScriptGenerator(self.openai).create()
            if not script:
                raise ValueError("생성된 스크립트가 없습니다")
                
            # 2. 음성 변환
            audio_file = self.audio.generate(script)
            
            # 3. 영상 제작
            video_output, thumbnail = self.video.render(
                script, 
                audio_file,
                is_shorts=True
            )
            
            # 4. 유튜브 업로드
            video_id = self.youtube.upload(
                video_path=video_output,
                title=script[:100],
                description=script,
                thumbnail=thumbnail
            )
            
            # 5. 포스트 작업
            self.youtube.add_comment(video_id, "🤖 AI 자동 생성 콘텐츠")
            self.quota.update_usage('youtube')
            
            logging.info(f"✅ 성공: https://youtu.be/{video_id}")
            return True
            
        except Exception as e:
            logging.error(f"🔥 실패: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help='자동 모드 활성화')
    args = parser.parse_args()
    
    bot = MasterBot()
    bot.initialize()
    
    if args.auto:
        success = bot.full_cycle()
        sys.exit(0 if success else 1)

