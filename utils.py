# utils.py

def create_video(audio_path, topic, thumbnail_path):
    video_path = f"static/video/{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"

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

