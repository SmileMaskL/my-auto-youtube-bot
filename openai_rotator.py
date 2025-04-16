import os
import sys
import logging
from typing import List

class OpenAIKeyManager:
    def __init__(self):
        self.keys = self._validate_keys()
        self.current_index = 0
        logging.info(f"🔑 키 로테이션 초기화: {len(self.keys)}개")

    def _validate_keys(self) -> List[str]:
        """키 검증 시스템 8.0"""
        key_str = os.getenv('OPENAI_API_KEYS', '').strip()
        if not key_str:
            logging.critical("❌ .env 파일 또는 GitHub Secrets에 OPENAI_API_KEYS가 없습니다!")
            sys.exit(1)
        
        keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        if len(keys) != 10:
            logging.critical(f"⚠️ 키 개수 오류: {len(keys)}/10 (반드시 10개 필요)")
            sys.exit(1)
        return keys

    def get_key(self) -> str:
        """완벽한 순환 알고리즘"""
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % 10
        logging.debug(f"🔄 {self.current_index+1}번째 키 사용")
        return key

key_rotator = OpenAIKeyManager()

