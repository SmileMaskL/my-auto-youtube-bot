import os
import subprocess
from elevenlabs import generate, save
from datetime import datetime

def text_to_speech(text, topic):
    audio = generate(
        text=text,
        voice=os.getenv("ELEVENLABS_VOICE_ID"),
        api_key=os.getenv("ELEVENLABS_KEY")
    )
    filename = f"static/audio/{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
    save(audio, filename)
    return filename

def create_video(audio_path, topic):
    video_path = f"static/video/{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    image_path = "default.jpg"

    if not os.path.exists(image_path):
        # 임시 배경 이미지 생성
        subprocess.run([
            "convert",  # imagemagick 필요
            "-size", "1280x720",
            "xc:gray",
            "-gravity", "center",
            "-pointsize", "48",
            "-annotate", "0", topic,
            image_path
        ])

    command = [
        "ffmpeg", "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-y", video_path
    ]

    subprocess.run(command, check=True)
    return video_path

def clean_folder():
    for folder in ["static/audio", "static/video"]:
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

