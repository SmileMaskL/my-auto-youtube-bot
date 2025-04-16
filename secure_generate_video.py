import os
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/"
API_KEY = os.getenv("ELEVENLABS_API_KEY")

def text_to_speech(text, voice_id, output_folder="audio_output"):
    if not API_KEY:
        raise ValueError("API key is missing!")

    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "voice_id": voice_id
    }

    response = requests.post(f"{API_URL}{voice_id}", headers=headers, json=data)
    if response.status_code == 200:
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3")
        with open(output_path, "wb") as f:
            f.write(response.content)
        logging.info(f"Audio saved to {output_path}")
        return output_path
    else:
        logging.error(f"Failed to generate audio: {response.status_code}, {response.text}")
        raise RuntimeError("Audio generation failed.")

if __name__ == "__main__":
    text = "Hello, this is a test."
    voice_id = "your_voice_id_here"
    text_to_speech(text, voice_id)
