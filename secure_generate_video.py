import os
import logging
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from datetime import datetime

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 폰트 경로 설정 (GitHub Actions 환경 고려)
# 'fonts-dejavu' 패키지 설치 시 일반적인 경로
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
DEFAULT_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Bold 없을 경우 대비

def get_font(size):
    """사용 가능한 폰트 객체를 반환"""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except IOError:
        logging.warning(f"Font not found at {FONT_PATH}. Trying default font.")
        try:
            return ImageFont.truetype(DEFAULT_FONT_PATH, size)
        except IOError:
            logging.warning(f"Default font not found at {DEFAULT_FONT_PATH}. Using Pillow's default font.")
            # Pillow 기본 폰트는 크기 조절이 제한적일 수 있음
            return ImageFont.load_default()


def generate_thumbnail(title, output_folder="generated_thumbnails", width=1280, height=720):
    """텍스트 기반의 동영상 썸네일 생성"""
    logging.info(f"Generating thumbnail for title: {title}")
    try:
        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logging.info(f"Created output folder: {output_folder}")

        # 배경 이미지 생성 (다이나믹 그라데이션)
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        # 랜덤한 색상 조합 또는 미리 정의된 팔레트 사용 가능
        r1, g1, b1 = random.randint(0, 100), random.randint(0, 100), random.randint(100, 200)
        r2, g2, b2 = random.randint(100, 200), random.randint(0, 100), random.randint(0, 100)

        for y in range(height):
            ratio = y / height
            r = int(r1 * (1 - ratio) + r2 * ratio)
            g = int(g1 * (1 - ratio) + g2 * ratio)
            b = int(b1 * (1 - ratio) + b2 * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # 텍스트 추가 (자동 줄바꿈 및 중앙 정렬)
        font_size = 80 # 기본 폰트 크기
        font = get_font(font_size)
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0, 180) # 약간 투명한 검은색 그림자

        # 텍스트 영역 설정 (가운데 영역)
        max_text_width = width * 0.8
        # 간단한 단어 단위 줄바꿈 로직
        words = title.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            # getbbox 사용 (Pillow 9.0.0 이상 권장) 또는 getlength/getsize (구 버전)
            try:
                # bbox = font.getbbox(test_line) # (left, top, right, bottom)
                # line_width = bbox[2] - bbox[0]
                # line_height = bbox[3] - bbox[1] # 실제 렌더링 높이
                # getsize는 deprecated 될 수 있음
                (line_width, line_height) = font.getsize(test_line)
            except AttributeError: # getsize가 없을 경우 대비 (최신 Pillow는 getbbox)
                 bbox = font.getbbox(test_line)
                 line_width = bbox[2] - bbox[0]
                 line_height = bbox[3] - bbox[1]


            if line_width <= max_text_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line) # 마지막 줄 추가

        # 텍스트 그리기 (중앙 정렬)
        total_text_height = len(lines) * (line_height + 10) # 줄 간격 포함
        y_start = (height - total_text_height) / 2

        for i, line in enumerate(lines):
            try:
                # (lw, lh) = font.getsize(line)
                 bbox = font.getbbox(line)
                 lw = bbox[2] - bbox[0]
                 lh = bbox[3] - bbox[1] + 5 # 높이 약간 여유
            except AttributeError:
                 bbox = font.getbbox(line)
                 lw = bbox[2] - bbox[0]
                 lh = bbox[3] - bbox[1] + 5

            x = (width - lw) / 2
            y = y_start + i * (lh + 10) # 줄 간격 10

            # 그림자 효과 (4방향)
            shadow_offset = 3
            draw.text((x - shadow_offset, y - shadow_offset), line, font=font, fill=shadow_color)
            draw.text((x + shadow_offset, y - shadow_offset), line, font=font, fill=shadow_color)
            draw.text((x - shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=shadow_color)

            # 메인 텍스트
            draw.text((x, y), line, font=font, fill=text_color)

        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in title[:20]) # 제목 일부 사용
        thumbnail_filename = f"thumbnail_{safe_title}_{timestamp}.jpg"
        thumbnail_path = os.path.join(output_folder, thumbnail_filename)
        image.save(thumbnail_path, "JPEG", quality=90) # 품질 설정

        logging.info(f"Thumbnail generated successfully: {thumbnail_path}")
        return thumbnail_path

    except Exception as e:
        logging.error(f"Failed to generate thumbnail: {str(e)}")
        raise

