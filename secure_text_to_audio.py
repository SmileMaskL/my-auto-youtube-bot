import os
import requests
import logging
from datetime import datetime
from elevenlabs import ElevenLabs, SaveMode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ElevenLabs 클라이언트 초기화
try:
    # API 키는 환경 변수 ELEVEN_API_KEY 또는 ELEVENLABS_API_KEY 에서 자동 로드 시도
    client = ElevenLabs()
    # 간단한 API 호출로 키 유효성 및 연결 확인
    client.models.get_all()
    logging.info("ElevenLabs client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize ElevenLabs client. Check API key (ELEVEN_API_KEY/ELEVENLABS_API_KEY). Error: {e}")
    client = None

# ElevenLabs 무료 티어의 대략적인 월간 한도 (정확한 값은 공식 문서 확인 필요)
ELEVENLABS_FREE_TIER_CHARS = 10000

def text_to_audio(text, voice_id, output_folder="generated_audio"):
    """텍스트를 오디오로 변환 (비용 및 무료 한도 경고 포함)"""
    if not client:
        raise ConnectionError("ElevenLabs client is not initialized. Check API key and initialization.")

    if not text:
        logging.error("Input text for audio generation is empty.")
        raise ValueError("Input text cannot be empty.")
    if not voice_id:
        logging.error("ElevenLabs Voice ID is not provided.")
        raise ValueError("Voice ID must be provided.")

    text_length = len(text)
    logging.info(f"Requesting audio generation for {text_length} characters.")
    logging.warning("ElevenLabs API calls consume character quota and may incur costs if free tier limit is exceeded.")
    # 현재 실행에서 사용량 추적은 어려우므로, 대략적인 경고만 제공
    if text_length > ELEVENLABS_FREE_TIER_CHARS * 0.1: # 한 번에 무료 한도의 10% 이상 사용 시 경고
         logging.warning(f"Requested text length ({text_length}) is significant compared to the estimated monthly free tier limit ({ELEVENLABS_FREE_TIER_CHARS}). Monitor your usage.")

    try:
        # 오디오 생성 요청
        # stream=True 대신 save 사용 (elevenlabs v1.0.0 이상)
        audio_data = client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2" # 또는 eleven_mono_v1 등
        )

        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logging.info(f"Created output folder: {output_folder}")

        # 파일 저장 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_voice_id = "".join(c if c.isalnum() else "_" for c in voice_id)
        audio_filename = f"audio_{safe_voice_id}_{timestamp}.mp3"
        audio_path = os.path.join(output_folder, audio_filename)

        # 파일 저장 (elevenlabs v1.0.0)
        with open(audio_path, "wb") as f:
            f.write(audio_data)

        # SaveMode.SAVE 사용 시 (다른 방식)
        # client.save(audio=audio_data, filename=audio_path, save_mode=SaveMode.OVERWRITE)

        logging.info(f"Audio file successfully saved to: {audio_path}")
        return audio_path

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error during ElevenLabs API request: {e}")
        raise ConnectionError(f"Network error communicating with ElevenLabs: {e}")
    except Exception as e:
        # API 에러 (예: 할당량 초과, 잘못된 키 등)
        logging.error(f"Failed to generate audio using ElevenLabs: {str(e)}")
        # 에러 응답 내용 로깅 시도 (API 구조에 따라 다를 수 있음)
        if hasattr(e, 'response') and e.response is not None:
             logging.error(f"API Response Status: {e.response.status_code}")
             try:
                 logging.error(f"API Response Body: {e.response.json()}")
             except:
                 logging.error(f"API Response Body: {e.response.text}")
        # 할당량 초과 관련 에러 메시지 확인 및 로깅 (예시)
        if "quota" in str(e).lower() or "limit" in str(e).lower():
             logging.error("Potential quota exceeded error detected.")
        raise

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    test_text = "비용 효율적인 자동화를 위한 짧은 음성 테스트입니다. 무료 한도를 잘 관리해야 합니다."
    test_voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not test_voice_id:
        print("오류: .env 파일에 ELEVENLABS_VOICE_ID를 설정해주세요.")
    elif not client:
         print("오류: ElevenLabs 클라이언트 초기화 실패. API 키를 확인하세요.")
    else:
        try:
            output_path = text_to_audio(test_text, test_voice_id)
            print(f"테스트 오디오 생성 완료: {output_path}")
        except Exception as e:
            print(f"테스트 오디오 생성 중 오류 발생: {e}")
