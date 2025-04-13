from moviepy.editor import VideoFileClip

def make_video(topic, audio_path):
    video_path = f"static/video/{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    image_path = "default.jpg"

    # 영상 파일 생성 및 길이 조정 (60초 이하로 자르기)
    video = VideoFileClip(image_path, audio=audio_path).subclip(0, 60)
    video.write_videofile(video_path, codec="libx264")
    
    return video_path

