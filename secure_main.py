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

# --- 설정 ---
# 환경 변수 로드 (.env 파일 우선)
load_dotenv()

# 로그 설정
LOG_FILE_PATH = ".secure_log.txt" # 로그 파일명
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH, encoding='utf-8'),
        logging.StreamHandler() # 콘솔에도 출력
    ]
)

# Google API 관련 설정
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRET_FILE = "client_secret.json" # 로컬용 파일 이름 (GitHub Secret에서 가져올 값과 다름)
TOKEN_FILE = "token.json" # 생성된 토큰 저장 파일 (Actions에서는 임시 저장)

# 비디오 생성/업로드 관련 설정
VIDEO_CATEGORY_ID = "22" # People & Blogs (카테고리 ID는 변경 가능)
DEFAULT_VIDEO_DESCRIPTION = "이 영상은 AI를 사용하여 자동으로 생성되었습니다. 최신 트렌드 정보를 재미있게 전달하기 위해 노력하고 있습니다. 구독과 좋아요 부탁드립니다!"
MAX_VIDEOS_PER_RUN = 2 # 한 번 실행 시 생성할 최대 비디오 수
RETRY_DELAY_SECONDS = 60 # API 오류 발생 시 재시도 대기 시간
MAX_RETRIES = 3 # 최대 재시도 횟수

# --- 함수 ---

