# secure_main.py (수정됨)

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
from secure_text_to_audio import text_to_speech # 함수명 변경됨
from secure_generate_video import generate_video
from trending import get_trending_topic
import openai # For specific exceptions like openai.RateLimitError
import requests # secure_text_to_audio에서 requests 사용

# --- 설정 ---
load_dotenv()

LOG_FILE_PATH = ".secure_log.txt"
# *** logging.basicConfig 수정 ***
logging.basicConfig(
    level=logging.INFO, # 로그 레벨 설정
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', # 로그 형식 지정
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'), # 파일 핸들러
        logging.StreamHandler() # 콘솔 핸들러 (터미널 출력)
    ]
)

# Google API 관련 설정
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json" # 로컬 테스트용 파일 이름
TOKEN_FILE = "token.json" # 생성/저장될 토큰 파일 이름

# 비디오 생성/업로드 관련 설정 (비용 최소화)
VIDEO_CATEGORY_ID = "22" # People & Blogs
DEFAULT_VIDEO_DESCRIPTION = "AI로 생성된 #Shorts 영상입니다. 흥미로운 정보를 빠르게 전달합니다. 구독과 좋아요는 큰 힘이 됩니다!"
MAX_VIDEOS_PER_RUN = 1 # 하루 1개 영상 생성으로 제한
RETRY_DELAY_SECONDS = 60 # 재시도 대기 시간 (초)
MAX_RETRIES = 2 # 최대 재시도 횟수

# --- 함수 정의 (이전 답변 내용과 동일) ---

