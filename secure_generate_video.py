import os
import logging
import random
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from datetime import datetime

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_generation.log'),
        logging.StreamHandler()
    ]
)

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except IOError:
        try:
            return ImageFont.truetype(DEFAULT_FONT, size)
        except IOError:
            return ImageFont.load_default()

def generate_thumbnail(title, output_folder="static/thumbnails", size=(1280, 720)):
    os.makedirs(output_folder, exist_ok=True)
    
    img = Image.new('RGB', size, color=(random.randint(0, 55), random.randint(0, 55), random.randint(100, 255)))
    draw = ImageDraw.Draw(img)
    
    font = get_font(80)
    text_width = draw.textlength(title, font=font)
    max_width = size[0] * 0.9
    
    if text_width > max_width:
        font_size = int(80 * (max_width / text_width))
        font = get_font(font_size)
    
    text_bbox = draw.textbbox((0,0), title, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2
    
    draw.text((x, y), title, font=font, fill=(255, 255, 255))
    
    filename = f"thumbnail_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    path = os.path.join(output_folder, filename)
    img.save(path, quality=90)
    return path

def generate_video(topic_title, audio_path, output_folder="static/videos"):
    os.makedirs(output_folder, exist_ok=True)
    
    # 1. 썸네일 생성
    thumbnail_path = generate_thumbnail(topic_title)
    
    # 2. 오디오 파일 로드
    audio_clip = AudioFileClip(audio_path)
    
    # 3. 비디오 클립 생성
    video_clip = ImageClip(thumbnail_path, duration=audio_clip.duration)
    video_clip = video_clip.set_audio(audio_clip)
    
    # 4. 비디오 저장
    filename = f"video_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    output_path = os.path.join(output_folder, filename)
    
    video_clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=24,
        threads=4,
        logger=None
    )
    
    return output_path, thumbnail_path, audio_clip.duration

if __name__ == "__main__":
    test_audio = "static/audio/test_audio.mp3"  # 테스트용 오디오 파일 필요
    if os.path.exists(test_audio):
        video_path, thumb_path, duration = generate_video("테스트 제목", test_audio)
        print(f"생성된 영상: {video_path}")
    else:
        print("테스트 오디오 파일이 없습니다.")

