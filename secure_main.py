# secure_main.py (수정됨 - SyntaxError 해결, 환경 변수 이름 추가 확인)

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

# 다른 모듈 임포트 (이전 답변과 동일)
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_speech
from secure_generate_video import generate_video
from trending import get_trending_topic
import openai
import requests

# --- 설정 ---
env_loaded = load_dotenv()
if env_loaded: logging.info(".env file loaded.")
else: logging.warning(".env file not found.")

LOG_FILE_PATH = ".secure_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
VIDEO_CATEGORY_ID = "22"
DEFAULT_VIDEO_DESCRIPTION = "AI로 생성된 #Shorts 영상입니다. 흥미로운 정보를 빠르게 전달합니다. 구독과 좋아요는 큰 힘이 됩니다!"
MAX_VIDEOS_PER_RUN = 1
RETRY_DELAY_SECONDS = 60
MAX_RETRIES = 2

# --- 함수 정의 ---

def authenticate_youtube_api():
    """YouTube API 인증 및 서비스 객체 반환 (OAuth 2.0 사용)"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info(f"Loaded credentials from {TOKEN_FILE}.")
        except Exception as e:
            logging.warning(f"Failed to load credentials from {TOKEN_FILE}: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully.")
            except Exception as e:
                logging.error(f"Failed to refresh credentials: {e}. Need to re-authenticate.")
                creds = None
        else:
            logging.info("No valid credentials found or refresh failed, starting authentication flow.")

            # *** 환경 변수 로드 시도 (두 가지 이름 모두 확인) ***
            client_secret_json_str = os.getenv("GOOGLE_CLIENT_SECRET_JSON") # for .env
            if not client_secret_json_str:
                logging.info("GOOGLE_CLIENT_SECRET_JSON not found, checking YOUTUBE_CLIENT_SECRETS_JSON (for GitHub Actions)...")
                client_secret_json_str = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON") # for GitHub Secret

            flow = None

            if not client_secret_json_str:
                # 환경 변수 값이 없는 경우 (두 이름 모두)
                logging.error("Neither GOOGLE_CLIENT_SECRET_JSON nor YOUTUBE_CLIENT_SECRETS_JSON environment variable found!")
                logging.warning("Attempting to use local client_secret.json file as fallback.")
                if os.path.exists(CLIENT_SECRET_FILE):
                     logging.info(f"Found local {CLIENT_SECRET_FILE}.")
                     try:
                         flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                     except Exception as e:
                         logging.error(f"Error loading {CLIENT_SECRET_FILE}: {e}")
                         raise ValueError(f"Cannot authenticate: Error loading {CLIENT_SECRET_FILE}.")
                else:
                    logging.error(f"{CLIENT_SECRET_FILE} not found either.")
                    raise ValueError(f"Cannot authenticate: No client secret JSON found in env vars or local file.")
            else:
                # 환경 변수 값이 있는 경우
                logging.info(f"Found client secret JSON in environment variable.")
                # (진단 로그는 이전 답변과 동일)
                logging.info(f"Type: {type(client_secret_json_str)}, Length: {len(client_secret_json_str)}")
                if not isinstance(client_secret_json_str, str) or len(client_secret_json_str) < 10:
                    logging.error("Client secret JSON from env var is not a valid non-empty string.")
                    raise ValueError("Invalid client secret JSON content detected.")
                # Base64 인코딩 확인 (단순 휴리스틱) - 에러 방지 위해 추가
                if client_secret_json_str.startswith('ey') and not client_secret_json_str.strip().startswith('{'):
                     logging.error("Detected likely Base64 encoded value in client secret JSON environment variable!")
                     logging.error("Please provide the RAW JSON content, not Base64 encoded.")
                     raise ValueError("Client secret JSON appears to be Base64 encoded. Provide raw JSON.")
                logging.info(f"First 10 chars: {client_secret_json_str[:10]}")

                try:
                    # JSON 파싱
                    client_config = json.loads(client_secret_json_str)
                    logging.info("Successfully parsed client secret JSON from environment variable.")

                    # flow 생성
                    if 'installed' in client_config:
                        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    elif 'web' in client_config:
                         raise NotImplementedError("Web client type requires pre-authorization or service account.")
                    else:
                        raise ValueError("Invalid client secret JSON format: 'installed' or 'web' key missing.")

                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: Failed to parse client secret JSON from env var. Error: {e}")
                    logging.error("Ensure the env var contains the EXACT, COMPLETE, VALID JSON content, properly quoted, and NOT Base64 encoded.")
                    raise ValueError("Failed to parse client secret JSON from env var.") from e
                except Exception as e:
                     logging.error(f"Error processing client secret JSON from env var: {e}")
                     raise ValueError(f"Error initializing authentication flow from env var: {e}")

            # 인증 진행 (flow 객체가 생성된 경우)
            if flow:
                try:
                    if os.getenv("CI"): # GitHub Actions 등 CI 환경
                        # ... (CI 환경 token.json 로드 로직 - 이전 답변과 동일) ...
                        logging.warning("Running in CI environment. Attempting to use stored token (GOOGLE_TOKEN_JSON).")
                        if not os.path.exists(TOKEN_FILE):
                            token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
                            if token_json_str:
                                logging.info("Found GOOGLE_TOKEN_JSON. Writing to token.json")
                                try:
                                    token_data = json.loads(token_json_str) # Validate JSON
                                    with open(TOKEN_FILE, "w") as t_file: json.dump(token_data, t_file)
                                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                                    if creds and creds.refresh_token: creds.refresh(Request()); logging.info("Token refreshed.")
                                    elif creds and creds.valid: logging.info("Token loaded is valid.")
                                    else: raise ValueError("Token lacks refresh token or is invalid.")
                                except json.JSONDecodeError: raise ValueError("Invalid GOOGLE_TOKEN_JSON content.")
                                except Exception as e: logging.error(f"Error processing GOOGLE_TOKEN_JSON: {e}"); raise
                            else: raise ValueError("Cannot authenticate in CI: GOOGLE_TOKEN_JSON secret required.")
                    else: # 로컬 환경
                        logging.info("Please follow the authentication steps in your browser.")
                        creds = flow.run_local_server(port=0)
                        logging.info("Authentication successful.")
                except Exception as e:
                    logging.error(f"Authentication process failed: {e}")
                    # *** SyntaxError 수정: try...except 블록을 올바르게 분리 ***
                    if os.path.exists(TOKEN_FILE):
                        try:
                            os.remove(TOKEN_FILE)
                            logging.info(f"Removed potentially invalid {TOKEN_FILE}")
                        except OSError as rm_e:
                            logging.warning(f"Could not remove {TOKEN_FILE}: {rm_e}")
                    raise # 원래 에러를 다시 발생시켜 호출자에게 알림

            # 인증 정보 저장
            if creds and creds.valid:
                try:
                    with open(TOKEN_FILE, "w") as token: token.write(creds.to_json())
                    logging.info(f"Credentials saved/updated in {TOKEN_FILE}")
                except Exception as e:
                    logging.error(f"Failed to save credentials to {TOKEN_FILE}: {e}")
            elif not creds:
                 raise ConnectionRefusedError("Failed to obtain valid credentials.")

    # YouTube API 서비스 빌드
    try:
        youtube = build("youtube", "v3", credentials=creds)
        logging.info("YouTube API service built successfully.")
        return youtube
    except Exception as e:
        logging.error(f"Failed to build YouTube API service: {str(e)}")
        raise ConnectionRefusedError("Failed to build YouTube service.")


# --- 나머지 함수 및 main 함수 ---
# log_upload, upload_video_to_youtube, cleanup_files, main 함수는
# 이전 답변과 동일하게 유지됩니다. (SyntaxError가 발생한 부분은 위에서 수정되었습니다.)
# 아래는 각 함수의 시작 부분만 표시합니다.

def log_upload(video_id, title, description): # 이전 답변 내용과 동일
    # ...
    pass
def upload_video_to_youtube(youtube, file_path, title, description, thumbnail_path=None, duration_seconds=None): # 이전 답변 내용과 동일
    # ...
    pass
def cleanup_files(*file_paths): # 이전 답변 내용과 동일
    # ...
    pass

def main():
    """메인 자동화 프로세스 실행 (비용 최소화 버전)"""
    logging.info("="*30)
    logging.info(f"Starting YouTube Automation Process (Cost-Optimized Mode v6) - Attempting {MAX_VIDEOS_PER_RUN} video(s)")
    logging.warning("Ensure API keys and quotas are sufficient. Ensure client secret JSON is RAW, not Base64.")
    logging.info("="*30)
    successful_uploads = 0
    youtube_service = None

    try:
        youtube_service = authenticate_youtube_api()
    except (ValueError, NotImplementedError, ConnectionRefusedError, Exception) as e:
        logging.critical(f"YouTube API authentication failed. Cannot proceed. Error: {e}")
        import traceback; logging.critical(traceback.format_exc())
        return

    # ... (for 루프 및 나머지 main 함수 내용은 이전 답변과 동일) ...
    for i in range(MAX_VIDEOS_PER_RUN):
        logging.info(f"\n--- Starting Video Generation Cycle {i + 1} / {MAX_VIDEOS_PER_RUN} ---")
        # ... (try...except...finally 블록 - 이전 답변 내용 복사) ...
        pass # 이전 답변 내용 복사

    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads in this run: {successful_uploads}")
    logging.info("Please check logs for any warnings or errors.")
    logging.info("="*30)


if __name__ == "__main__":
    main()
