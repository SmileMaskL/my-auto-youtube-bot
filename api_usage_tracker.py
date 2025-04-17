import time
import json
import os

class APIUsageTracker:
    def __init__(self, usage_file='api_usage.json', max_calls_per_key=50):
        self.usage_file = usage_file
        self.max_calls_per_key = max_calls_per_key
        self.load_usage()

    def load_usage(self):
        if os.path.exists(self.usage_file):
            with open(self.usage_file, 'r') as f:
                self.usage = json.load(f)
        else:
            self.usage = {}

    def save_usage(self):
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage, f)

    def increment_usage(self, api_key):
        today = time.strftime('%Y-%m-%d')
        if api_key not in self.usage:
            self.usage[api_key] = {}
        if today not in self.usage[api_key]:
            self.usage[api_key][today] = 0
        self.usage[api_key][today] += 1
        self.save_usage()

    def is_quota_exceeded(self, api_key):
        today = time.strftime('%Y-%m-%d')
        return self.usage.get(api_key, {}).get(today, 0) >= self.max_calls_per_key

