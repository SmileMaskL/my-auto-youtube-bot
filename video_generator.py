import subprocess

def generate_video():
    input_audio = "output/final.mp3"
    input_image = "output/background.png"
    output_video = "output/final.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", input_image,
        "-i", input_audio,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_video
    ]

    subprocess.run(cmd, check=True)
    print("🎬 영상 생성 완료:", output_video)
    return output_video

def convert_to_shorts_format(input_path: str, output_path: str):
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", "crop=in_h*9/16:in_h,scale=720:1280",
        "-t", "60",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-strict", "experimental",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print("🎬 Shorts 포맷 변환 완료:", output_path)

