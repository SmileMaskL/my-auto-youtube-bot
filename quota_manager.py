import os
import json
import time
from datetime import datetime

class QuotaManager:
    def __init__(self):
        self.quota_file = 'quota_status.json'
        self.quota_data = self._load_quota_data()
        self.rate_limits = {
            'youtube': {'daily': 10000, 'monthly': 300000},
            'openai': {'daily_per_key': 100, 'monthly': 3000},
            'elevenlabs': {'daily': 1000, 'monthly': 30000}
        }

    def _load_quota_data(self):
        if os.path.exists(self.quota_file):
            with open(self.quota_file, 'r') as f:
                return json.load(f)
        else:
            return {
                'youtube': {'daily_used': 0, 'monthly_used': 0},
                'openai': {'keys': {}, 'monthly_used': 0},
                'elevenlabs': {'daily_used': 0, 'monthly_used': 0},
                'last_updated': datetime.now().isoformat()
            }

    def _save_quota_data(self):
        self.quota_data['last_updated'] = datetime.now().isoformat()
        with open(self.quota_file, 'w') as f:
            json.dump(self.quota_data, f, indent=2)

    def check_quota(self, service, key=None):
        now = datetime.now()
        if now.day == 1:  # 매월 1일 리셋
            self.reset_monthly_usage()

        if service == 'youtube':
            return self.quota_data['youtube']['daily_used'] < self.rate_limits['youtube']['daily']
        elif service == 'openai' and key:
            key_usage = self.quota_data['openai']['keys'].get(key, 0)
            return key_usage < self.rate_limits['openai']['daily_per_key']
        elif service == 'elevenlabs':
            return self.quota_data['elevenlabs']['daily_used'] < self.rate_limits['elevenlabs']['daily']
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

    def reset_daily_usage(self):
        self.quota_data['youtube']['daily_used'] = 0
        self.quota_data['openai']['keys'] = {k:0 for k in self.quota_data['openai']['keys']}
        self.quota_data['elevenlabs']['daily_used'] = 0
        self._save_quota_data()

    def reset_monthly_usage(self):
        self.quota_data['youtube']['monthly_used'] = 0
        self.quota_data['openai']['monthly_used'] = 0
        self.quota_data['elevenlabs']['monthly_used'] = 0
        self.reset_daily_usage()

    def get_status(self):
        return self.quota_data

# Singleton 인스턴스 생성
quota_manager = QuotaManager()

