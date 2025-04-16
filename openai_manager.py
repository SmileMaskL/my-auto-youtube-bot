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
        
        if len(keys) < 5:  # 최소 5개 키 요구
            logging.critical(f"⚠️ 키 개수 부족: {len(keys)}/5 (최소 5개 필요, 권장 10개)")
            sys.exit(1)
            
        logging.info(f"✅ 키 검증 완료: {len(keys)}개")
        return keys

    def get_valid_key(self) -> str:
        """유효한 키를 찾아 반환 (로테이션 + 쿼터 확인)"""
        attempts = 0
        max_attempts = len(self.keys) * 2  # 모든 키를 두 번씩 시도
        
        while attempts < max_attempts:
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            
            # 실패한 키는 건너뛰기
            if key in self.failed_keys:
                attempts += 1
                continue
                
            # 쿼터 확인
            if quota_manager.check_quota('openai', key):
                logging.debug(f"🔄 {self.current_index+1}번째 키 사용 (쿼터 여유 있음)")
                return key
            else:
                logging.warning(f"⚠️ {self.current_index+1}번째 키 쿼터 초과. 다음 키 시도")
                self.failed_keys.add(key)
                
            attempts += 1
            
        logging.error("🚨 사용 가능한 OpenAI 키가 없습니다. 모든 키의 쿼터가 소진되었거나 유효하지 않습니다.")
        raise RuntimeError("No valid OpenAI keys available")

    def report_key_failure(self, key: str):
        """실패한 키 보고"""
        if key in self.keys:
            self.failed_keys.add(key)
            logging.warning(f"⚠️ 키 실패 보고: {key[:5]}...{key[-5:]} (실패 키 수: {len(self.failed_keys)})")

    def get_active_key_count(self) -> int:
        """활성 키 수 반환"""
        return len([k for k in self.keys if k not in self.failed_keys])

    def reset_failed_keys(self):
        """실패한 키 리셋 (매일 자정에 실행 권장)"""
        self.failed_keys = set()
        logging.info("✅ 실패한 키 기록 초기화 완료")

# Singleton 인스턴스 생성
openai_manager = OpenAIManager()
