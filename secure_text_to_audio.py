import os
from dotenv import load_dotenv
import requests
import logging
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 로그 설정
logging.basicConfig(filename='audio_generation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def text_to_audio(text, voice_id):
    """텍스트를 오디오로 변환하고 파일로 저장"""
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key not found in environment variables")
        
        if not voice_id:
            raise ValueError("Voice ID not provided")
        
        # 오디오 파일 경로 설정
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = f"generated_audio_{timestamp}.mp3"
        
        # ElevenLabs API 요청
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "voice_settings": {
                "stability": 0.7,
                "similarity_boost": 0.8,
                "style": 0.2,
                "speaker_boost": True
            },
            "model_id": "eleven_multilingual_v2"
        }
        
        response = requests.post(url, headers=headers, json=data, stream=True)
        
        if response.status_code == 200:
            with open(audio_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            logging.info(f"Audio file saved to: {audio_path}")
            return audio_path
        else:
            error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        logging.error(f"Failed to generate audio: {str(e)}")
        raise

if __name__ == "__main__":
    test_text = "이것은 테스트 오디오 생성입니다. ElevenLabs API가 잘 작동하는지 확인합니다."
    test_voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    text_to_audio(test_text, test_voice_id)
