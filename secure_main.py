import os
from dotenv import load_dotenv
from openai_manager import get_available_api_key
from video_generator import generate_video
from text_to_speech import generate_speech
from youtube_uploader import upload_video

def main():
    load_dotenv()
    api_key = get_available_api_key()
    if not api_key:
        print("사용 가능한 API 키가 없습니다.")
        return

    # 텍스트 생성
    script_text = "오늘의 뉴스 헤드라인입니다."

    # 음성 생성
    audio_file = generate_speech(script_text, api_key)

    # 영상 생성
    video_file, thumbnail_file = generate_video(script_text, audio_file)

    # 유튜브 업로드
    upload_video(video_file, thumbnail_file, script_text)

if __name__ == "__main__":
    main()

