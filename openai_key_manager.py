import os
import threading

class OpenAIKeyManager:
    def __init__(self):
        # 환경 변수에서 OpenAI API 키 목록을 읽어옵니다.
        keys = os.getenv("OPENAI_API_KEYS", "")
        self.api_keys = [k.strip() for k in keys.split(";") if k.strip()]
        self.lock = threading.Lock()
        self.index = 0

    def get_key(self):
        # 순차적으로 API 키를 가져옵니다.
        with self.lock:
            key = self.api_keys[self.index]
            self.index = (self.index + 1) % len(self.api_keys)
            return key

key_manager = OpenAIKeyManager()

