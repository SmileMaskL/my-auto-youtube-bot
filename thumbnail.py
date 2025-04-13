from PIL import Image, ImageDraw, ImageFont
import os

def create_thumbnail(text, topic):
    # 기본 이미지 크기 설정
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 폰트 설정 (시스템에 따라 경로를 맞춰야 할 수 있음)
    font = ImageFont.load_default()
    
    # 텍스트 추가 (중앙 정렬)
    text_width, text_height = draw.textsize(text, font=font)
    text_position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(text_position, text, font=font, fill="black")
    
    # 썸네일 파일 저장
    thumbnail_path = f"static/thumbnails/{topic}_thumbnail.jpg"
    image.save(thumbnail_path)
    return thumbnail_path

