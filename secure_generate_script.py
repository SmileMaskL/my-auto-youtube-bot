import openai
import os
import logging
from openai_rotate import get_openai_api_key

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_openai_client():
    """OpenAI 클라이언트 생성 및 API 키 설정 (로테이션 사용)"""
    try:
        api_key = get_openai_api_key()
        if not api_key:
            raise ValueError("Failed to get a valid OpenAI API key from rotation.")
        # 비용 절감을 위해 타임아웃 설정 (옵션)
        return openai.OpenAI(api_key=api_key, timeout=60.0) # 60초 타임아웃
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        raise

def generate_script(trend_data, target_duration_seconds=60):
    """트렌드 데이터를 기반으로 스크립트 생성 (비용 절감 모델 사용)"""
    logging.info(f"Generating script for topic: {trend_data} using cost-effective model.")
    logging.warning("Using gpt-3.5-turbo for cost saving. Quality may be lower than GPT-4.")
    # 예상 비용에 대한 경고 추가 (실제 비용은 토큰 사용량에 따라 다름)
    logging.warning("OpenAI API calls incur costs. Monitor your usage and billing.")

    try:
        client = get_openai_client()

        # 스크립트 길이 및 토큰 사용량 줄이기 (약 60초 목표)
        # max_tokens는 응답 길이 제한, 실제 스크립트 길이는 프롬프트와 모델에 따라 달라짐
        # 60초 스크립트는 대략 150-200단어, 토큰 수로는 더 많음 (한글 기준)
        # 보수적으로 800 토큰 정도로 제한 시도
        estimated_max_tokens = 800

        prompt = f"""
        주제: "{trend_data}"

        요청: 위 주제에 대한 흥미로운 유튜브 쇼츠(Shorts) 영상 스크립트를 한국어로 작성해 주세요. 총 길이는 반드시 **{target_duration_seconds}초 미만**이 되도록 해주세요 (약 150단어 내외).

        스크립트 구조 (간결하게):
        1.  **훅 (Hook, 3-5초):** 시청자의 시선을 즉시 사로잡는 문구 또는 질문.
        2.  **본론 (40-50초):** 주제의 핵심 내용 1~2가지를 간결하고 빠르게 전달.
        3.  **결론/CTA (Call to Action, 5초):** 요약 및 구독/좋아요 요청.

        스타일:
        - 짧고 간결하며, 핵심만 전달.
        - 쉽고 재미있는 단어 사용.
        - 각 파트 구분 없이 자연스럽게 이어지는 나레이션 형식.

        스크립트만 제공해주세요. 다른 설명은 필요 없습니다.
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # 비용 효율적인 모델 사용
            messages=[
                {"role": "system", "content": "You are a YouTube script writer specialized in creating concise and engaging short-form video scripts (under 60 seconds) in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=estimated_max_tokens # 응답 최대 길이 제한 (비용 관리)
        )

        script = response.choices[0].message.content.strip()
        logging.info(f"Script generated successfully for topic: {trend_data}")
        # 실제 생성된 스크립트 길이 확인 (토큰 사용량과 다름)
        logging.info(f"Generated script length: {len(script)} characters")
        # ElevenLabs 무료 한도 고려: 생성된 글자 수 확인
        if len(script) > 2500: # ElevenLabs 무료 티어의 월간 한도를 고려한 임의의 경고 기준
            logging.warning(f"Generated script is long ({len(script)} chars). This will consume significant ElevenLabs quota.")

        return script

    except openai.RateLimitError as e:
        logging.error(f"OpenAI API rate limit exceeded: {e}")
        raise
    except openai.APIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise
    except Exception as e:
        logging.error(f"Failed to generate script: {str(e)}")
        raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_trend = "인공지능의 미래"
    try:
        generated_script = generate_script(test_trend)
        print("--- 생성된 스크립트 (gpt-3.5-turbo) ---")
        print(generated_script)
        print("------------------------------------")
    except Exception as e:
        print(f"스크립트 생성 테스트 중 오류: {e}")
