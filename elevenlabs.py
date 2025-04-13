import requests
import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def text_to_speech(text, filename, model="eleven_multilingual_v2"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        },
        "model_id": model
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"[오디오 생성 완료] {filename}")
        return filename
    else:
        print(f"[오류] ElevenLabs 요청 실패: {response.status_code} - {response.text}")
        raise Exception("ElevenLabs TTS 실패")

