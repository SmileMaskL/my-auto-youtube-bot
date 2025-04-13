# secure_generate_video.py

from secure_generate_script import generate_script
from secure_text_to_audio import text_to_audio
from PIL import Image, ImageDraw, ImageFont

def generate_video(trend_data, voice_id):
    # 스크립트 생성
    script = generate_script(trend_data)
    
    # 텍스트를 오디오로 변환
    text_to_audio(script, voice_id)
    
    # 썸네일 생성
    generate_thumbnail(f"Video about {trend_data}")
    
    print(f"Generated video for {trend_data}")

def generate_thumbnail(title):
    # 기본 이미지 크기 설정
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    
    # 텍스트를 이미지에 추가
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()  # 기본 폰트 사용
    text = title
    text_width, text_height = draw.textsize(text, font=font)
    draw.text(((width - text_width) / 2, (height - text_height) / 2), text, font=font, fill=(0, 0, 0))
    
    # 썸네일 파일 저장
    image.save("generated_thumbnail.jpg")

# main.py에서 호출될 수 있도록 함수 반환
if __name__ == "__main__":
    generate_video("Sample trend", "VoiceID")

