import os
import logging
import openai
from openai_manager import openai_manager
from quota_manager import quota_manager
from typing import Optional, Dict, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/script_generation.log'),
        logging.StreamHandler()
    ]
)

class ScriptGenerator:
    def __init__(self):
        self.max_retries = 3
        self.fallback_models = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-1106-preview']
        self.default_model = 'gpt-3.5-turbo'

    def _get_openai_client(self, api_key: str):
        """OpenAI 클라이언트 생성"""
        return openai.OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=3
        )

    def _estimate_token_usage(self, text: str) -> int:
        """대략적인 토큰 사용량 추정 (간단한 버전)"""
        return len(text) // 4  # 대략적인 추정

    def generate_script(self, trend_data: Dict[str, Any], target_duration: int = 60) -> Optional[str]:
        """트렌드 데이터를 기반으로 스크립트 생성"""
        topic = trend_data.get('topic', '인기 있는 기술 트렌드')
        category = trend_data.get('category', '기술')
        score = trend_data.get('score', 50)
        
        prompt = f"""
        주제: "{topic}" (카테고리: {category}, 인기 점수: {score}/100)

        요청: 위 주제에 대한 흥미로운 한국어 유튜브 쇼츠(Shorts) 스크립트를 작성해주세요.
        - 총 길이: 정확히 {target_duration}초 (약 150-200단어)
        - 대상: 일반 시청자 (전문 용어 최소화)
        - 톤: 친근하고 재미있게
        - 구조:
          1. 훅 (3-5초): 강렬한 시작
          2. 본문 (40-50초): 핵심 내용 2-3가지
          3. 결론 (5-7초): 요약 및 CTA
        - 추가 요구사항:
          - 이모지 적절히 사용 (예: 🔥, 🤖, ��)
          - 문장은 짧고 간결하게
          - 숫자/사례 구체적으로 제시
          #해시태그 포함하지 마세요
        """

        for attempt in range(self.max_retries):
            try:
                api_key = openai_manager.get_valid_key()
                client = self._get_openai_client(api_key)
                model = self._select_model(attempt)

                logging.info(f"시도 {attempt + 1}: '{topic}' 주제로 스크립트 생성 (모델: {model})")

                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "당신은 유튜브 쇼츠 전문 작가입니다. 간결하고 흥미로운 스크립트를 작성하세요."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.9
                )

                script = response.choices[0].message.content.strip()
                token_usage = self._estimate_token_usage(prompt + script)

                # 쿼터 업데이트
                quota_manager.update_usage('openai', token_usage // 1000 + 1, api_key)

                logging.info(f"스크립트 생성 성공! (길이: {len(script)}자, 예상 토큰: ~{token_usage})")
                return script

            except openai.RateLimitError:
                logging.warning(f"시도 {attempt + 1}: API Rate Limit 도달. 키 변경 중...")
                openai_manager.report_key_failure(api_key)
                continue
            except openai.APIError as e:
                logging.error(f"시도 {attempt + 1}: OpenAI API 오류: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                continue
            except Exception as e:
                logging.error(f"시도 {attempt + 1}: 예상치 못한 오류: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                continue

        logging.error("모든 시도 실패. 스크립트 생성 불가")
        return None

    def _select_model(self, attempt: int) -> str:
        """재시도 횟수에 따라 모델 선택"""
        if attempt == 0:
            return self.default_model
        return self.fallback_models[min(attempt, len(self.fallback_models) - 1)]

# 스크립트 생성기 인스턴스
script_generator = ScriptGenerator()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    test_trend = {
        'topic': 'AI의 미래와 일자리',
        'category': '기술',
        'score': 85
    }
    
    try:
        script = script_generator.generate_script(test_trend)
        print("\n=== 생성된 스크립트 ===")
        print(script)
        print("\n=== 스크립트 통계 ===")
        print(f"길이: {len(script)}자")
        print(f"줄 수: {len(script.splitlines())}")
    except Exception as e:
        print(f"스크립트 생성 실패: {e}")
