# test_env.py 파일 생성 후 실행
import os
from dotenv import load_dotenv

load_dotenv()

required_keys = [
    'ELEVENLABS_KEY',
    'ELEVENLABS_VOICE_ID',
    'OPENAI_API_KEYS',
    'GOOGLE_CREDS',
    'YOUTUBE_CLIENT_SECRETS_JSON'
]

for key in required_keys:
    value = os.getenv(key)
    print(f"{key}: {'설정됨' if value else '누락됨'}")

# OPENAI 키 개수 확인
if os.getenv('OPENAI_API_KEYS'):
    print(f"\nOPENAI 키 개수: {len(os.getenv('OPENAI_API_KEYS').split(';'))}")
