import os
import json
import time
from datetime import datetime, timedelta

class QuotaManager:
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
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, 'r') as f:
                    return json.load(f)
            except:
                return self._initialize_quota_data()
        return self._initialize_quota_data()

    def _initialize_quota_data(self):
        return {
            'youtube': {'daily_used': 0, 'monthly_used': 0, 'last_reset': datetime.now().isoformat()},
            'openai': {'keys': {}, 'monthly_used': 0, 'last_reset': datetime.now().isoformat()},
            'elevenlabs': {'daily_used': 0, 'monthly_used': 0, 'last_reset': datetime.now().isoformat()},
            'last_updated': datetime.now().isoformat()
        }

    def _check_reset(self):
        now = datetime.now()
        for service in ['youtube', 'openai', 'elevenlabs']:
            last_reset = datetime.fromisoformat(self.quota_data[service]['last_reset'])
            
            # 매일 리셋 체크
            if (now - last_reset) >= timedelta(days=1):
                self._reset_daily_usage(service)
            
            # 매월 1일 리셋 체크
            if now.day == 1 and (now - last_reset) >= timedelta(days=1):
                self._reset_monthly_usage(service)

    def _reset_daily_usage(self, service):
        if service == 'youtube':
            self.quota_data['youtube']['daily_used'] = 0
        elif service == 'openai':
            self.quota_data['openai']['keys'] = {k:0 for k in self.quota_data['openai']['keys']}
        elif service == 'elevenlabs':
            self.quota_data['elevenlabs']['daily_used'] = 0
        
        self.quota_data[service]['last_reset'] = datetime.now().isoformat()
        self._save_quota_data()

    def _reset_monthly_usage(self, service):
        if service == 'youtube':
            self.quota_data['youtube']['monthly_used'] = 0
        elif service == 'openai':
            self.quota_data['openai']['monthly_used'] = 0
        elif service == 'elevenlabs':
            self.quota_data['elevenlabs']['monthly_used'] = 0
        
        self._reset_daily_usage(service)

    def _save_quota_data(self):
        self.quota_data['last_updated'] = datetime.now().isoformat()
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        with open(self.quota_file, 'w') as f:
            json.dump(self.quota_data, f, indent=2)

    def check_quota(self, service, key=None):
        self._check_reset()
        
        if service == 'youtube':
            daily_remaining = self.rate_limits['youtube']['daily'] - self.quota_data['youtube']['daily_used']
            monthly_remaining = self.rate_limits['youtube']['monthly'] - self.quota_data['youtube']['monthly_used']
            return min(daily_remaining, monthly_remaining) > 0
        
        elif service == 'openai' and key:
            if key not in self.quota_data['openai']['keys']:
                return True
            daily_remaining = self.rate_limits['openai']['daily_per_key'] - self.quota_data['openai']['keys'][key]
            monthly_remaining = self.rate_limits['openai']['monthly'] - self.quota_data['openai']['monthly_used']
            return min(daily_remaining, monthly_remaining) > 0
        
        elif service == 'elevenlabs':
            daily_remaining = self.rate_limits['elevenlabs']['daily'] - self.quota_data['elevenlabs']['daily_used']
            monthly_remaining = self.rate_limits['elevenlabs']['monthly'] - self.quota_data['elevenlabs']['monthly_used']
            return min(daily_remaining, monthly_remaining) > 0
        
        return False

    def update_usage(self, service, amount=1, key=None):
        if service == 'youtube':
            self.quota_data['youtube']['daily_used'] += amount
            self.quota_data['youtube']['monthly_used'] += amount
        elif service == 'openai' and key:
            if key not in self.quota_data['openai']['keys']:
                self.quota_data['openai']['keys'][key] = 0
            self.quota_data['openai']['keys'][key] += amount
            self.quota_data['openai']['monthly_used'] += amount
        elif service == 'elevenlabs':
            self.quota_data['elevenlabs']['daily_used'] += amount
            self.quota_data['elevenlabs']['monthly_used'] += amount
        
        self._save_quota_data()

    def get_status(self):
        self._check_reset()
        return {
            'youtube': {
                'daily_used': self.quota_data['youtube']['daily_used'],
                'daily_limit': self.rate_limits['youtube']['daily'],
                'monthly_used': self.quota_data['youtube']['monthly_used'],
                'monthly_limit': self.rate_limits['youtube']['monthly']
            },
            'openai': {
                'keys': {k: v for k, v in self.quota_data['openai']['keys'].items()},
                'daily_limit_per_key': self.rate_limits['openai']['daily_per_key'],
                'monthly_used': self.quota_data['openai']['monthly_used'],
                'monthly_limit': self.rate_limits['openai']['monthly']
            },
            'elevenlabs': {
                'daily_used': self.quota_data['elevenlabs']['daily_used'],
                'daily_limit': self.rate_limits['elevenlabs']['daily'],
                'monthly_used': self.quota_data['elevenlabs']['monthly_used'],
                'monthly_limit': self.rate_limits['elevenlabs']['monthly']
            }
        }

# Singleton 인스턴스 생성
quota_manager = QuotaManager()
