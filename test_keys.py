from dotenv import load_dotenv  # 추가된 부분
import os
from openai import OpenAI

# .env 파일 로드 (필수!)
load_dotenv()

def test_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return True
    except Exception as e:
        print(f"❌ 실패: {str(e)}")
        return False

# 모든 OpenAI 키 불러오기
keys = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]

# 각 키 테스트
for idx, key in enumerate(keys):
    print(f"🔑 키 {idx+1} 테스트 중...")
    if test_key(key):
        print("✅ 유효한 키입니다!")
    else:
        print("🚨 유효하지 않은 키!")
