import os
import logging
from typing import List

class OpenAIKeyManager:
    def __init__(self):
        self.keys: List[str] = []
        self.current_index = 0
        self._load_keys()

    def _load_keys(self):
        """환경 변수에서 키 로드"""
        key_str = os.getenv('OPENAI_API_KEYS', '')
        if not key_str:
            raise EnvironmentError("OPENAI_API_KEYS 환경 변수 필요")
            
        self.keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        if len(self.keys) < 10:
            logging.warning(f"경고: {len(self.keys)}/10 개의 키만 발견됨")
            
        logging.info(f"🔑 총 {len(self.keys)} 개의 OpenAI 키 로드됨")

    def get_key(self):
        """로테이션으로 키 제공"""
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key

# 초기화
try:
    openai_manager = OpenAIKeyManager()
except Exception as e:
    logging.critical(f"❌ OpenAI 초기화 실패: {str(e)}")
    sys.exit(1)

