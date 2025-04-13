# video_maker.py

import os
import subprocess
from datetime import datetime

def make_video(topic, audio_path):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    video_filename = f"{topic}_{timestamp}.mp4"
    video_path = os.path.join("static", "video", video_filename)
    image_path = "default.jpg"

    # 배경 이미지가 없으면 생성
    if not os.path.exists(image_path):
        subprocess.run([
            "convert",  # ImageMagick 필요
            "-size", "1280x720",
            "xc:gray",
            "-gravity", "center",
            "-pointsize", "48",
            "-annotate", "0", topic,
            image_path
        ], check=True)

    # ffmpeg를 사용하여 영상 생성
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

