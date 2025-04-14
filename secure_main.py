import os
import json
import logging
import time
import random
from datetime import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# 다른 모듈 임포트
from secure_generate_script import generate_script
# *** 함수명 변경 반영 ***
from secure_text_to_audio import text_to_speech
from secure_generate_video import generate_video
from trending import get_trending_topic
import openai # For specific exceptions like openai.RateLimitError
import requests # secure_text_to_audio에서 requests 사용하므로 여기서도 import 해두면 좋음

# --- 설정 (이전 답변과 동일) ---
load_dotenv()
LOG_FILE_PATH = ".secure_log.txt"
logging.basicConfig(...) # 이전 답변 내용 복사
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
VIDEO_CATEGORY_ID = "22"
DEFAULT_VIDEO_DESCRIPTION = "AI로 생성된 #Shorts 영상입니다. 흥미로운 정보를 빠르게 전달합니다. 구독과 좋아요는 큰 힘이 됩니다!"
MAX_VIDEOS_PER_RUN = 1
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 2

# --- 함수 (authenticate_youtube_api, log_upload, upload_video_to_youtube, cleanup_files는 이전 답변과 동일) ---
# 이전 답변의 함수들 복사하여 사용...
# authenticate_youtube_api() ...
# log_upload() ...
# upload_video_to_youtube() ...
# cleanup_files() ...

# --- 메인 실행 로직 (TTS 함수 호출 부분만 수정) ---
def main():
    """메인 자동화 프로세스 실행 (비용 최소화 버전)"""
    logging.info("="*30)
    logging.info("Starting YouTube Automation Process (Cost-Optimized Mode v2)")
    logging.info(f"Attempting to generate {MAX_VIDEOS_PER_RUN} video(s) per run.")
    logging.warning("This process uses APIs (OpenAI, ElevenLabs) that may incur costs beyond free tiers.")
    logging.warning("YouTube API usage also consumes daily quota.")
    logging.info("="*30)
    successful_uploads = 0
    youtube_service = None

    try:
        youtube_service = authenticate_youtube_api()
    except Exception as e:
        logging.critical(f"YouTube API authentication failed. Cannot proceed. Error: {e}")
        return

    for i in range(MAX_VIDEOS_PER_RUN):
        logging.info(f"\n--- Starting Video Generation Cycle {i + 1} / {MAX_VIDEOS_PER_RUN} ---")
        script = None
        audio_path = None
        video_path = None
        thumbnail_path = None
        topic = None
        duration = None

        try:
            # 1. 트렌드 토픽 가져오기
            topic = get_trending_topic()
            logging.info(f"Selected Topic: {topic}")

            logging.warning("Calling OpenAI API (gpt-3.5-turbo) to generate script...")
            # 2. 스크립트 생성 (이전 답변의 오류 처리 로직 포함)
            script_generated = False
            # ... (script 생성 로직 - 이전 답변 내용 복사) ...
            for attempt in range(MAX_RETRIES + 1):
                try:
                    script = generate_script(topic)
                    script_generated = True
                    break
                except openai.RateLimitError as e:
                    logging.error(f"OpenAI Rate Limit Error on attempt {attempt+1}: {e}. Retrying...") # ... (재시도 로직) ...
                    if attempt >= MAX_RETRIES: raise ConnectionAbortedError("OpenAI Rate Limit persist.") from e
                    time.sleep(RETRY_DELAY_SECONDS * (2**attempt))
                except (openai.APIError, openai.Timeout, openai.APIServerError) as e:
                    logging.error(f"OpenAI API Error on attempt {attempt+1}: {e}. Retrying...") # ... (재시도 로직) ...
                    if attempt >= MAX_RETRIES: raise ConnectionAbortedError("OpenAI API Error persist.") from e
                    time.sleep(RETRY_DELAY_SECONDS)
                except Exception as e:
                    logging.error(f"Unexpected error during script generation (attempt {attempt+1}): {e}")
                    raise

            if not script_generated: continue

            logging.warning("Calling ElevenLabs API to generate audio...")
            logging.warning("Ensure your ElevenLabs plan/free tier can handle the script length.")
            # 3. 텍스트를 오디오로 변환 (*** 함수 호출명 변경 ***)
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            if not voice_id:
                logging.error("ELEVENLABS_VOICE_ID not set.")
                raise ValueError("Missing ElevenLabs Voice ID")

            audio_generated = False
            # ... (audio 생성 로직 - 이전 답변 내용 복사, 함수명만 변경) ...
            for attempt in range(MAX_RETRIES + 1):
                 try:
                     # *** 함수 호출명 변경: text_to_speech ***
                     audio_path = text_to_speech(script, voice_id)
                     audio_generated = True
                     break
                 except ConnectionAbortedError as e: # 인증/쿼터 오류는 재시도 X
                      logging.error(f"Cannot generate audio: {e}")
                      raise
                 except (ConnectionError, requests.exceptions.RequestException) as e:
                      logging.error(f"Network Error during audio generation (attempt {attempt+1}): {e}. Retrying...")
                      if attempt >= MAX_RETRIES: raise ConnectionAbortedError("Network Error persist.") from e
                      time.sleep(RETRY_DELAY_SECONDS)
                 except Exception as e:
                      logging.error(f"Error during audio generation (attempt {attempt+1}): {e}")
                      if attempt >= MAX_RETRIES: raise ConnectionAbortedError("Audio generation failed.") from e
                      time.sleep(RETRY_DELAY_SECONDS)


            if not audio_generated: continue

            # 4. 비디오 생성
            video_title = f"{topic} #Shorts"
            video_path, thumbnail_path, duration = generate_video(video_title, audio_path)
            logging.info(f"Video generated: {video_path} (Duration: {duration:.2f}s)")
            logging.info(f"Thumbnail generated: {thumbnail_path}")

            logging.warning("Calling YouTube API for upload. This consumes daily quota.")
            # 5. YouTube 업로드
            video_description = f"'{topic}'에 대한 흥미로운 사실을 짧게 담았습니다.\n\n{script[:150]}...\n\n{DEFAULT_VIDEO_DESCRIPTION}"
            video_id = upload_video_to_youtube(youtube_service, video_path, video_title, video_description, thumbnail_path, duration)

            if video_id:
                successful_uploads += 1
            else:
                logging.warning(f"Upload failed for topic: {topic}")

        except ConnectionAbortedError as e:
             logging.error(f"Stopping cycle {i+1} due to persistent error: {e}")
             break
        except Exception as e:
            logging.error(f"Unhandled error in video cycle {i + 1} for topic '{topic}': {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

        finally:
            logging.info("Cleaning up generated files for this cycle...")
            cleanup_files(audio_path, video_path, thumbnail_path)

    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads in this run: {successful_uploads}")
    logging.info("Remember to monitor API usage and costs.")
    logging.info("="*30)

if __name__ == "__main__":
    # authenticate_youtube_api, log_upload, upload_video_to_youtube, cleanup_files 함수 정의 필요
    # 이전 답변에서 복사하여 이 아래 main() 함수 위에 배치하세요.
    # 예시:
    def authenticate_youtube_api(): pass # 실제 구현 필요
    def log_upload(vid, title, desc): pass # 실제 구현 필요
    def upload_video_to_youtube(yt, fp, t, d, tp=None, dur=None): pass # 실제 구현 필요
    def cleanup_files(*paths): pass # 실제 구현 필요

    main()
