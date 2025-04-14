import os
import random
import time
import logging

# 사용 가능한 OpenAI API 키 목록을 환경 변수에서 로드
# 예: OPENAI_API_KEY_1, OPENAI_API_KEY_2, ...
def get_available_keys():
    keys = []
    i = 1
    while True:
        key = os.getenv(f"OPENAI_API_KEY_{i}")
        if key:
            keys.append(key)
            i += 1
        else:
            # 키가 더 이상 없으면 중단 (최대 10개 또는 그 이상 탐색 가능)
            if i > 10: # 너무 많은 키를 탐색하지 않도록 제한
                break
            break # 혹은 키가 순차적이지 않을 수 있으므로 계속 탐색? 여기서는 순차적으로 가정
    return keys

# !! 중요 !!
# 이 함수는 실제 API 사용량이나 할당량을 **확인하지 않습니다**.
# 단순히 사용 가능한 키 목록에서 무작위로 하나를 선택하거나,
# 간단한 (가상의) 확인 로직 후 첫 번째 유효한 키를 반환합니다.
# 실제 할당량 관리는 OpenAI 대시보드 모니터링과 API 응답 오류(429 등) 처리를 통해 구현해야 합니다.
def get_current_usage(api_key):
    """가상의 사용량 확인 함수 (실제 구현 아님)"""
    # 실제로는 OpenAI API를 호출하여 사용량을 확인하거나,
    # 자체적으로 사용량을 추적하는 로직이 필요합니다.
    # 여기서는 단순히 무작위 값을 반환하여 로직 흐름만 보여줍니다.
    logging.warning(f"Using placeholder usage check for key: {api_key[:8]}...")
    return random.randint(0, 100) # 0% ~ 100% 사용했다고 가정

def check_api_quota(api_key):
    """가상의 할당량 확인 함수 (실제 구현 아님)"""
    quota_limit = 90 # 90% 사용 시 초과로 간주 (가상)
    try:
        # 실제 사용량 확인 로직 호출 (현재는 가상 함수 사용)
        current_usage_percent = get_current_usage(api_key)
        logging.info(f"Placeholder usage for key {api_key[:8]}...: {current_usage_percent}%")
        if current_usage_percent >= quota_limit:
            logging.warning(f"API Key {api_key[:8]}... placeholder quota nearing limit ({current_usage_percent}%).")
            # 실제 구현 시: 특정 시간 동안 대기하거나 다른 키 시도
            # time.sleep(60) # 예시: 1분 대기
            return False # 현재 키 사용 불가
        return True # 사용 가능
    except Exception as e:
        logging.error(f"Failed to check quota for key {api_key[:8]}...: {e}")
        return False # 오류 발생 시 사용 불가로 간주

def get_openai_api_key():
    """사용 가능한 OpenAI API 키를 순환하며 선택"""
    available_keys = get_available_keys()
    if not available_keys:
        logging.error("No OpenAI API keys found in environment variables (e.g., OPENAI_API_KEY_1).")
        raise ValueError("No OpenAI API keys configured.")

    # 키 목록을 순회하며 (가상의) 할당량 확인 후 첫 번째 사용 가능한 키 반환
    for key in available_keys:
        if check_api_quota(key): # 가상의 확인 로직
            logging.info(f"Selected OpenAI API Key: {key[:8]}...")
            return key

    # 모든 키의 할당량이 초과되었거나 사용할 수 없는 경우 (가상 시나리오)
    logging.error("All available OpenAI API keys seem to be over their quota (placeholder check) or invalid.")
    # 실제 구현: 여기서 대기하거나 예외 발생 결정
    raise Exception("All OpenAI API keys are currently unavailable based on placeholder quota check.")

if __name__ == "__main__":
    # 로컬 테스트용 .env 로드
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    try:
        selected_key = get_openai_api_key()
        print(f"선택된 API 키 (앞 8자리): {selected_key[:8]}...")
    except Exception as e:
        print(f"API 키 선택 중 오류 발생: {e}")
