import os
import logging
import random
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.all import resize
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/video_generation.log'),
        logging.StreamHandler()
    ]
)

class VideoGenerator:
    def __init__(self):
        self.video_width = 1080
        self.video_height = 1920  # Shorts 기본 해상도
        self.font_path = self._find_font()
        self.default_font_size = 80
        self.max_text_width = self.video_width * 0.9
        self.background_colors = [
            (30, 40, 180), (80, 20, 120), (10, 100, 150),
            (40, 60, 200), (20, 80, 160), (60, 30, 140)
        ]

    def _find_font(self) -> Optional[str]:
        """시스템에서 사용 가능한 폰트 찾기"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "arial.ttf"
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        return None

    def _get_font(self, size: int):
        """폰트 객체 생성"""
        try:
            if self.font_path:
                return ImageFont.truetype(self.font_path, size)
            return ImageFont.load_default(size)
        except IOError:
            return ImageFont.load_default()

    def _adjust_font_size(self, text: str, draw: ImageDraw, initial_size: int) -> ImageFont:
        """텍스트 길이에 따라 폰트 크기 조정"""
        font_size = initial_size
        font = self._get_font(font_size)
        
        while True:
            text_width = draw.textlength(text, font=font)
            if text_width <= self.max_text_width or font_size <= 20:
                break
            font_size -= 5
            font = self._get_font(font_size)
        
        return font

    def generate_thumbnail(self, title: str, output_dir: str = "static/thumbnails") -> str:
        """동영상 썸네일 생성"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 배경색 랜덤 선택
        bg_color = random.choice(self.background_colors)
        
        # 이미지 생성
        img = Image.new('RGB', (self.video_width, self.video_height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 폰트 설정 및 크기 조정
        font = self._adjust_font_size(title, draw, self.default_font_size)
        
        # 텍스트 위치 계산
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (self.video_width - text_width) / 2
        y = (self.video_height - text_height) / 2
        
        # 텍스트 그리기 (흰색에 그림자 효과)
        shadow_offset = 5
        draw.text((x + shadow_offset, y + shadow_offset), title, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), title, font=font, fill=(255, 255, 255))
        
        # 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"thumbnail_{timestamp}.jpg"
        output_path = os.path.join(output_dir, filename)
        
        img.save(output_path, quality=95)
        logging.info(f"썸네일 생성 완료: {output_path}")
        return output_path

    def generate_video(self, title: str, audio_path: str, output_dir: str = "static/videos") -> Tuple[str, str, float]:
        """동영상 생성 (썸네일 + 오디오 조합)"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. 썸네일 생성
        thumbnail_path = self.generate_thumbnail(title)
        
        # 2. 오디오 파일 로드
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # 3. 비디오 클립 생성 (썸네일 이미지를 오디오 길이만큼 지속)
            video_clip = ImageClip(thumbnail_path, duration=duration)
            video_clip = video_clip.set_audio(audio_clip)
            
            # 4. 해상도 조정 (1080x1920)
            video_clip = resize(video_clip, (self.video_width, self.video_height))
            
            # 5. 비디오 저장
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"video_{timestamp}.mp4"
            output_path = os.path.join(output_dir, filename)
            
            video_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                threads=4,
                preset='fast',
                ffmpeg_params=['-movflags', '+faststart']
            )
            
            logging.info(f"동영상 생성 완료: {output_path} (길이: {duration:.2f}초)")
            return output_path, thumbnail_path, duration
            
        except Exception as e:
            logging.error(f"동영상 생성 실패: {str(e)}")
            raise

# 비디오 생성기 인스턴스
video_generator = VideoGenerator()

if __name__ == "__main__":
    test_title = "AI의 미래: 어떻게 변화할까?"
    test_audio = "static/audio/test_audio.mp3"
    
    if not os.path.exists(test_audio):
        logging.error("테스트 오디오 파일이 없습니다. 먼저 오디오를 생성하세요.")
    else:
        try:
            video_path, thumb_path, duration = video_generator.generate_video(test_title, test_audio)
            print(f"생성된 영상: {video_path}")
            print(f"썸네일: {thumb_path}")
            print(f"길이: {duration:.2f}초")
        except Exception as e:
            print(f"테스트 실패: {e}")
