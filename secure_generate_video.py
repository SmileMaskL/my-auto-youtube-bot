import os
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import logging
from datetime import datetime

# 로그 설정
logging.basicConfig(filename='video_generation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def generate_thumbnail(title, output_folder="generated_thumbnails"):
    """동영상 썸네일 생성"""
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 이미지 크기 설정 (YouTube 썸네일 표준 크기)
        width, height = 1280, 720
        
        # 배경 이미지 생성 (간단한 그라데이션)
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        
        # 그라데이션 배경
        for y in range(height):
            r, g, b = 30 + int(120 * y/height), 50 + int(100 * y/height), 80 + int(100 * y/height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # 폰트 설정 (기본 폰트 대신 DejaVu Sans 사용)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
        except:
            # 기본 폰트 사용
            font = ImageFont.load_default()
            font.size = 60
        
        # 텍스트 추가
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        
        # 텍스트 위치 계산
        text_width = font.getlength(title)
        text_height = 60  # 폰트 크기와 동일
        
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        # 그림자 효과
        draw.text((x-2, y-2), title, font=font, fill=shadow_color)
        draw.text((x+2, y-2), title, font=font, fill=shadow_color)
        draw.text((x-2, y+2), title, font=font, fill=shadow_color)
        draw.text((x+2, y+2), title, font=font, fill=shadow_color)
        
        # 메인 텍스트
        draw.text((x, y), title, font=font, fill=text_color)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thumbnail_path = os.path.join(output_folder, f"thumbnail_{timestamp}.jpg")
        image.save(thumbnail_path)
        
        logging.info(f"Thumbnail generated: {thumbnail_path}")
        return thumbnail_path
        
    except Exception as e:
        logging.error(f"Failed to generate thumbnail: {str(e)}")
        raise

def generate_video(trend_data, audio_path, output_folder="generated_videos"):
    """오디오와 썸네일을 결합하여 동영상 생성"""
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 1. 썸네일 생성
        thumbnail_path = generate_thumbnail(f"최신 트렌드: {trend_data}")
        
        # 2. 오디오 파일 로드
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        
        # 3. 비디오 클립 생성 (썸네일 이미지를 오디오 길이만큼 확장)
        video_clip = ImageClip(thumbnail_path, duration=audio_duration)
        video_clip = video_clip.set_audio(audio_clip)
        
        # 4. 비디오 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(output_folder, f"video_{timestamp}.mp4")
        
        # 비디오 코덱 설정 (YouTube 권장 설정)
        video_clip.write_videofile(
            video_path,
            codec="libx264",
            audio_codec="aac",
            fps=24,
            threads=4,
            preset="fast",
            bitrate="5000k"
        )
        
        logging.info(f"Video generated: {video_path}")
        return video_path, thumbnail_path
        
    except Exception as e:
        logging.error(f"Failed to generate video: {str(e)}")
        raise

if __name__ == "__main__":
    test_trend = "테스트 트렌드"
    test_audio = "test_audio.mp3"
    generate_video(test_trend, test_audio)