def authenticate_youtube_api():
    """YouTube API 인증 및 서비스 객체 반환 (OAuth 2.0 사용)"""
    creds = None
    # 토큰 파일 로드 시도
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logging.info("Loaded credentials from token file.")
        except Exception as e:
            logging.warning(f"Failed to load credentials from {TOKEN_FILE}: {e}")

    # 유효한 인증 정보가 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Credentials expired, attempting to refresh...")
            try:
                creds.refresh(Request())
                logging.info("Credentials refreshed successfully.")
            except Exception as e:
                logging.error(f"Failed to refresh credentials: {e}. Need to re-authenticate.")
                creds = None # 새로 인증 필요
        else:
            logging.info("No valid credentials found, starting authentication flow.")
            # GitHub Secret에서 클라이언트 시크릿 JSON 문자열 가져오기
            client_secret_json_str = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
            if not client_secret_json_str:
                logging.error("GOOGLE_CLIENT_SECRET_JSON environment variable not set.")
                # 로컬 테스트용: client_secret.json 파일 사용 시도
                if os.path.exists(CLIENT_SECRET_FILE):
                     logging.info(f"Trying to use local {CLIENT_SECRET_FILE}")
                     flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                else:
                    raise ValueError("Cannot authenticate: GOOGLE_CLIENT_SECRET_JSON not set and client_secret.json not found.")
            else:
                try:
                    # 환경 변수에서 JSON 로드
                    client_config = json.loads(client_secret_json_str)
                    # 'installed' 또는 'web' 키 확인
                    if 'installed' in client_config:
                        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    elif 'web' in client_config:
                         # 웹 플로우는 GitHub Actions에서 직접 사용 불가 (리디렉션 필요)
                         # 미리 발급받은 리프레시 토큰이 JSON에 포함되어 있어야 함
                         # 이 경우 from_authorized_user_info 직접 사용 시도 가능 (아래 참고)
                         logging.warning("Using 'web' client type. Ensure refresh_token is available for non-interactive refresh.")
                         # 혹은 서비스 계정 사용 고려
                         raise NotImplementedError("Web flow authentication not directly supported in this script version for Actions without prior authorization.")
                    else:
                        raise ValueError("Invalid client secret JSON format: 'installed' or 'web' key missing.")

                except json.JSONDecodeError:
                    raise ValueError("Failed to parse GOOGLE_CLIENT_SECRET_JSON. Ensure it's a valid JSON string.")
                except Exception as e:
                    raise ValueError(f"Error initializing authentication flow: {e}")

            # 로컬 환경에서는 브라우저를 통해 인증 진행
            # GitHub Actions에서는 이 부분 실패 (사용자 인터랙션 불가)
            # => 해결책: Actions 실행 전에 로컬에서 한 번 인증하여 token.json 생성 후,
            #    token.json 내용을 Secret으로 저장하고 Actions에서 사용하거나,
            #    리프레시 토큰이 포함된 client_secret_json 사용.
            # 여기서는 리프레시 토큰이 GOOGLE_CLIENT_SECRET_JSON에 있다고 가정하고 시도.
            try:
                 # GitHub Actions 환경인지 확인 (CI 환경 변수 등)
                 if os.getenv("CI"): # GitHub Actions 등 CI 환경
                     logging.warning("Running in CI environment. Direct user authentication flow skipped.")
                     logging.warning("Attempting to use refresh token from GOOGLE_CLIENT_SECRET_JSON if available.")
                     # GOOGLE_CLIENT_SECRET_JSON에 refresh_token이 포함되어 있고,
                     # Credentials.from_authorized_user_info 또는 유사 방식으로 로드 시도
                     # 이 예제에서는 token.json이 미리 생성되어 Secret에 저장되었다고 가정
                     if not os.path.exists(TOKEN_FILE):
                          token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
                          if token_json_str:
                               logging.info("Found GOOGLE_TOKEN_JSON in environment variables. Writing to token.json")
                               with open(TOKEN_FILE, "w") as t_file:
                                    t_file.write(token_json_str)
                               creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                               # 즉시 리프레시 시도하여 유효성 검사
                               if creds and creds.refresh_token:
                                   creds.refresh(Request())
                               else:
                                   raise ValueError("Token JSON loaded, but no refresh token found or refresh failed.")
                          else:
                              raise ValueError("Cannot authenticate in CI environment without pre-existing token.json or GOOGLE_TOKEN_JSON secret.")
                 else:
                      # 로컬 환경: 사용자 인증 진행
                      logging.info("Please follow the authentication steps in your browser.")
                      creds = flow.run_local_server(port=0)
                      logging.info("Authentication successful.")

            except Exception as e:
                 logging.error(f"Authentication process failed: {e}")
                 raise

        # 생성/갱신된 인증 정보 저장 (Actions에서는 임시 저장)
        try:
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
            logging.info(f"Credentials saved to {TOKEN_FILE}")
        except Exception as e:
            logging.error(f"Failed to save credentials to {TOKEN_FILE}: {e}")


    # YouTube API 서비스 빌드
    try:
        youtube = build("youtube", "v3", credentials=creds)
        logging.info("YouTube API service built successfully.")
        return youtube
    except Exception as e:
        logging.error(f"Failed to build YouTube API service: {str(e)}")
        raise

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
    while retries <= MAX_RETRIES:
        try:
            logging.info(f"Attempting to upload video: {file_path} (Attempt {retries + 1})")
            logging.info(f"Title: {title}")
            logging.info(f"Description: {description[:100]}...")

            # Shorts 영상 조건 확인 및 태그 추가
            is_shorts = False
            if duration_seconds is not None and duration_seconds <= 60:
                # 가로/세로 비율 확인은 현재 불가 (영상 파일 분석 필요)
                # 우선 길이만으로 판단
                is_shorts = True
                if "#Shorts" not in title:
                    title += " #Shorts"
                if "#Shorts" not in description:
                    description += "\n\n#Shorts"
                logging.info("Video duration <= 60s, tagged as #Shorts.")


            body = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": [tag.strip() for tag in title.replace("#Shorts", "").split()[:10]], # 제목에서 태그 추출 (최대 10개)
                    "categoryId": VIDEO_CATEGORY_ID
                },
                "status": {
                    "privacyStatus": "public", # 또는 "private", "unlisted"
                    "selfDeclaredMadeForKids": False
                }
            }

            # 비디오 파일 업로드
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
                        # 로그 자주 남기지 않도록 조절 (예: 10% 단위)
                        if progress % 10 == 0:
                             logging.info(f"Upload progress: {progress}%")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        logging.warning(f"Resumable upload error (HTTP {e.resp.status}): {e}. Retrying...")
                        time.sleep(RETRY_DELAY_SECONDS * (2 ** retries)) # Exponential backoff
                        # request 객체 재생성 또는 재시도 로직 필요 (라이브러리가 자동 처리할 수도 있음)
                        # 여기서는 단순 재시도로 가정, 실제로는 더 복잡할 수 있음
                        continue # 같은 청크 재시도 (라이브러리 지원 시)
                    else:
                        logging.error(f"Non-recoverable HTTP error during upload: {e}")
                        raise
                except Exception as e:
                    logging.error(f"Error during upload chunk: {e}")
                    raise # 알 수 없는 오류 시 중단


            video_id = response["id"]
            logging.info(f"Video uploaded successfully! Video ID: {video_id}")
            logging.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")

            # 썸네일 업로드 시도
            if thumbnail_path and os.path.exists(thumbnail_path):
                logging.info(f"Uploading thumbnail: {thumbnail_path}")
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logging.info(f"Thumbnail uploaded successfully for video {video_id}")
                except HttpError as e:
                    logging.error(f"Failed to upload thumbnail: {e}")
                    # 썸네일 실패는 치명적이지 않을 수 있으므로 계속 진행
                except Exception as e:
                    logging.error(f"Unexpected error uploading thumbnail: {e}")

            # 댓글 추가 시도
            comment_text = f"AI가 생성한 '{title}' 영상입니다. 재미있게 보셨다면 구독과 좋아요 부탁드려요! #AI자동화"
            logging.info("Adding comment to video...")
            try:
                comment_body = {
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment_text
                            }
                        }
                    }
                }
                youtube.commentThreads().insert(
                    part="snippet",
                    body=comment_body
                ).execute()
                logging.info(f"Comment added successfully to video {video_id}")
            except HttpError as e:
                logging.error(f"Failed to add comment: {e}")
            except Exception as e:
                logging.error(f"Unexpected error adding comment: {e}")

            # 성공 로그 기록
            log_upload(video_id, title, description)
            return video_id # 성공 시 ID 반환

        except HttpError as e:
            logging.error(f"YouTube API HTTP error during upload process: {e}")
            if e.resp.status in [403]: # 할당량 초과 등 치명적 오류
                 logging.error("Quota exceeded or permission error. Stopping.")
                 raise # 재시도 불가
            elif e.resp.status in [500, 502, 503, 504]: # 서버 오류, 재시도 가능
                 retries += 1
                 logging.warning(f"Server error (HTTP {e.resp.status}). Retrying in {RETRY_DELAY_SECONDS * (2 ** retries)} seconds...")
                 time.sleep(RETRY_DELAY_SECONDS * (2 ** retries))
                 continue
            else: # 기타 HTTP 오류
                 raise
        except Exception as e:
            logging.error(f"An unexpected error occurred during video upload: {str(e)}")
            retries += 1
            if retries <= MAX_RETRIES:
                logging.warning(f"Retrying in {RETRY_DELAY_SECONDS * (2 ** retries)} seconds...")
                time.sleep(RETRY_DELAY_SECONDS * (2 ** retries))
                continue
            else:
                logging.error("Max retries reached. Upload failed.")
                raise # 최종 실패

    # 모든 재시도 실패 시
    raise Exception(f"Failed to upload video '{title}' after {MAX_RETRIES + 1} attempts.")


