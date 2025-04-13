# thumbnail.py
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime

def create_thumbnail(content, topic):
    width, height = 1280, 720
    thumbnail = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(thumbnail)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 또는 업로드한 .ttf 경로
    font = ImageFont.truetype(font_path, 48)
    draw.text((50, 300), topic, fill=(255, 255, 255), font=font)

    filename = f"static/video/{topic}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    thumbnail.save(filename)
    return filename

