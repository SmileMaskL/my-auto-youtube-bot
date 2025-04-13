# elevenlabs.py
import requests
import os
from datetime import datetime

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")

def text_to_speech(text, voice, model="eleven_multilingual_v2"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        file_path = f"static/audio/voice_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(response.content)
        return file_path
    else:
        raise Exception(f"ElevenLabs API 오류: {response.status_code} - {response.text}")

