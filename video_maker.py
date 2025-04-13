from moviepy.editor import *
import os

def make_video(title, audio_path):
    # 영상 정보
    output_path = f"static/video/{title}.mp4"
    background = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=10)

    # 텍스트 오버레이 (이미지로 변환)
    txt_clip = TextClip(title, fontsize=70, color='white', size=(1280, 720), method='caption')
    txt_clip = txt_clip.set_duration(10).set_position('center')

    # 오디오
    audio = AudioFileClip(audio_path)

    # 영상 합성
    final_video = CompositeVideoClip([background, txt_clip]).set_audio(audio)
    final_video.duration = audio.duration
    final_video.write_videofile(output_path, fps=24, codec='libx264')
    return output_path

