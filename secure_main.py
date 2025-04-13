import os
import json
import logging
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_audio
from secure_generate_video import generate_video
from dotenv import load_dotenv
import time
import random

# 환경 변수 로드
load_dotenv()

# 로그 설정
log_file_path = ".secure_log.txt"
logging.basicConfig(filename=log_file_path, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# YouTube API 인증
def authenticate_youtube_api():
    try:
        creds_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
        if not creds_json:
            raise ValueError("Google credentials not found in environment variables")
            
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_authorized_user_info(creds_dict)
        youtube = build("youtube", "v3", credentials=creds)
        return youtube
    except Exception as e:
        logging.error(f"YouTube API authentication failed: {str(e)}")
        raise

# 업로드 로그 기록
def log_upload(title, video_id, description=""):
    try:
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().isoformat()} | {title} | {description[:50]}... | https://www.youtube.com/watch?v={video_id}\n")
    except Exception as e:
        logging.error(f"Failed to log upload: {str(e)}")

# 비디오 업로드
def upload_video(youtube, title, description, file_path, thumbnail_path=None, category="22"):
    try:
        # 비디오 업로드
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": category,
                    "tags": title.split()[:5]
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logging.info(f"Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response["id"]
        logging.info(f"Video uploaded successfully: {video_id}")
        
        # 썸네일 업로드
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logging.info(f"Thumbnail uploaded for video {video_id}")
            except Exception as e:
                logging.error(f"Failed to upload thumbnail: {str(e)}")
        
        # 댓글 추가
        try:
            comment_body = {
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": f"{title}에 대한 자동 생성 콘텐츠입니다. 구독과 좋아요 부탁드립니다!"
                        }
                    }
                }
            }
            youtube.commentThreads().insert(
                part="snippet",
                body=comment_body
            ).execute()
            logging.info(f"Comment added to video {video_id}")
        except Exception as e:
            logging.error(f"Failed to add comment: {str(e)}")
        
        return video_id
        
    except Exception as e:
        logging.error(f"Video upload failed: {str(e)}")
        raise

# API 키 로테이션 관리
def manage_api_quotas():
    # 여기에 API 사용량 모니터링 및 키 로테이션 로직 추가
    pass

# 메인 함수
def main():
    try:
        logging.info("Starting YouTube automation process")
        
        # 1. 트렌드 데이터 가져오기
        trend_data = "Sample Trend"  # 실제로는 트렌드 API에서 가져옴
        logging.info(f"Trend data: {trend_data}")
        
        # 2. 스크립트 생성
        script = generate_script(trend_data)
        logging.info("Script generated successfully")
        
        # 3. 텍스트를 오디오로 변환
        voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        audio_path = text_to_audio(script, voice_id)
        logging.info(f"Audio generated and saved to: {audio_path}")
        
        # 4. 비디오 생성
        video_path, thumbnail_path = generate_video(trend_data, audio_path)
        logging.info(f"Video generated and saved to: {video_path}")
        logging.info(f"Thumbnail generated and saved to: {thumbnail_path}")
        
        # 5. YouTube API 인증
        youtube = authenticate_youtube_api()
        logging.info("YouTube API authenticated successfully")
        
        # 6. 비디오 업로드
        title = f"Trending Topic: {trend_data}"
        video_id = upload_video(youtube, title, script, video_path, thumbnail_path)
        logging.info(f"Video uploaded successfully with ID: {video_id}")
        
        # 7. 업로드 후 로그 기록
        log_upload(title, video_id, script)
        logging.info("Process completed successfully")
        
    except Exception as e:
        logging.error(f"An error occurred in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main()
