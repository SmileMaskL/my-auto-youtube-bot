import os
from dotenv import load_dotenv
import openai
from youtube_uploader import youtube_uploader

load_dotenv()

# API 키 로테이션을 위한 클래스
class APIKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def get_key(self):
        return self.keys[self.index]

    def rotate_key(self):
        self.index = (self.index + 1) % len(self.keys)
        openai.api_key = self.get_key()

openai_keys = os.getenv("OPENAI_API_KEYS")
if not openai_keys:
    raise ValueError("OPENAI_API_KEYS 가 .env에 설정되지 않았습니다.")

key_manager = APIKeyManager(openai_keys.split(","))
openai.api_key = key_manager.get_key()

# 오류 발생 시 키 교체 후 재시도
def safe_openai_call(prompt):
    try:
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
    except openai.error.RateLimitError:
        print("RateLimitError 발생, 다음 키로 교체")
        key_manager.rotate_key()
        return safe_openai_call(prompt)

# 자동 실행 설정
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="자동 실행 여부")
    parser.add_argument("--max-videos", type=int, default=1)
    args = parser.parse_args()

    youtube_uploader.run(
        auto=args.auto,
        max_videos=args.max_videos
    )