def authenticate_youtube_api():
    """YouTube API 인증 및 서비스 객체 반환 (OAuth 2.0 사용)"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info("Loaded credentials from token file.")
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
            logging.info("No valid credentials found, starting authentication flow.")
            client_secret_json_str = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
            flow = None # flow 변수 초기화
            if not client_secret_json_str:
                logging.warning("GOOGLE_CLIENT_SECRET_JSON environment variable not set.")
                if os.path.exists(CLIENT_SECRET_FILE):
                     logging.info(f"Trying to use local {CLIENT_SECRET_FILE}")
                     try:
                         flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                     except Exception as e:
                         logging.error(f"Error loading {CLIENT_SECRET_FILE}: {e}")
                         raise ValueError(f"Cannot authenticate: Error loading {CLIENT_SECRET_FILE}.")
                else:
                    raise ValueError(f"Cannot authenticate: GOOGLE_CLIENT_SECRET_JSON not set and {CLIENT_SECRET_FILE} not found.")
            else:
                try:
                    client_config = json.loads(client_secret_json_str)
                    if 'installed' in client_config:
                        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    elif 'web' in client_config:
                         logging.error("Authentication Error: 'web' client type JSON is not suitable for this script flow without a pre-existing refresh token.")
                         logging.error("Use 'installed app' or 'desktop app' type credentials, or ensure the JSON contains a 'refresh_token'.")
                         # 혹은 token.json을 직접 로드하는 로직 추가 필요
                         raise NotImplementedError("Web client type requires pre-authorization or service account.")
                    else:
                        raise ValueError("Invalid client secret JSON format: 'installed' or 'web' key missing.")
                except json.JSONDecodeError:
                    raise ValueError("Failed to parse GOOGLE_CLIENT_SECRET_JSON. Ensure it's a valid JSON string.")
                except Exception as e:
                    raise ValueError(f"Error initializing authentication flow: {e}")

            # 인증 진행 (로컬/CI 환경 구분)
            if flow: # flow 객체가 성공적으로 생성된 경우에만 진행
                try:
                    if os.getenv("CI"): # GitHub Actions 등 CI 환경
                        logging.warning("Running in CI environment. Attempting to use stored token.")
                        if not os.path.exists(TOKEN_FILE):
                            token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
                            if token_json_str:
                                logging.info("Found GOOGLE_TOKEN_JSON. Writing to token.json")
                                try:
                                    # JSON 유효성 검사 추가
                                    json.loads(token_json_str)
                                    with open(TOKEN_FILE, "w") as t_file:
                                        t_file.write(token_json_str)
                                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                                    if creds and creds.refresh_token:
                                        logging.info("Attempting to refresh token from GOOGLE_TOKEN_JSON...")
                                        creds.refresh(Request()) # 즉시 리프레시 시도
                                        logging.info("Token refreshed successfully from GOOGLE_TOKEN_JSON.")
                                    elif creds and creds.valid:
                                         logging.info("Token loaded from GOOGLE_TOKEN_JSON is valid.")
                                    else:
                                        # 리프레시 토큰 없으면 재인증 불가
                                        raise ValueError("Token loaded from GOOGLE_TOKEN_JSON lacks refresh token or is invalid.")
                                except json.JSONDecodeError:
                                    logging.error("GOOGLE_TOKEN_JSON is not valid JSON.")
                                    raise ValueError("Invalid GOOGLE_TOKEN_JSON content.")
                                except Exception as e:
                                     logging.error(f"Error processing GOOGLE_TOKEN_JSON: {e}")
                                     raise
                            else:
                                raise ValueError("Cannot authenticate in CI: Pre-existing token.json or GOOGLE_TOKEN_JSON secret required.")
                        # else: token.json 파일이 이미 존재하면 위에서 로드 시도됨
                    else: # 로컬 환경
                        logging.info("Please follow the authentication steps in your browser.")
                        creds = flow.run_local_server(port=0)
                        logging.info("Authentication successful.")
                except Exception as e:
                    logging.error(f"Authentication process failed: {e}")
                    # 실패 시 생성된 token.json이 유효하지 않을 수 있으므로 삭제 시도
                    if os.path.exists(TOKEN_FILE):
                        try:
                            os.remove(TOKEN_FILE)
                        except OSError:
                            pass
                    raise

        # 인증 정보 저장
        if creds and creds.valid:
            try:
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
                logging.info(f"Credentials saved/updated in {TOKEN_FILE}")
            except Exception as e:
                logging.error(f"Failed to save credentials to {TOKEN_FILE}: {e}")
        elif not creds:
             # flow 객체 생성 실패 또는 인증 과정 실패 시
             raise ConnectionRefusedError("Failed to obtain valid credentials.")


    # YouTube API 서비스 빌드
    try:
        youtube = build("youtube", "v3", credentials=creds)
        logging.info("YouTube API service built successfully.")
        return youtube
    except Exception as e:
        logging.error(f"Failed to build YouTube API service: {str(e)}")
        raise ConnectionRefusedError("Failed to build YouTube service.")


def log_upload(video_id, title, description):
    """업로드 성공 로그 기록"""
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
            log_entry = f"{datetime.now().isoformat()} | SUCCESS | ID: {video_id} | Title: {title} | Desc: {description[:50]}... | URL: https://www.youtube.com/watch?v={video_id}\n"
            log_file.write(log_entry)
            logging.info(f"Logged successful upload: {video_id}")
    except Exception as e:
        logging.error(f"Failed to log upload for video {video_id}: {str(e)}")


def upload_video_to_youtube(youtube, file_path, title, description, thumbnail_path=None, duration_seconds=None):
    """비디오, 썸네일, 댓글을 유튜브에 업로드"""
    retries = 0
    last_exception = None
    while retries <= MAX_RETRIES:
        try:
            logging.info(f"Attempting to upload video: {file_path} (Attempt {retries + 1}/{MAX_RETRIES + 1})")
            logging.info(f"Title: {title}")
            logging.info(f"Description: {description[:100]}...")

            is_shorts = False
            if duration_seconds is not None and duration_seconds <= 60:
                is_shorts = True
                if "#Shorts" not in title: title += " #Shorts"
                if "#Shorts" not in description: description += "\n\n#Shorts"
                logging.info("Tagged as #Shorts based on duration.")

            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": [tag.strip() for tag in title.replace("#Shorts", "").split()[:15]], # 태그 수 약간 늘림
                    "categoryId": VIDEO_CATEGORY_ID
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            }

            media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            logging.info("Starting video upload...")
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        # 로그 빈도 조절
                        if progress == 0 or progress == 100 or progress % 20 == 0 :
                             logging.info(f"Upload progress: {progress}%")
                except HttpError as e:
                    logging.error(f"HTTP error during upload chunk: {e.resp.status} - {e.content}")
                    if e.resp.status in [500, 502, 503, 504]:
                        logging.warning("Resumable upload error (server-side). Retrying chunk...")
                        # 라이브러리가 재시도 처리할 수 있음, 잠시 대기 후 continue
                        time.sleep(5 * (retries + 1)) # 간단한 대기
                        continue
                    else:
                        logging.error("Non-recoverable HTTP error during upload chunk.")
                        raise # 치명적 오류는 재시도 루프로 전달
                except Exception as e:
                    logging.error(f"Error during upload chunk processing: {e}")
                    raise # 예상 못한 오류

            video_id = response["id"]
            logging.info(f"Video uploaded successfully! Video ID: {video_id}")
            logging.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")

            # 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                logging.info(f"Uploading thumbnail: {thumbnail_path}")
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logging.info(f"Thumbnail uploaded successfully for video {video_id}")
                except HttpError as e:
                    logging.warning(f"Failed to upload thumbnail (HTTP {e.resp.status}): {e.content}")
                except Exception as e:
                    logging.warning(f"Unexpected error uploading thumbnail: {e}")

            # 댓글 추가
            comment_text = f"AI가 생성한 '{title}' 영상입니다. 재미있게 보셨다면 구독과 좋아요 부탁드려요! #AI자동화 #자동생성"
            logging.info("Adding comment to video...")
            try:
                comment_body = {"snippet": {"videoId": video_id,"topLevelComment": {"snippet": {"textOriginal": comment_text}}}}
                youtube.commentThreads().insert(part="snippet",body=comment_body).execute()
                logging.info(f"Comment added successfully to video {video_id}")
            except HttpError as e:
                logging.warning(f"Failed to add comment (HTTP {e.resp.status}): {e.content}")
            except Exception as e:
                logging.warning(f"Unexpected error adding comment: {e}")

            log_upload(video_id, title, description)
            return video_id # 성공

        except HttpError as e:
            logging.error(f"YouTube API HTTP Error (Upload Attempt {retries + 1}): {e.resp.status} - {e.content}")
            last_exception = e
            if e.resp.status in [403]: # 할당량, 권한 등
                 logging.error("Quota exceeded or permission error. Stopping retries for upload.")
                 break # 재시도 중단
            elif e.resp.status in [500, 502, 503, 504]: # 서버 오류
                 retries += 1
                 wait_time = RETRY_DELAY_SECONDS * (2 ** (retries - 1)) # Exponential backoff
                 logging.warning(f"Server error. Retrying upload in {wait_time:.0f} seconds...")
                 time.sleep(wait_time)
                 continue
            else: # 기타 HTTP 오류
                 break # 재시도 중단
        except Exception as e:
            logging.error(f"An unexpected error occurred during video upload (Attempt {retries + 1}): {str(e)}")
            last_exception = e
            retries += 1
            if retries <= MAX_RETRIES:
                wait_time = RETRY_DELAY_SECONDS * (retries) # Linear backoff for unexpected errors
                logging.warning(f"Retrying upload in {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                continue
            else:
                logging.error("Max retries reached for unexpected error during upload.")
                break # 재시도 중단

    # 모든 재시도 후에도 실패한 경우
    logging.error(f"Failed to upload video '{title}' after all attempts.")
    if last_exception:
        raise ConnectionAbortedError(f"Upload failed permanently. Last error: {last_exception}") from last_exception
    else:
        raise ConnectionAbortedError("Upload failed permanently for unknown reasons.")


def cleanup_files(*file_paths):
    """생성된 임시 파일들 삭제"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to clean up file {file_path}: {e}")


