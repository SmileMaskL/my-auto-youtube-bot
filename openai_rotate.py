import os
import sys
import logging
from typing import List

class OpenAIKeyManager:
    def __init__(self):
        self.keys = self._validate_keys()
        self.index = 0

    def _validate_keys(self) -> List[str]:
        """키 검증 시스템 5.0"""
        key_str = os.getenv('OPENAI_API_KEYS', '')
        
        if not key_str:
            logging.critical("❌ .env 파일에 키가 없거나 GitHub Secrets 미설정")
            sys.exit(1)

        keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        
        if len(keys) != 10:
            logging.error(f"⚠️ 키 개수 오류: {len(keys)}/10 (반드시 10개 필요)")
            sys.exit(1)
            
        logging.info(f"🔑 키 검증 완료: {len(keys)}개")
        return keys

    def get_next_key(self) -> str:
        """완벽한 키 순환 로직"""
        key = self.keys[self.index]
        self.index = (self.index + 1) % 10
        logging.debug(f"🔄 키 변경: {self.index}번째 사용")
        return key

key_manager = OpenAIKeyManager()

