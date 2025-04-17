from openai_key_manager import key_manager
from api_usage_tracker import APIUsageTracker

# API 사용 추적 객체를 생성합니다.
usage_tracker = APIUsageTracker()

def get_available_api_key():
    # 모든 키를 확인하여 사용할 수 있는 키를 찾아 반환합니다.
    for _ in range(len(key_manager.api_keys)):
        api_key = key_manager.get_key()
        if not usage_tracker.is_quota_exceeded(api_key):
            usage_tracker.increment_usage(api_key)
            return api_key
    raise Exception("All API keys have exceeded their quota.")

# 여기에 추가적으로 사용할 함수가 있을 경우 계속 추가하세요.

