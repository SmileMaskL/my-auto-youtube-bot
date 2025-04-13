import openai
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 로그 설정
logging.basicConfig(filename='script_generation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_openai_client():
    """OpenAI 클라이언트 생성 및 API 키 설정"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    return openai.OpenAI(api_key=api_key)

def generate_script(trend_data):
    """트렌드 데이터를 기반으로 스크립트 생성"""
    try:
        client = get_openai_client()
        
        prompt = f"""
        Create an engaging YouTube video script about the trending topic: {trend_data}.
        The script should be in Korean and structured as follows:
        
        1. Introduction (10-15 seconds)
        2. Main content (45-60 seconds)
        3. Conclusion (10-15 seconds)
        
        Make it informative, entertaining, and suitable for a general audience.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional YouTube script writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        script = response.choices[0].message.content.strip()
        logging.info(f"Script generated successfully for topic: {trend_data}")
        return script
        
    except Exception as e:
        logging.error(f"Failed to generate script: {str(e)}")
        raise

if __name__ == "__main__":
    test_trend = "인공지능 기술의 최신 동향"
    print(generate_script(test_trend))
