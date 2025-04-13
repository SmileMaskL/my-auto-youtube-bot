# elevenlabs.py
import requests
import os

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
        return response.content
    else:
        print(f"[음성 생성 실패] 상태코드: {response.status_code}")
        print(response.text)
        raise Exception("음성 생성 실패")

def save(audio_data, output_path):
    with open(output_path, "wb") as f:
        f.write(audio_data)

