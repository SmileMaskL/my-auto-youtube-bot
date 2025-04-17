import os
import json
import time
from datetime import datetime, timedelta
import openai
from openai_rotator import key_rotator

class EnhancedQuotaManager:
    def __init__(self):
        self.quota_file = 'static/logs/quota_status.json'
        self.quota_data = self._load_quota_data()
        self.rate_limits = {
            'youtube': {'daily': 10000, 'monthly': 300000},
            'openai': {'daily_per_key': 100, 'monthly': 3000},
            'elevenlabs': {'daily': 1000, 'monthly': 30000}
        }
        self._check_reset()

    def _load_quota_data(self):
        # [기존 코드 동일] (중략)

    def _initialize_quota_data(self):
        # [기존 코드 동일] (중략)

    def _check_reset(self):
        # [기존 코드 동일] (중략)

    def _sync_with_api(self, service: str):
        """실제 API 사용량과 로컬 데이터 동기화"""
        if service == 'openai':
            for key in key_rotator.keys:
                try:
                    client = openai.OpenAI(api_key=key)
                    usage = client.usage.retrieve(
                        start_date=datetime.now().strftime("%Y-%m-%d"),
                        end_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    self.quota_data['openai']['keys'][key] = usage.daily_usage
                except Exception as e:
                    logging.error(f"API 사용량 동기화 실패: {str(e)}")

    def check_quota(self, service: str, key: str = None) -> bool:
        """향상된 쿼터 체크 로직"""
        self._sync_with_api(service)
        
        if service == 'youtube':
            used = self.quota_data['youtube']['daily_used']
            return used < self.rate_limits['youtube']['daily']
        
        elif service == 'openai' and key:
            key_usage = self.quota_data['openai']['keys'].get(key, 0)
            return key_usage < self.rate_limits['openai']['daily_per_key']
        
        elif service == 'elevenlabs':
            return self.quota_data['elevenlabs']['daily_used'] < self.rate_limits['elevenlabs']['daily']
        
        return False

    def update_usage(self, service: str, amount: int = 1, key: str = None):
        """동적 가중치 반영 업데이트"""
        weight = self._calculate_dynamic_weight(service)
        adjusted_amount = int(amount * weight)
        
        if service == 'youtube':
            self.quota_data['youtube']['daily_used'] += adjusted_amount
        elif service == 'openai' and key:
            self.quota_data['openai']['keys'][key] = self.quota_data['openai']['keys'].get(key, 0) + adjusted_amount
        elif service == 'elevenlabs':
            self.quota_data['elevenlabs']['daily_used'] += adjusted_amount
        
        self._save_quota_data()

    def _calculate_dynamic_weight(self, service: str) -> float:
        """API 응답시간 기반 가중치 계산"""
        response_times = {
            'youtube': 2.0,  # 기본값
            'openai': 1.5,
            'elevenlabs': 1.8
        }
        # 실시간 모니터링 데이터 적용 가능한 구조
        return min(2.0, max(0.5, 1 / response_times.get(service, 1.0)))

    def optimize_schedule(self):
        """쿼터 사용 패턴 기반 자동 스케줄 조정"""
        avg_usage = self._calculate_avg_usage()
        for service in self.rate_limits:
            if avg_usage[service] > 0.8:
                self.rate_limits[service]['daily'] = int(
                    self.rate_limits[service]['daily'] * 0.9
                )

    def _calculate_avg_usage(self) -> dict:
        """서비스별 평균 사용량 계산"""
        return {
            service: (self.quota_data[service]['daily_used'] / 
                     self.rate_limits[service]['daily'])
            for service in self.rate_limits
        }

# Singleton 인스턴스 생성
quota_manager = EnhancedQuotaManager()

