import requests
import os

def text_to_speech(text, output_path="output.mp3"):
    key = os.getenv("ELEVENLABS_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
    }
    response = requests.post(url, headers=headers, json=data)
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path

