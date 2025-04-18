import os
import logging
import hashlib
import time
import json
from typing import Optional
from quota_manager import quota_manager
from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/audio_generation.log'),
        logging.StreamHandler()
    ]
)

class AudioGenerator:
    def __init__(self):
        self.voice_id = os.getenv('ELEVENLABS_VOICE_ID')
        self.api_key = os.getenv('ELEVENLABS_KEY')
        self.max_retries = 3
        self.timeout = 300
        self._validate_voice_id()

    def _validate_voice_id(self):
        """Voice ID 검증"""
        if not self.voice_id:
            logging.error("ELEVENLABS_VOICE_ID 환경 변수가 설정되지 않았습니다.")
            raise ValueError("ELEVENLABS_VOICE_ID is required")

        if not self.api_key:
            logging.error("ELEVENLABS_KEY 환경 변수가 설정되지 않았습니다.")
            raise ValueError("ELEVENLABS_KEY is required")

    def _get_audio_filename(self, text: str) -> str:
        """텍스트 해시를 기반으로 오디오 파일명 생성"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"audio_{text_hash}.mp3"

    def text_to_speech(self, text: str, output_dir: str = "static/audio") -> Optional[str]:
        """텍스트를 음성으로 변환하여 파일로 저장"""
        if not text or len(text.strip()) < 10:
            logging.error("텍스트가 너무 짧아 오디오 생성 불가")
            return None

        os.makedirs(output_dir, exist_ok=True)
        filename = self._get_audio_filename(text)
        output_path = os.path.join(output_dir, filename)

        # 이미 존재하는 파일 체크
        if os.path.exists(output_path):
            logging.info(f"기존 오디오 파일 재사용: {output_path}")
            return output_path

        # 쿼터 체크
        if not quota_manager.check_quota('elevenlabs'):
            logging.error("ElevenLabs 일일 쿼터 초과")
            return None

        for attempt in range(self.max_retries):
            try:
                logging.info(f"시도 {attempt + 1}: 오디오 생성 (길이: {len(text)}자)")

                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key
                }

                data = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.7,
                        "similarity_boost": 0.8
                    }
                }

                response = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}",
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                with open(output_path, 'wb') as f:
                    f.write(response.content)

                # 쿼터 업데이트 (문자 단위)
                quota_manager.update_usage('elevenlabs', len(text))

                logging.info(f"오디오 파일 저장 완료: {output_path}")
                return output_path

            except Exception as e:
                logging.error(f"시도 {attempt + 1} 실패: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))

        return None

# 오디오 생성기 인스턴스
audio_generator = AudioGenerator()

if __name__ == "__main__":
    test_text = "이것은 ElevenLabs API를 사용한 음성 생성 테스트입니다. 이 오디오가 정상적으로 생성되고 저장되면 성공입니다."
    
    try:
        audio_path = audio_generator.text_to_speech(test_text)
        if audio_path:
            print(f"오디오 생성 성공! 파일 위치: {audio_path}")
        else:
            print("오디오 생성 실패")
    except Exception as e:
        print(f"오디오 생성 중 오류 발생: {e}")
