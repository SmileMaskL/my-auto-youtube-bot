import os
import requests
import logging
from datetime import datetime
from elevenlabs import ElevenLabs # 최신 SDK 사용 (설치 필요: pip install elevenlabs)

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ElevenLabs 클라이언트 초기화 (API 키는 환경 변수에서 자동 로드 시도)
# 또는 명시적으로 client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
try:
    client = ElevenLabs()
    # API 키가 제대로 로드되었는지 확인 (예: 간단한 API 호출)
    client.models.get_all()
    logging.info("ElevenLabs client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize ElevenLabs client. Check API key. Error: {e}")
    client = None # 초기화 실패 시 None으로 설정

def text_to_audio(text, voice_id, output_folder="generated_audio"):
    """텍스트를 오디오로 변환하고 파일로 저장 (최신 elevenlabs SDK 사용)"""
    if not client:
        raise ConnectionError("ElevenLabs client is not initialized. Check API key and initialization.")

    if not text:
        logging.error("Input text for audio generation is empty.")
        raise ValueError("Input text cannot be empty.")
    if not voice_id:
        logging.error("ElevenLabs Voice ID is not provided.")
        raise ValueError("Voice ID must be provided.")

    try:
        logging.info(f"Requesting audio generation for voice ID: {voice_id}")

        # 오디오 생성 요청
        audio_stream = client.generate(
            text=text,
            voice=voice_id,
            model="eleven_multilingual_v2" # 또는 다른 적합한 모델
            # stability, similarity_boost 등 추가 설정 가능
            # voice_settings=VoiceSettings(stability=0.7, similarity_boost=0.8)
        )

        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logging.info(f"Created output folder: {output_folder}")

        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 파일명에 voice_id 포함하여 구분 용이하게 (옵션)
        safe_voice_id = "".join(c if c.isalnum() else "_" for c in voice_id) # 파일명에 안전한 문자만 사용
        audio_filename = f"audio_{safe_voice_id}_{timestamp}.mp3"
        audio_path = os.path.join(output_folder, audio_filename)

        with open(audio_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        logging.info(f"Audio file successfully saved to: {audio_path}")
        return audio_path

    except requests.exceptions.RequestException as e:
        # 네트워크 관련 오류
        logging.error(f"Network error during ElevenLabs API request: {e}")
        raise ConnectionError(f"Network error communicating with ElevenLabs: {e}")
    except Exception as e:
        # ElevenLabs API 에러 또는 기타 예외
        logging.error(f"Failed to generate audio using ElevenLabs: {str(e)}")
        # API 응답에서 상세 에러 메시지 추출 시도 (라이브러리 구조에 따라 다름)
        # if hasattr(e, 'response') and e.response is not None:
        #     logging.error(f"API Response Status: {e.response.status_code}")
        #     try:
        #         logging.error(f"API Response Body: {e.response.json()}")
        #     except:
        #         logging.error(f"API Response Body: {e.response.text}")
        raise # 원래 예외를 다시 발생시켜 상위에서 처리

if __name__ == "__main__":
    # 로컬 테스트용 .env 로드
    from dotenv import load_dotenv
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    test_text = "이것은 한국어 음성 생성 테스트입니다. ElevenLabs API가 최신 SDK와 함께 잘 작동하는지 확인합니다."
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
