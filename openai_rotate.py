import os
import random
import time

# 현재 API 호출 사용량을 확인하는 가상의 함수
def get_current_usage(api_key):
    # 여기서 실제 사용량을 체크하는 로직을 추가합니다.
    # 예시로 랜덤 값으로 반환합니다.
    return random.randint(0, 1000)

# API 호출 쿼터 체크 함수
def check_api_quota(api_key):
    quota_limit = 1000  # 하루 호출 한도 예시
    current_usage = get_current_usage(api_key)
    if current_usage >= quota_limit:
        print(f"API 한도가 초과되었습니다. 대기 중...")
        time.sleep(3600)  # 1시간 대기 후 재시도
        return False
    return True

# 최적의 API 키를 선택하는 함수
def use_api_key_optimally():
    available_keys = [
        os.getenv("OPENAI_API_KEY_1"),
        os.getenv("OPENAI_API_KEY_2"),
        os.getenv("OPENAI_API_KEY_3"),
        os.getenv("OPENAI_API_KEY_4"),
        os.getenv("OPENAI_API_KEY_5"),
        os.getenv("OPENAI_API_KEY_6"),
        os.getenv("OPENAI_API_KEY_7"),
        os.getenv("OPENAI_API_KEY_8"),
        os.getenv("OPENAI_API_KEY_9"),
        os.getenv("OPENAI_API_KEY_10")
    ]
    
    for key in available_keys:
        if check_api_quota(key):
            return key  # 유효한 API 키 반환
    
    return None  # 모든 키가 초과되었으면 None 반환

def get_openai_api_key():
    key = use_api_key_optimally()
    if key:
        print(f"현재 사용 중인 OpenAI API 키: {key}")
        return key
    else:
        raise Exception("모든 OpenAI API 키가 초과되었습니다.")

