import openai
import os
import logging
from openai_rotate import get_openai_api_key # 키 로테이션 함수 임포트

# 로그 설정 (main 스크립트에서 설정하므로 여기서는 기본 설정)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_openai_client():
    """OpenAI 클라이언트 생성 및 API 키 설정 (로테이션 사용)"""
    try:
        api_key = get_openai_api_key() # 로테이션 함수를 통해 키 가져오기
        if not api_key:
            # get_openai_api_key 내부에서 이미 예외 처리가 되어 있어야 함
            raise ValueError("Failed to get a valid OpenAI API key from rotation.")
        return openai.OpenAI(api_key=api_key)
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        raise

def generate_script(trend_data, target_duration_seconds=60):
    """트렌드 데이터를 기반으로 스크립트 생성"""
    logging.info(f"Generating script for topic: {trend_data}")
    try:
        client = get_openai_client()

        prompt = f"""
        주제: "{trend_data}"

        요청: 위 주제에 대한 흥미로운 유튜브 영상(Shorts 또는 일반 영상) 스크립트를 한국어로 작성해 주세요. 총 길이는 약 {target_duration_seconds}초가 되도록 해주세요.

        스크립트 구조:
        1.  **인트로 (약 5-10초):** 시청자의 흥미를 유발하고 주제를 명확히 제시하세요.
        2.  **본론 (약 {target_duration_seconds - 20}초):** 주제에 대한 핵심 정보, 흥미로운 사실, 또는 이야기를 2~3개의 소주제로 나누어 전달하세요. 쉽고 간결하게 설명해주세요.
        3.  **결론 (약 5-10초):** 내용을 요약하고, 시청자에게 구독, 좋아요 등 행동을 유도하는 메시지를 포함하세요.

        스타일:
        - 정보적이면서도 재미있게 작성해주세요.
        - 쉽고 명확한 단어를 사용해주세요.
        - 너무 길거나 복잡한 문장은 피해주세요.
        - 각 파트(인트로, 본론1, 본론2, ..., 결론)를 명확히 구분하여 작성해주세요. (예: "[인트로]", "[본론1]", "[결론]")

        스크립트만 제공해주세요. 다른 설명은 필요 없습니다.
        """

        response = client.chat.completions.create(
            model="gpt-4o", # 또는 gpt-4, gpt-3.5-turbo 등 사용 가능한 모델
            messages=[
                {"role": "system", "content": "You are a professional YouTube script writer specialized in creating engaging short-form and standard video scripts in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500 # 스크립트 길이에 맞춰 조정
        )

        script = response.choices[0].message.content.strip()
        logging.info(f"Script generated successfully for topic: {trend_data}")
        # 생성된 스크립트 길이 로깅 (옵션)
        # logging.info(f"Generated script length: {len(script)} characters")
        return script

    except openai.RateLimitError as e:
        logging.error(f"OpenAI API rate limit exceeded: {e}")
        # 여기서 재시도 로직 또는 다른 키 사용 로직 추가 가능
        raise # 에러를 다시 발생시켜 main 루프에서 처리하도록 함
    except Exception as e:
        logging.error(f"Failed to generate script: {str(e)}")
        raise

if __name__ == "__main__":
    # 로컬 테스트용 .env 로드
    from dotenv import load_dotenv
    load_dotenv()
    test_trend = "인공지능 기술의 최신 동향"
    try:
        generated_script = generate_script(test_trend)
        print("--- 생성된 스크립트 ---")
        print(generated_script)
        print("----------------------")
    except Exception as e:
        print(f"스크립트 생성 테스트 중 오류: {e}")
