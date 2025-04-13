import os
import json
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_audio
from secure_generate_video import generate_video
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로그 설정
log_file_path = ".secure_log.txt"
logging.basicConfig(filename=log_file_path, level=logging.INFO)

# YouTube API 인증
def authenticate_youtube_api():
    credentials = Credentials.from_authorized_user_info(json.loads(os.getenv("GOOGLE_CLIENT_SECRET_JSON")))
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube

# 업로드 로그 기록
def log_upload(title, video_id):
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.now()} | {title} | https://www.youtube.com/watch?v={video_id}\n")

# 비디오 업로드
def upload_video(youtube, title, description, file_path, category="22"):
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=file_path
    )
    response = request.execute()
    return response["id"]

# 메인 함수
def main():
    # 트렌드 데이터 예시
    trend_data = "Sample Trend"

    # 스크립트 생성
    script = generate_script(trend_data)
    
    # 텍스트 오디오 변환
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    text_to_audio(script, voice_id)
    
    # 비디오 생성
    video_path = "generated_video.mp4"
    generate_video(trend_data, voice_id)

    # YouTube API 인증
    youtube = authenticate_youtube_api()

    # 비디오 업로드
    title = f"Trending Topic: {trend_data}"
    video_id = upload_video(youtube, title, script, video_path)
    
    # 업로드 후 로그 기록
    log_upload(title, video_id)

if __name__ == "__main__":
    main()

