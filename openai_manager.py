import os
import sys
import logging
from typing import List
from quota_manager import quota_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OpenAIManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.keys = self._validate_keys()
        self.current_index = 0
        self.failed_keys = set()
        logging.info(f"🔑 OpenAI 키 관리자 초기화 완료. 활성 키: {len(self.keys)}개")

    def _validate_keys(self) -> List[str]:
        """키 검증 시스템 9.0"""
        key_str = os.getenv('OPENAI_API_KEYS', '').strip()
        if not key_str:
            logging.critical("❌ .env 또는 GitHub Secrets에 OPENAI_API_KEYS가 없습니다!")
            sys.exit(1)
        
        keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        
        if len(keys) < 5:
            logging.critical(f"⚠️ 키 개수 부족: {len(keys)}/5 (최소 5개 필요)")
            sys.exit(1)
            
        logging.info(f"✅ 키 검증 완료: {len(keys)}개")
        return keys

    def get_valid_key(self) -> str:
        """로테이션 알고리즘 개선 버전"""
        for _ in range(len(self.keys)):
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            if key not in self.failed_keys and quota_manager.check_quota('openai', key):
                return key
                
        logging.error("🚨 사용 가능한 OpenAI 키가 없습니다")
        raise RuntimeError("No valid OpenAI keys available")

openai_manager = OpenAIManager()
