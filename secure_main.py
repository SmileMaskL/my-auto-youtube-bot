import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from secure_generate_script import generate_script
from secure_generate_audio import text_to_speech
from secure_generate_video import generate_video
from youtube_uploader import YouTubeUploader
from google_auth import get_authenticated_service
from quota_manager import quota_manager
from openai_rotate import openai_manager

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('secure_log.txt'),
        logging.StreamHandler()
    ]
)

def main(auto_mode=False):
    try:
        # 1. 스크립트 생성
        logging.info("Generating script...")
        script = generate_script()
        
        # 2. 음성 생성
        logging.info("Generating audio...")
        audio_path = text_to_speech(script)
        
        # 3. 영상 생성
        logging.info("Generating video...")
        video_path, thumbnail_path, duration = generate_video(script[:100], audio_path)
        
        # 4. 유튜브 업로드
        logging.info("Authenticating YouTube...")
        youtube = get_authenticated_service()
        uploader = YouTubeUploader(youtube)
        
        # 5. 자동 업로드
        if auto_mode or input("Upload to YouTube? (y/n): ").lower() == 'y':
            video_id = uploader.upload_video(
                video_path,
                script[:100],
                script,
                thumbnail_path
            )
            if video_id:
                # 댓글 자동 작성
                uploader.post_comment(video_id, "이 영상은 AI로 자동 생성되었습니다.")
                logging.info(f"Successfully uploaded: https://youtu.be/{video_id}")
        
        # 6. 쿼터 상태 업데이트
        logging.info("Current quota status:")
        logging.info(quota_manager.get_status())
        
    except Exception as e:
        logging.error(f"Critical error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help='Enable full automation mode')
    args = parser.parse_args()
    
    main(auto_mode=args.auto)