import random # 상단에 import 추가

def generate_video(topic_title, audio_path, output_folder="generated_videos", width=1280, height=720):
    """오디오와 생성된 썸네일을 기반으로 동영상 생성"""
    logging.info(f"Generating video for topic: {topic_title}")
    try:
        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            logging.info(f"Created output folder: {output_folder}")

        # 1. 썸네일 생성 또는 기존 썸네일 사용
        # 여기서는 매번 새로 생성한다고 가정, 필요시 경로를 인자로 받도록 수정 가능
        thumbnail_path = generate_thumbnail(topic_title) # 위에서 정의한 함수 사용
        if not thumbnail_path or not os.path.exists(thumbnail_path):
             raise FileNotFoundError("Thumbnail generation failed or file not found.")

        # 2. 오디오 파일 로드
        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        logging.info(f"Audio duration: {audio_duration:.2f} seconds")

        # 3. 비디오 클립 생성 (썸네일 이미지를 오디오 길이만큼 사용)
        # MoviePy에서 이미지를 비디오 클립으로 만들 때 duration 설정
        video_clip = ImageClip(thumbnail_path, duration=audio_duration)
        video_clip = video_clip.set_audio(audio_clip)
        # 프레임 속도 설정 (유튜브 권장: 24, 25, 30, 48, 50, 60)
        fps = 24

        # 4. 비디오 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in topic_title[:20])
        video_filename = f"video_{safe_title}_{timestamp}.mp4"
        video_path = os.path.join(output_folder, video_filename)

        logging.info(f"Writing video file to: {video_path}")
        # 비디오 코덱, 오디오 코덱, 비트레이트 등 설정 (H.264, AAC 권장)
        # preset: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
        # threads: 사용 가능한 CPU 코어 수에 맞게 조절
        video_clip.write_videofile(
            video_path,
            codec="libx264",        # H.264 코덱
            audio_codec="aac",      # AAC 오디오 코덱
            fps=fps,
            preset="medium",        # 인코딩 속도와 품질 균형 (fast 또는 medium 권장)
            threads=4,              # 사용할 CPU 스레드 수 (환경에 맞게 조절)
            logger='bar',           # 진행률 표시
            ffmpeg_params=[         # 추가적인 ffmpeg 파라미터 (옵션)
                "-b:v", "5000k",    # 비디오 비트레이트 (예: 5000kbps)
                "-b:a", "192k"     # 오디오 비트레이트 (예: 192kbps)
            ]
        )

        # 사용한 클립 메모리 해제 (긴 프로세스 실행 시 도움될 수 있음)
        audio_clip.close()
        video_clip.close()

        logging.info(f"Video generated successfully: {video_path}")
        return video_path, thumbnail_path, audio_duration # 생성된 파일 경로 및 오디오 길이 반환

    except Exception as e:
        logging.error(f"Failed to generate video: {str(e)}")
        # 생성 실패 시 생성된 중간 파일(썸네일 등) 정리 로직 추가 가능
        raise

if __name__ == "__main__":
    # 로컬 테스트용 설정
    logging.basicConfig(level=logging.INFO)
    import time # 시간 측정용

    test_topic = "파이썬과 MoviePy를 이용한 자동 비디오 생성 테스트"
    # 실제 오디오 파일 경로 지정 필요
    # test_audio_file = "path/to/your/test_audio.mp3" # 이 파일을 준비해야 함
    test_audio_file = "generated_audio/audio_YOUR_VOICE_ID_20250414_xxxxxx.mp3" # 실제 생성된 파일 경로

    if not os.path.exists(test_audio_file):
        print(f"오류: 테스트 오디오 파일({test_audio_file})을 찾을 수 없습니다. 먼저 오디오를 생성하세요.")
    else:
        try:
            start_time = time.time()
            generated_video_path, generated_thumbnail_path, duration = generate_video(test_topic, test_audio_file)
            end_time = time.time()
            print(f"테스트 비디오 생성 완료!")
            print(f" - 비디오: {generated_video_path}")
            print(f" - 썸네일: {generated_thumbnail_path}")
            print(f" - 길이: {duration:.2f} 초")
            print(f" - 소요 시간: {end_time - start_time:.2f} 초")
        except Exception as e:
            print(f"테스트 비디오 생성 중 오류 발생: {e}")
