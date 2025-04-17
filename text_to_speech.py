import openai
import os

def generate_speech(text, api_key):
    openai.api_key = api_key
    response = openai.Audio.speech.create(
        model="tts-1",
        voice="nova",
        input=text
    )
    audio_path = "output/audio.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path

