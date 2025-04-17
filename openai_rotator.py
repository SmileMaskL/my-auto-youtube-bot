# openai_rotator.py
import os
import logging
from typing import List
import time

class OpenAIKeyManager:
    def __init__(self):
        self.keys = self._validate_keys()
        self.usage_counter = {key: {'count':0, 'last_used':0} for key in self.keys}
        self.circuit_breaker = {key: {'state':'closed', 'expiry':0} for key in self.keys}
        logging.info(f"🔑 초기화 완료: {len(self.keys)}개 키 로드")

    def _validate_keys(self) -> List[str]:
        key_str = os.getenv('OPENAI_API_KEYS', '')
        if not key_str:
            raise EnvironmentError("OPENAI_API_KEYS 환경 변수 없음")
        return [k.strip() for k in key_str.split(';') if k.startswith('sk-')]

    def get_key(self) -> str:
        now = time.time()
        sorted_keys = sorted(
            self.keys,
            key=lambda k: (
                self.circuit_breaker[k]['state'] == 'open',
                -self.usage_counter[k]['count'],
                self.usage_counter[k]['last_used']
            )
        )
        
        for key in sorted_keys:
            if self.circuit_breaker[key]['state'] == 'closed' or \
               self.circuit_breaker[key]['expiry'] < now:
                self.usage_counter[key]['count'] += 1
                self.usage_counter[key]['last_used'] = now
                return key
        
        raise RuntimeError("사용 가능한 API 키 없음")

    def report_error(self, key: str):
        self.circuit_breaker[key] = {
            'state': 'open',
            'expiry': time.time() + 300  # 5분 차단
        }

key_rotator = OpenAIKeyManager()

