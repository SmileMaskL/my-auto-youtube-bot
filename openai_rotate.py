import os
import sys
import logging
from typing import List

class OpenAIKeyRotator:
    def __init__(self):
        self.keys = self._validate_keys()
        self.current_idx = 0
        
    def _validate_keys(self) -> List[str]:
        """키 검증 시스템 6.0"""
        key_str = os.getenv('OPENAI_API_KEYS', '')
        if not key_str:
            logging.critical("❌ 키가 없습니다. .env 또는 GitHub Secrets 확인")
            sys.exit(1)
            
        keys = [k.strip() for k in key_str.split(';') if k.startswith('sk-')]
        
        if len(keys) != 10:
            logging.error(f"⚠️ 키 개수 오류: {len(keys)}/10 (반드시 10개 필요)")
            sys.exit(1)
            
        logging.info(f"✅ 키 검증 완료: {len(keys)}개")
        return keys
    
    def get_key(self) -> str:
        """완벽한 키 순환 시스템"""
        key = self.keys[self.current_idx]
        self.current_idx = (self.current_idx + 1) % 10
        logging.debug(f"🔄 {self.current_idx}번 키 사용")
        return key

key_rotator = OpenAIKeyRotator()

