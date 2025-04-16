import os
import random
import logging
from quota_manager import quota_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenAIManager:
    def __init__(self):
        self.keys = self._load_keys()
        self.current_key = None

    def _load_keys(self):
        keys = []
        for i in range(1, 11):
            key = os.getenv(f'OPENAI_API_KEY_{i}')
            if key and key.strip():
                keys.append(key.strip())
        if not keys:
            raise ValueError("No valid OpenAI API keys found in environment variables")
        return keys

    def get_active_key(self):
        valid_keys = [k for k in self.keys if quota_manager.check_quota('openai', k)]
        if not valid_keys:
            logging.warning("All OpenAI keys exhausted. Resetting daily usage...")
            quota_manager.reset_daily_usage()
            valid_keys = self.keys  # 재시도 위해 모든 키 반환

        # 사용량이 가장 적은 키 선택
        valid_keys.sort(key=lambda k: quota_manager.quota_data['openai']['keys'].get(k, 0))
        self.current_key = valid_keys[0]
        return self.current_key

    def track_usage(self, prompt_tokens, completion_tokens):
        if self.current_key:
            total_tokens = prompt_tokens + completion_tokens
            quota_manager.update_usage('openai', total_tokens, self.current_key)
            logging.info(f"Updated OpenAI usage for key {self.current_key[-5:]}: +{total_tokens} tokens")

# 전역 인스턴스 생성
openai_manager = OpenAIManager()

