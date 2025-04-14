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
from secure_text_to_audio import text_to_audio
from secure_generate_video import generate_video
from trending import get_trending_topic
import openai # For specific exceptions like openai.RateLimitError

# --- 설정 ---
load_dotenv()

LOG_FILE_PATH = ".secure_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Google API 관련 설정
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"

# 비디오 생성/업로드 관련 설정 (비용 최소화)
VIDEO_CATEGORY_ID = "22"
DEFAULT_VIDEO_DESCRIPTION = "AI로 생성된 #Shorts 영상입니다. 흥미로운 정보를 빠르게 전달합니다. 구독과 좋아요는 큰 힘이 됩니다!"
MAX_VIDEOS_PER_RUN = 1 # *** 비용 최소화를 위해 하루 1개 영상 생성으로 제한 ***
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 2 # 재시도 횟수 줄임

# --- 함수 (authenticate_youtube_api, log_upload, upload_video_to_youtube, cleanup_files는 이전 답변과 동일) ---
# 이전 답변의 함수들 복사하여 사용...
# authenticate_youtube_api() ...
# log_upload() ...
# upload_video_to_youtube() ...
# cleanup_files() ...
# 아래는 위 함수들이 정의되었다고 가정하고 main 함수 수정

# --- 메인 실행 로직 (수정됨) ---
def main():
    """메인 자동화 프로세스 실행 (비용 최소화 버전)"""
    logging.info("="*30)
    logging.info("Starting YouTube Automation Process (Cost-Optimized Mode)")
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
        return # 인증 실패 시 완전 종료

    # 비디오 생성 루프 (MAX_VIDEOS_PER_RUN 만큼 실행)
    for i in range(MAX_VIDEOS_PER_RUN):
        logging.info(f"\n--- Starting Video Generation Cycle {i + 1} / {MAX_VIDEOS_PER_RUN} ---")
        script = None
        audio_path = None
        video_path = None
        thumbnail_path = None
        topic = None
        duration = None # duration 변수 초기화

        try:
            # 1. 트렌드 토픽 가져오기
            topic = get_trending_topic()
            logging.info(f"Selected Topic: {topic}")

            # --- OpenAI API 호출 전 비용 경고 ---
            logging.warning("Calling OpenAI API (gpt-3.5-turbo) to generate script...")

            # 2. 스크립트 생성 (오류 처리 강화)
            script_generated = False
            for attempt in range(MAX_RETRIES + 1):
                try:
                    script = generate_script(topic) # target_duration 기본값(60초) 사용
                    script_generated = True
                    break # 성공
                except openai.RateLimitError as e:
                    logging.error(f"OpenAI Rate Limit Error on attempt {attempt+1}: {e}. Retrying after delay...")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS * (2**attempt))
                    else:
                        logging.error("Max retries reached for OpenAI Rate Limit. Skipping this video cycle.")
                        # 다음 비디오 사이클로 넘어가지 않고 종료하거나, 다음 사이클 시도 결정 필요
                        # 여기서는 현재 비디오 사이클 중단
                        raise ConnectionAbortedError("OpenAI Rate Limit persist after retries.") from e
                except (openai.APIError, openai.Timeout, openai.APIServerError) as e:
                     logging.error(f"OpenAI API Error on attempt {attempt+1}: {e}. Retrying after delay...")
                     if attempt < MAX_RETRIES:
                         time.sleep(RETRY_DELAY_SECONDS)
                     else:
                         logging.error("Max retries reached for OpenAI API Error. Skipping this video cycle.")
                         raise ConnectionAbortedError("OpenAI API Error persist after retries.") from e
                except Exception as e: # 다른 예상치 못한 오류
                    logging.error(f"Unexpected error during script generation (attempt {attempt+1}): {e}")
                    # 예상치 못한 오류는 재시도하지 않고 바로 중단하는 것이 안전할 수 있음
                    raise # 오류를 상위로 보내 처리 중단

            if not script_generated: continue # 스크립트 생성 최종 실패 시 다음 사이클 (현재는 MAX_VIDEOS_PER_RUN=1이라 사실상 종료)

            # --- ElevenLabs API 호출 전 비용/쿼터 경고 ---
            logging.warning("Calling ElevenLabs API to generate audio...")
            logging.warning("Ensure your ElevenLabs plan/free tier can handle the script length.")

            # 3. 텍스트를 오디오로 변환
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            if not voice_id:
                logging.error("ELEVENLABS_VOICE_ID not set.")
                raise ValueError("Missing ElevenLabs Voice ID")

            audio_generated = False
            for attempt in range(MAX_RETRIES + 1):
                try:
                    audio_path = text_to_audio(script, voice_id)
                    audio_generated = True
                    break # 성공
                except (ConnectionError, requests.exceptions.RequestException) as e:
                    logging.error(f"Network Error during audio generation (attempt {attempt+1}): {e}. Retrying...")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY_SECONDS)
                    else:
                        logging.error("Max retries reached for Network Error. Skipping audio generation.")
                        raise ConnectionAbortedError("Network Error persist after retries.") from e
                except Exception as e: # ElevenLabs API 오류 등
                    logging.error(f"Error during audio generation (attempt {attempt+1}): {e}")
                    # 특정 API 오류(예: 할당량 초과)는 재시도 의미 없을 수 있음
                    if "quota" in str(e).lower() or "limit" in str(e).lower():
                         logging.error("Quota likely exceeded for ElevenLabs. Stopping this cycle.")
                         raise ConnectionAbortedError("ElevenLabs Quota Exceeded.") from e
                    # 다른 오류 시 재시도
                    if attempt < MAX_RETRIES:
                         time.sleep(RETRY_DELAY_SECONDS)
                    else:
                         logging.error("Max retries reached for audio generation. Skipping this cycle.")
                         raise ConnectionAbortedError("Audio generation failed after retries.") from e

            if not audio_generated: continue # 오디오 생성 실패 시

            # 4. 비디오 생성
            video_title = f"{topic} #Shorts" # 제목에 #Shorts 포함
            video_path, thumbnail_path, duration = generate_video(video_title, audio_path)
            logging.info(f"Video generated: {video_path} (Duration: {duration:.2f}s)")
            logging.info(f"Thumbnail generated: {thumbnail_path}")

            # --- YouTube API 호출 전 쿼터 경고 ---
            logging.warning("Calling YouTube API for upload. This consumes daily quota.")

            # 5. YouTube 업로드
            # 설명에 스크립트 일부 포함 및 기본 설명 추가
            video_description = f"'{topic}'에 대한 흥미로운 사실을 짧게 담았습니다.\n\n{script[:150]}...\n\n{DEFAULT_VIDEO_DESCRIPTION}"
            video_id = upload_video_to_youtube(youtube_service, video_path, video_title, video_description, thumbnail_path, duration)

            if video_id:
                successful_uploads += 1
            else:
                logging.warning(f"Upload failed for topic: {topic}")

        except ConnectionAbortedError as e:
             # 재시도 후에도 실패한 특정 오류들 처리
             logging.error(f"Stopping cycle {i+1} due to persistent error: {e}")
             # 여기서 프로세스를 완전히 종료할지, 다음 스케줄을 기다릴지 결정
             # 여기서는 현재 실행 중단
             break # for 루프 탈출
        except Exception as e:
            # 예상치 못한 다른 오류 처리
            logging.error(f"Unhandled error in video cycle {i + 1} for topic '{topic}': {str(e)}")
            # 필요시 traceback 로깅 추가
            import traceback
            logging.error(traceback.format_exc())

        finally:
            # 6. 생성된 로컬 파일 정리
            logging.info("Cleaning up generated files for this cycle...")
            cleanup_files(audio_path, video_path, thumbnail_path)

        # API 제한 및 비용 최소화를 위해 사이클 간 대기 불필요 (MAX_VIDEOS_PER_RUN = 1 이므로)
        # if i < MAX_VIDEOS_PER_RUN - 1: time.sleep(...) # 여러 개 생성 시 주석 해제


    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads in this run: {successful_uploads}")
    logging.info("Remember to monitor API usage and costs.")
    logging.info("="*30)

if __name__ == "__main__":
    main()
