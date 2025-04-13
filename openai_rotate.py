import os
import random
import time

def get_current_usage(api_key):
    return random.randint(0, 1000)

def check_api_quota(api_key):
    quota_limit = 1000
    current_usage = get_current_usage(api_key)
    if current_usage >= quota_limit:
        print(f"API 한도가 초과되었습니다. 대기 중...")
        time.sleep(3600)
        return False
    return True

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
            return key
    
    return None

def get_openai_api_key():
    key = use_api_key_optimally()
    if key:
        print(f"현재 사용 중인 OpenAI API 키: {key}")
        return key
    else:
        raise Exception("모든 OpenAI API 키가 초과되었습니다.")

