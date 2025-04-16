import os
import json
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Logging 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 파일과 환경 변수 정의
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
TOKEN_FILE = "token.json"

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
            client_secret_json_str = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON")
            if not client_secret_json_str:
                raise ValueError("YOUTUBE_CLIENT_SECRETS_JSON environment variable is missing!")

            try:
                config = json.loads(client_secret_json_str)
                flow = InstalledAppFlow.from_client_config(config, SCOPES)
                creds = flow.run_local_server(port=8080)
                logging.info("Authentication successful.")
            except Exception as e:
                logging.error(f"Error during authentication: {e}")
                raise

        if creds and creds.valid:
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
                logging.info(f"Saved credentials to {TOKEN_FILE}.")
        else:
            raise ConnectionRefusedError("Failed to obtain valid credentials.")

    try:
        youtube = build("youtube", "v3", credentials=creds)
        logging.info("YouTube API service built successfully.")
        return youtube
    except Exception as e:
        logging.error(f"Failed to build YouTube API service: {e}")
        raise ConnectionRefusedError("Failed to build YouTube service.")

if __name__ == "__main__":
    youtube = authenticate_youtube_api()
    logging.info("YouTube API 인증 완료!")
