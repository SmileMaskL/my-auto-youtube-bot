import os
import logging
from elevenlabs import generate, set_api_key
from quota_manager import quota_manager

def text_to_speech(text: str, output_dir="static/audio"):
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # API 키 체크
        if not quota_manager.check_quota('elevenlabs'):
            raise Exception("ElevenLabs API quota exceeded")
        
        # 음성 생성
        set_api_key(os.getenv('ELEVENLABS_KEY'))
        audio = generate(
            text=text,
            voice=os.getenv('ELEVENLABS_VOICE_ID'),
            model="eleven_multilingual_v2"
        )
        
        # 파일 저장
        filename = f"audio_{hash(text)}.mp3"
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'wb') as f:
            f.write(audio)
        
        # 쿼터 업데이트
        quota_manager.update_usage('elevenlabs')
        
        return output_path
        
    except Exception as e:
        logging.error(f"Audio generation failed: {str(e)}")
        raise

