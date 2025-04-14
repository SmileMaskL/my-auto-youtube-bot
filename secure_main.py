# secure_main.py (수정됨 - 환경 변수 로드 확인 로그 추가)

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
# .env 파일 로드 시도
env_loaded = load_dotenv()
# *** .env 로드 결과 로깅 추가 ***
if env_loaded:
    logging.info(".env file loaded successfully.")
else:
    logging.warning(".env file not found or failed to load. Relying on system environment variables.")

LOG_FILE_PATH = ".secure_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 나머지 설정 (이전 답변과 동일)
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
    # ... (token.json 로드 및 갱신 로직) ...
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info(f"Loaded credentials from {TOKEN_FILE}.")
        except Exception as e:
            logging.warning(f"Failed to load credentials from {TOKEN_FILE}: {e}")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # ... (토큰 갱신 로직) ...
            logging.info("Credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully.")
            except Exception as e:
                logging.error(f"Failed to refresh credentials: {e}. Need to re-authenticate.")
                creds = None
        else:
            # --- 새 인증 흐름 ---
            logging.info("No valid credentials found or refresh failed, starting authentication flow.")

            # *** 환경 변수 로드 확인 로그 강화 ***
            client_secret_json_str = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
            if client_secret_json_str:
                logging.info("GOOGLE_CLIENT_SECRET_JSON environment variable FOUND.")
            else:
                # *** 이 로그가 출력된다면 .env 파일 문제 또는 환경 변수 설정 문제입니다! ***
                logging.error("GOOGLE_CLIENT_SECRET_JSON environment variable NOT FOUND or EMPTY!")

            flow = None # flow 변수 초기화

            # 환경 변수가 없는 경우 로컬 파일 시도
            if not client_secret_json_str:
                logging.warning("Attempting to use local client_secret.json file as fallback.")
                if os.path.exists(CLIENT_SECRET_FILE):
                     logging.info(f"Found local {CLIENT_SECRET_FILE}.")
                     try:
                         flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                     except Exception as e:
                         logging.error(f"Error loading {CLIENT_SECRET_FILE}: {e}")
                         raise ValueError(f"Cannot authenticate: Error loading {CLIENT_SECRET_FILE}.")
                else:
                    # 환경 변수도 없고, 로컬 파일도 없는 최종 실패
                    logging.error(f"{CLIENT_SECRET_FILE} not found either.")
                    raise ValueError(f"Cannot authenticate: GOOGLE_CLIENT_SECRET_JSON not set and {CLIENT_SECRET_FILE} not found.")
            else:
                # 환경 변수가 있는 경우 (이전 진단 로그 포함)
                logging.info(f"Processing GOOGLE_CLIENT_SECRET_JSON. Type: {type(client_secret_json_str)}, Length: {len(client_secret_json_str)}")
                if not isinstance(client_secret_json_str, str) or len(client_secret_json_str) < 10:
                    logging.error("GOOGLE_CLIENT_SECRET_JSON is not a valid non-empty string.")
                    raise ValueError("Invalid GOOGLE_CLIENT_SECRET_JSON content (not string or too short).")
                logging.info(f"First 10 chars of GOOGLE_CLIENT_SECRET_JSON: {client_secret_json_str[:10]}")

                try:
                    # JSON 파싱 시도
                    client_config = json.loads(client_secret_json_str)
                    logging.info("Successfully parsed GOOGLE_CLIENT_SECRET_JSON.")

                    # flow 생성 (이전과 동일)
                    if 'installed' in client_config:
                        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    # ... (elif 'web', else - 이전과 동일) ...
                    elif 'web' in client_config:
                         logging.error("Authentication Error: 'web' client type JSON provided.")
                         raise NotImplementedError("Web client type requires pre-authorization or service account.")
                    else:
                        raise ValueError("Invalid client secret JSON format in environment variable: 'installed' or 'web' key missing.")

                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: Failed to parse GOOGLE_CLIENT_SECRET_JSON environment variable. Error: {e}")
                    logging.error("Ensure the variable contains the exact, complete, and valid JSON content, properly quoted.")
                    raise ValueError("Failed to parse GOOGLE_CLIENT_SECRET_JSON. Ensure it's a valid JSON string.") from e
                except Exception as e:
                     logging.error(f"Error processing GOOGLE_CLIENT_SECRET_JSON: {e}")
                     raise ValueError(f"Error initializing authentication flow from environment variable: {e}")

            # 인증 진행 (flow 객체가 생성된 경우)
            if flow:
                try:
                     # ... (CI / 로컬 인증 로직 - 이전 답변과 동일) ...
                     # ... (token.json 저장 로직 - 이전 답변과 동일) ...
                    if os.getenv("CI"): # GitHub Actions 등 CI 환경
                        logging.warning("Running in CI environment. Attempting to use stored token.")
                        if not os.path.exists(TOKEN_FILE):
                            token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
                            if token_json_str:
                                logging.info("Found GOOGLE_TOKEN_JSON. Writing to token.json")
                                try:
                                    token_data = json.loads(token_json_str) # Validate JSON first
                                    with open(TOKEN_FILE, "w") as t_file: json.dump(token_data, t_file)
                                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                                    if creds and creds.refresh_token: creds.refresh(Request()); logging.info("Token refreshed successfully.")
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
                    if os.path.exists(TOKEN_FILE): try: os.remove(TOKEN_FILE)
                    except OSError: pass
                    raise
            elif not creds: # flow 객체 생성 실패 시 (예: 파일 없음)
                 # 이 경우는 이미 위에서 raise ValueError 했어야 함
                 logging.error("Internal error: Flow object not created but reached credential saving step.")
                 raise ConnectionRefusedError("Failed to initialize authentication flow.")


        # 인증 정보 저장
        if creds and creds.valid:
            try:
                with open(TOKEN_FILE, "w") as token: token.write(creds.to_json())
                logging.info(f"Credentials saved/updated in {TOKEN_FILE}")
            except Exception as e:
                logging.error(f"Failed to save credentials to {TOKEN_FILE}: {e}")
        elif not creds:
             # 최종적으로 유효한 creds가 없는 경우
             raise ConnectionRefusedError("Failed to obtain valid credentials after authentication attempt.")

    # YouTube API 서비스 빌드
    try:
        youtube = build("youtube", "v3", credentials=creds)
        logging.info("YouTube API service built successfully.")
        return youtube
    except Exception as e:
        logging.error(f"Failed to build YouTube API service: {str(e)}")
        raise ConnectionRefusedError("Failed to build YouTube service.")


# --- 나머지 함수 및 main 함수 (log_upload, upload_video_to_youtube, cleanup_files, main) ---
# 이전 답변과 동일하게 유지됩니다. 아래는 main 함수의 시작 부분만 다시 표시합니다.

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
    # main 함수 시작 시 로그 레벨 변경 (옵션 - 더 상세한 로그 원할 시 DEBUG)
    # logging.getLogger().setLevel(logging.DEBUG)
    logging.info(f"Starting YouTube Automation Process (Cost-Optimized Mode v5) - Attempting {MAX_VIDEOS_PER_RUN} video(s)")
    logging.warning("Ensure API keys and quotas (OpenAI, ElevenLabs, YouTube) are sufficient.")
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
        # ... (try...except...finally 블록) ...
        pass # 이전 답변 내용 복사

    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads in this run: {successful_uploads}")
    logging.info("Please check logs for any warnings or errors.")
    logging.info("="*30)

if __name__ == "__main__":
    main()
