from datetime import datetime
import subprocess
import os

def clean_folder(folder="static/video"):
    if not os.path.exists(folder):
        os.makedirs(folder)
    else:
        for file in os.listdir(folder):
            os.remove(os.path.join(folder, file))

def create_video(topic, audio_path, thumbnail_path):
    video_filename = f"{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    video_path = f"static/video/{video_filename}"

    command = [
        "ffmpeg", "-loop", "1",
        "-i", thumbnail_path,
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

