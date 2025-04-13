# secure_main.py

import os
import time
from dotenv import load_dotenv
from openai_rotate import get_openai_api_key
from trending import get_trending_topic
from utils import text_to_speech, create_video as make_video, clean_folder
from youtube_upload import upload_video
from thumbnail import create_thumbnail

# .env 파일 로드
load_dotenv()

# OpenAI API 키 로테이션
OPENAI_API_KEY = get_openai_api_key()

# ElevenLabs API 키 로드
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def retry_text_to_speech(content, topic, retries=3):
    for _ in range(retries):
        try:
            return text_to_speech(content, topic)
        except Exception as e:
            print(f"음성 생성 오류 발생: {e}. 재시도 중...")
            time.sleep(5)  # 5초 후 재시도
    raise Exception("음성 생성에 실패했습니다.")

def main():
    # 폴더 정리
    clean_folder()

    # 트렌드 주제 가져오기
    topic = get_trending_topic()
    print(f"[1] 트렌드 주제 추출 완료: {topic}")

    # 콘텐츠 생성
    content = f"{topic}에 대해 오늘 알아보겠습니다. 많은 관심을 받고 있는 주제입니다."

    # 음성 생성 (재시도 함수 사용)
    audio_path = retry_text_to_speech(content, topic)
    print(f"[2] 오디오 저장 완료: {audio_path}")

    # 썸네일 생성
    thumbnail_path = create_thumbnail(content, topic)
    print(f"[3] 썸네일 생성 완료: {thumbnail_path}")

    # 영상 생성
    video_path = make_video(topic, audio_path, thumbnail_path)
    print(f"[4] 영상 생성 완료: {video_path}")

    # YouTube 업로드
    upload_video(video_path, title=topic, description=f"{topic}에 대한 자동 생성 콘텐츠입니다.", thumbnail_path=thumbnail_path)
    print("[5] YouTube 업로드 완료 🎉")

if __name__ == "__main__":
    main()

