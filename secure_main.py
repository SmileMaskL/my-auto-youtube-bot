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

            client_secret_json_str = os.getenv("GOOGLE_CLIENT_SECRET_JSON") 
            if not client_secret_json_str:
                client_secret_json_str = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON")

            flow = None

            if not client_secret_json_str:
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
                logging.info(f"Found client secret JSON in environment variable.")
                try:
                    client_config = json.loads(client_secret_json_str)
                    logging.info("Successfully parsed client secret JSON from environment variable.")

                    if 'installed' in client_config:
                        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    elif 'web' in client_config:
                        raise NotImplementedError("Web client type requires pre-authorization or service account.")
                    else:
                        raise ValueError("Invalid client secret JSON format: 'installed' or 'web' key missing.")

                except json.JSONDecodeError as e:
                    logging.error(f"JSONDecodeError: Failed to parse client secret JSON from env var. Error: {e}")
                    raise ValueError("Failed to parse client secret JSON from env var.") from e
                except Exception as e:
                    logging.error(f"Error processing client secret JSON from env var: {e}")
                    raise ValueError(f"Error initializing authentication flow from env var: {e}")

            if flow:
                try:
                    if os.getenv("CI"): 
                        logging.warning("Running in CI environment. Attempting to use stored token (GOOGLE_TOKEN_JSON).")
                        if not os.path.exists(TOKEN_FILE):
                            token_json_str = os.getenv("GOOGLE_TOKEN_JSON")
                            if token_json_str:
                                logging.info("Found GOOGLE_TOKEN_JSON. Writing to token.json")
                                try:
                                    token_data = json.loads(token_json_str)
                                    with open(TOKEN_FILE, "w") as t_file: json.dump(token_data, t_file)
                                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                                    if creds and creds.refresh_token: creds.refresh(Request()); logging.info("Token refreshed.")
                                    elif creds and creds.valid: logging.info("Token loaded is valid.")
                                    else: raise ValueError("Token lacks refresh token or is invalid.")
                                except json.JSONDecodeError: raise ValueError("Invalid GOOGLE_TOKEN_JSON content.")
                                except Exception as e: logging.error(f"Error processing GOOGLE_TOKEN_JSON: {e}"); raise
                            else: raise ValueError("Cannot authenticate in CI: GOOGLE_TOKEN_JSON secret required.")
                    else:
                        # 로컬 인증 개선: 브라우저 자동 실행, 포트 지정 
                        logging.info("Starting local authentication server on port 8080...")
                        # 자동으로 브라우저 열기
                        creds = flow.run_local_server(port=8080, open_browser=True, 
                                                     success_message="인증 성공! 이 탭은 닫으셔도 됩니다.")
                        logging.info("Authentication successful.")
                except Exception as e:
                    logging.error(f"Authentication process failed: {e}")
                    if os.path.exists(TOKEN_FILE):
                        try:
                            os.remove(TOKEN_FILE)
                            logging.info(f"Removed potentially invalid {TOKEN_FILE}")
                        except OSError as rm_e:
                            logging.warning(f"Could not remove {TOKEN_FILE}: {rm_e}")
                    raise

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