def cleanup_files(*file_paths):
    """생성된 임시 파일들 삭제"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Cleaned up file: {file_path}")
            except Exception as e:
                logging.warning(f"Failed to clean up file {file_path}: {e}")

# --- 메인 실행 로직 ---
def main():
    """메인 자동화 프로세스 실행"""
    logging.info("="*30)
    logging.info("Starting YouTube Automation Process")
    logging.info("="*30)
    successful_uploads = 0
    youtube_service = None # API 서비스 객체

    try:
        # 0. YouTube API 인증 (프로세스 시작 시 한 번만 수행)
        youtube_service = authenticate_youtube_api()
    except Exception as e:
        logging.error(f"YouTube API authentication failed. Cannot proceed. Error: {e}")
        return # 인증 실패 시 종료

    # 여러 비디오 생성 루프
    for i in range(MAX_VIDEOS_PER_RUN):
        logging.info(f"\n--- Starting Video Generation Cycle {i + 1} / {MAX_VIDEOS_PER_RUN} ---")
        script = None
        audio_path = None
        video_path = None
        thumbnail_path = None
        topic = None

        try:
            # 1. 트렌드 토픽 가져오기
            topic = get_trending_topic()
            logging.info(f"Selected Topic: {topic}")

            # 2. 스크립트 생성
            # 스크립트 생성 시도 및 재시도
            script_retries = 0
            while script_retries <= MAX_RETRIES:
                try:
                    script = generate_script(topic) # 약 60초 분량 목표
                    break # 성공 시 루프 탈출
                except openai.RateLimitError as e:
                    logging.warning(f"OpenAI rate limit error: {e}. Waiting and retrying...")
                    script_retries += 1
                    time.sleep(RETRY_DELAY_SECONDS * (2**script_retries))
                except Exception as e:
                     logging.error(f"Script generation failed: {e}")
                     script_retries += 1
                     if script_retries > MAX_RETRIES:
                          logging.error("Max retries reached for script generation. Skipping this video.")
                          raise # 루프 중단 또는 다음 비디오로 건너뛰기
                     time.sleep(RETRY_DELAY_SECONDS) # 다른 오류 시 잠시 대기 후 재시도

            if not script: continue # 스크립트 생성 최종 실패 시 다음 비디오로

            # 3. 텍스트를 오디오로 변환
            voice_id = os.getenv("ELEVENLABS_VOICE_ID")
            if not voice_id:
                logging.error("ELEVENLABS_VOICE_ID not set in environment variables.")
                raise ValueError("Missing ElevenLabs Voice ID")
            audio_path = text_to_audio(script, voice_id) # 생성된 오디오 파일 경로 반환
            logging.info(f"Audio generated: {audio_path}")

            # 4. 비디오 생성 (오디오 + 썸네일 기반)
            video_title = f"오늘의 트렌드: {topic}" # 비디오 제목 설정
            video_path, thumbnail_path, duration = generate_video(video_title, audio_path)
            logging.info(f"Video generated: {video_path} (Duration: {duration:.2f}s)")
            logging.info(f"Thumbnail generated: {thumbnail_path}")

            # 5. YouTube 업로드
            video_description = f"{topic}에 대한 최신 정보를 담은 영상입니다.\n\n{script[:300]}...\n\n{DEFAULT_VIDEO_DESCRIPTION}"
            video_id = upload_video_to_youtube(youtube_service, video_path, video_title, video_description, thumbnail_path, duration)

            if video_id:
                successful_uploads += 1
            else:
                logging.warning(f"Upload failed for topic: {topic}")

        except Exception as e:
            logging.error(f"Error in video cycle {i + 1} for topic '{topic}': {str(e)}")
            # 특정 단계 실패 시 다음 비디오 생성 시도 계속 (옵션)

        finally:
            # 6. 생성된 로컬 파일 정리
            logging.info("Cleaning up generated files for this cycle...")
            cleanup_files(audio_path, video_path, thumbnail_path)
            # token.json은 유지해야 다음 실행 시 인증 건너뜀 (Actions에서는 휘발성)

        # API 제한 고려: 각 비디오 생성 후 잠시 대기 (옵션)
        if i < MAX_VIDEOS_PER_RUN - 1:
            wait_time = random.uniform(10, 30) # 10~30초 랜덤 대기
            logging.info(f"Waiting for {wait_time:.1f} seconds before next cycle...")
            time.sleep(wait_time)


    logging.info("="*30)
    logging.info(f"YouTube Automation Process Finished. Successful uploads: {successful_uploads} / {MAX_VIDEOS_PER_RUN}")
    logging.info("="*30)

if __name__ == "__main__":
    main()
