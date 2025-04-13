from moviepy.editor import *
import os

def make_video(title, audio_path):
    # 영상 정보
    output_path = f"static/video/{title}.mp4"
    background = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=10)

    # 텍스트 오버레이 (이미지로 변환) - PIL로 수정
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1280, 720), color='black')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((640, 360), title, font=font, fill="white")
    img.save("temp_image.png")

    txt_clip = ImageClip("temp_image.png").set_duration(10).set_position('center')

    # 오디오
    audio = AudioFileClip(audio_path)

    # 영상 합성
    final_video = CompositeVideoClip([background, txt_clip]).set_audio(audio)
    final_video.duration = audio.duration
    final_video.write_videofile(output_path, fps=24, codec='libx264')
    os.remove("temp_image.png")  # 임시 이미지 삭제
    return output_path

