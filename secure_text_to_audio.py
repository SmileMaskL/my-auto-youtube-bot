import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ElevenLabs 무료 티어의 대략적인 월간 한도 (참고용)
ELEVENLABS_FREE_TIER_CHARS = 10000

# *** 함수명을 text_to_speech 로 변경 ***
def text_to_speech(text, voice_id, output_folder="generated_audio", stability=0.7, similarity_boost=0.8):
    """텍스트를 오디오로 변환하고 파일로 저장 (requests 사용, elevenlabs==0.2.x 호환)"""

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logging.error("ElevenLabs API key not found in environment variables (ELEVENLABS_API_KEY).")
        raise ValueError("Missing ElevenLabs API Key")

    if not text:
        logging.error("Input text for audio generation is empty.")
        raise ValueError("Input text cannot be empty.")
    if not voice_id:
        logging.error("ElevenLabs Voice ID is not provided.")
        raise ValueError("Voice ID must be provided.")

    text_length = len(text)
    logging.info(f"Requesting audio generation for {text_length} characters.")
    logging.warning("ElevenLabs API calls consume character quota and may incur costs if free tier limit is exceeded.")
    if text_length > ELEVENLABS_FREE_TIER_CHARS * 0.1:
         logging.warning(f"Requested text length ({text_length}) is significant compared to the estimated monthly free tier ({ELEVENLABS_FREE_TIER_CHARS}). Monitor your usage.")

    # ElevenLabs API 엔드포인트 (v1)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2", # 또는 다른 모델 ID
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            # "style": 0.2, # 필요시 추가
            # "use_speaker_boost": True # 필요시 추가
        }
    }

    try:
        logging.info(f"Sending request to ElevenLabs API for voice ID: {voice_id}")
        response = requests.post(url, json=data, headers=headers, timeout=180) # 타임아웃 3분 설정
        response.raise_for_status() # 오류 발생 시 예외 발생 (4xx, 5xx)

        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logging.info(f"Created output folder: {output_folder}")

        # 파일 저장 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_voice_id = "".join(c if c.isalnum() else "_" for c in voice_id)
        audio_filename = f"audio_{safe_voice_id}_{timestamp}.mp3"
        audio_path = os.path.join(output_folder, audio_filename)

        # 오디오 파일 저장
        with open(audio_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        logging.info(f"Audio file successfully saved to: {audio_path}")
        return audio_path

    except requests.exceptions.RequestException as e:
        logging.error(f"Network or request error during ElevenLabs API call: {e}")
        # 응답 내용 로깅 시도
        if e.response is not None:
            logging.error(f"Response status code: {e.response.status_code}")
            logging.error(f"Response text: {e.response.text}")
        # 할당량 초과 또는 인증 오류 확인
        if e.response is not None and e.response.status_code in [401, 402]:
             logging.error("Authentication error or quota exceeded likely for ElevenLabs.")
             # 재시도 의미 없음
             raise ConnectionAbortedError("ElevenLabs authentication/quota error.") from e
        raise ConnectionError(f"Failed to get audio from ElevenLabs: {e}") from e
    except Exception as e:
        logging.error(f"Unexpected error during audio generation: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    test_text = "이것은 elevenlabs 0.2.12 버전 호환성 테스트입니다. requests 라이브러리를 사용합니다."
    test_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not test_voice_id:
        print("오류: .env 파일에 ELEVENLABS_VOICE_ID를 설정해주세요.")
    else:
        try:
            # 함수명 변경됨: text_to_speech
            output_path = text_to_speech(test_text, test_voice_id)
            print(f"테스트 오디오 생성 완료: {output_path}")
        except Exception as e:
            print(f"테스트 오디오 생성 중 오류 발생: {e}")
