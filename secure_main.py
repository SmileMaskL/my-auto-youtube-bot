from openai_manager import get_available_api_key

def main():
    try:
        # API 키를 가져옵니다.
        api_key = get_available_api_key()
        print(f"사용 가능한 API 키: {api_key}")

        # API 키를 사용하여 필요한 작업을 수행합니다.
        # 예시: OpenAI API 호출 등
        # api_response = some_api_call(api_key)

    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()

