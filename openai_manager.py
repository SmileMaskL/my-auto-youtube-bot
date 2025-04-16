import os
import sys
import logging
from typing import List

class OpenAIRotation:
    def __init__(self):
        self.keys = self._validate_keys()
        self.index = 0
        logging.info(f"🔑 활성화된 키: {len(self.keys)}개")

    def _validate_keys(self) -> List[str]:
        """키 검증 시스템 7.0"""
        key_str = os.getenv('OPENAI_API_KEYS', '')
        if not key_str:
            logging.critical("❌ .env 또는 GitHub Secrets에 키가 없습니다!")
            sys.exit(1)

        keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        if len(keys) != 10:
            logging.error(f"⚠️ 키 개수 오류: {len(keys)}/10")
            sys.exit(1)
        return keys

    def get_key(self) -> str:
        """완벽한 순환 로직"""
        key = self.keys[self.index]
        self.index = (self.index + 1) % 10
        logging.debug(f"🔄 {self.index}번 키 사용")
        return key

key_manager = OpenAIRotation()

