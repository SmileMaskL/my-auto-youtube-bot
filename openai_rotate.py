import os
import logging
from typing import List
from quota_manager import quota_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class OpenAIKeyManager:
    def __init__(self):
        self.keys: List[str] = []
        self._load_keys()
        
    def _load_keys(self) -> None:
        """환경 변수에서 키 불러오기"""
        key_str = os.getenv('OPENAI_API_KEYS', '')
        self.keys = [k.strip() for k in key_str.split(';') if k.strip()]
        
        if not self.keys:
            logging.critical("❌ No OpenAI keys found in environment")
            raise EnvironmentError("OPENAI_API_KEYS environment variable required")
            
        logging.info(f"🔑 Loaded {len(self.keys)} API keys")

    def get_active_key(self) -> str:
        """사용 가능한 키 선택"""
        for key in self.keys:
            if quota_manager.check_quota('openai', key):
                logging.info(f"🔄 Using key: {key[-6:]}")
                return key
                
        logging.warning("⚠️ All keys exhausted, resetting...")
        quota_manager.reset_daily_usage()
        return self.keys[0]

openai_manager = OpenAIKeyManager()