# --- 메인 실행 로직 (이전 답변과 동일, TTS 호출 부분 확인) ---
def main():
    """메인 자동화 프로세스 실행 (비용 최소화 버전)"""
    logging.info("="*30)
    logging.info(f"Starting YouTube Automation Process (Cost-Optimized Mode v3) - Attempting {MAX_VIDEOS_PER_RUN} video(s)")
    logging.warning("Ensure API keys and quotas (OpenAI, ElevenLabs, YouTube) are sufficient.")
    logging.info("="*30)
    successful_uploads = 0
    youtube_service = None

    try:
        youtube_service = authenticate_youtube_api()
    except (ValueError, NotImplementedError, ConnectionRefusedError, Exception) as e: # 인증 실패 시 종료
        logging.critical(f"YouTube API authentication failed. Cannot proceed. Error: {e}")
        # traceback 로깅 추가
        import traceback
        logging.critical(traceback.format_exc())
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

            # 2. 스크립트 생성
            logging.warning("Calling OpenAI API (gpt-3.5-turbo)...")
            script_generated = False
            last_script_error = None
            for attempt in range(MAX_RETRIES + 1):
                try:
                    script = generate_script(topic)
                    script_generated = True
                    break
                except (openai.RateLimitError, openai.APIError, openai.Timeout, openai.APIServerError, ConnectionAbortedError) as e:
                    logging.error(f"Script Gen Error (Attempt {attempt+1}/{MAX_RETRIES+1}): {e}")
                    last_script_error = e
                    if isinstance(e, openai.RateLimitError) or isinstance(e, ConnectionAbortedError):
                        wait_time = RETRY_DELAY_SECONDS * (2**attempt)
                        logging.warning(f"Rate limit or persistent API error. Retrying in {wait_time:.0f}s...")
                        time.sleep(wait_time)
                    else: # Other API errors
                        time.sleep(RETRY_DELAY_SECONDS)
                except Exception as e:
                    logging.error(f"Unexpected Script Gen Error (Attempt {attempt+1}): {e}")
                    last_script_error = e
                    # Don't retry unexpected errors immediately, break and log
                    break
            if not script_generated:
                logging.error(f"Script generation failed after {MAX_RETRIES+1} attempts. Last error: {last_script_error}")
                continue # 다음 사이클로 (현재는 종료)

            # 3. 텍스트를 오디오로 변환
            logging.warning("Calling ElevenLabs API...")
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            if not voice_id: raise ValueError("Missing ElevenLabs Voice ID")

            audio_generated = False
            last_audio_error = None
            for attempt in range(MAX_RETRIES + 1):
                 try:
                     audio_path = text_to_speech(script, voice_id) # Use the correct function name
                     audio_generated = True
                     break
                 except (ConnectionAbortedError, ConnectionError, requests.exceptions.RequestException) as e:
                      logging.error(f"Audio Gen Error (Attempt {attempt+1}/{MAX_RETRIES+1}): {e}")
                      last_audio_error = e
                      if isinstance(e, ConnectionAbortedError): # Quota/Auth error
                           logging.error("Stopping retries due to quota/auth error.")
                           break
                      # Network errors
                      wait_time = RETRY_DELAY_SECONDS * (retries + 1)
                      logging.warning(f"Network error. Retrying in {wait_time:.0f}s...")
                      time.sleep(wait_time)
                 except Exception as e:
                      logging.error(f"Unexpected Audio Gen Error (Attempt {attempt+1}): {e}")
                      last_audio_error = e
                      break # Don't retry unexpected errors

            if not audio_generated:
                logging.error(f"Audio generation failed after attempts. Last error: {last_audio_error}")
                # 생성된 스크립트 파일 정리 등 고려
                continue # 다음 사이클로 (현재는 종료)

            # 4. 비디오 생성
            video_title = f"{topic} #Shorts"
            video_path, thumbnail_path, duration = generate_video(video_title, audio_path)
            logging.info(f"Video generated: {video_path} (Duration: {duration:.2f}s)")
            logging.info(f"Thumbnail generated: {thumbnail_path}")

            # 5. YouTube 업로드
            logging.warning("Calling YouTube API for upload...")
            video_description = f"'{topic}'에 대한 흥미로운 사실을 짧게 담았습니다.\n\n{script[:150]}...\n\n{DEFAULT_VIDEO_DESCRIPTION}"
            video_id = upload_video_to_youtube(youtube_service, video_path, video_title, video_description, thumbnail_path, duration)

            if video_id:
                successful_uploads += 1
            else:
                logging.warning(f"Upload failed for topic: {topic}") # upload_video_to_youtube에서 이미 에러 로깅/raise 함

        except (ConnectionAbortedError, ValueError, NotImplementedError, ConnectionRefusedError) as e:
             # 재시도 후에도 실패한 특정 오류들 또는 설정 오류
             logging.error(f"Stopping cycle {i+1} due to critical error: {e}")
             break # for 루프 탈출 (현재는 즉시 종료)
        except Exception as e:
            # 메인 루프에서의 예상치 못한 오류 처리
            logging.error(f"Unhandled error in main video cycle {i + 1} for topic '{topic}': {str(e)}")
            import traceback
            logging.error(traceback.format_exc()) # 상세 트레이스백 로깅

        finally:
            # 생성된 파일 정리 (오류 발생 여부와 관계없이 실행)
            logging.info("Cleaning up generated files for this cycle...")
            cleanup_files(audio_path, video_path, thumbnail_path)
            # audio_path 등이 정의되지 않았을 수 있으므로 cleanup_files 내부에서 None 체크 필요

    # 최종 마무리 로그
    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads in this run: {successful_uploads}")
    logging.info("Please check logs for any warnings or errors.")
    logging.info("="*30)

if __name__ == "__main__":
    main()
