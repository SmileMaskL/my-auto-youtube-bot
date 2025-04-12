from dotenv import load_dotenv
load_dotenv()  # .env 파일 로드

import os
import requests
import random
import time
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from pytrends.request import TrendReq
from youtube_upload import upload_video
import moviepy.editor as mp

# ========== 환경 변수 검증 ==========
def validate_environment():
    required_vars = [
        *[f"OPENAI_API_KEY_{i}" for i in range(1, 11)],  # OpenAI 키 10개
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"❌ 누락된 환경 변수: {', '.join(missing)}")

validate_environment()  # 시작 전 검증

# ========== OpenAI 멀티 API 키 관리 시스템 ==========
OPENAI_KEYS = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]
current_key_index = random.randint(0, 9)  # 초기 랜덤 시작

def get_openai_client():
    global current_key_index
    for _ in range(len(OPENAI_KEYS)):
        key = OPENAI_KEYS[current_key_index]
        
        # 키 형식 검증
        if not key.startswith("sk-"):
            print(f"⚠️ 잘못된 API 키 형식: KEY_{current_key_index+1}")
            current_key_index = (current_key_index + 1) % len(OPENAI_KEYS)
            continue
            
        try:
            client = OpenAI(api_key=key)
            client.models.list()  # API 키 유효성 검증
            return client
        except Exception as e:
            print(f"⚠️ API 키 {current_key_index+1} 실패: {str(e)[:100]}")
            current_key_index = (current_key_index + 1) % len(OPENAI_KEYS)
    raise RuntimeError("🚨 모든 OpenAI API 키가 유효하지 않습니다.")

# ========== 핵심 기능 ==========
def fetch_trend_keyword():
    """구글 트렌드에서 실시간 인기 키워드 추출"""
    try:
        pytrends = TrendReq()
        trends = pytrends.today_searches(pn='KR')  # 한국 기준
        return trends[0] if len(trends) > 0 else "AI 자동화"
    except Exception as e:
        print(f"⚠️ 트렌드 조회 실패: {str(e)[:100]}")
        return "AI 자동화"

def generate_video_script(keyword):
    """GPT-4로 영상 스크립트 생성"""
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"'{keyword}' 주제의 1분 유튜브 스크립트를 생성해줘. 문장 단위로 줄바꿈하고, 각 문장은 5초 분량으로 작성."
            }]
        )
        return [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]
    except Exception as e:
        print(f"⚠️ 스크립트 생성 실패: {str(e)[:100]}")
        return [f"{keyword}에 대한 최신 정보를 전달드립니다."]

def generate_background_image(prompt):
    """DALL-E 3으로 배경 이미지 생성"""
    client = get_openai_client()
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"유튜브 썸네일 스타일: {prompt}, 고화질, 최신 트렌드, 한국어 텍스트 없음",
            size="1024x1024",
            quality="hd"
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url, timeout=15).content
        with open("static/background.png", "wb") as f:
            f.write(img_data)
        return Image.open("static/background.png")
    except Exception as e:
        print(f"⚠️ 이미지 생성 실패: {str(e)[:100]}")
        return Image.new('RGB', (1920, 1080), (0, 0, 0))  # 검은 배경

def download_background_music():
    """무료 BGM 다운로드"""
    try:
        bgm_urls = [
            "https://cdn.pixabay.com/music/free/bg-music-168515.mp3",
            "https://cdn.pixabay.com/music/free/retro-80s-171304.mp3"
        ]
        response = requests.get(random.choice(bgm_urls), timeout=10)
        with open("static/music.mp3", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"⚠️ BGM 다운로드 실패: {str(e)[:100]}")

def render_video(script_lines):
    """영상 렌더링"""
    try:
        # 1. 배경 이미지 준비
        bg_image = generate_background_image(script_lines[0])
        
        # 2. 프레임 생성
        clips = []
        for idx, line in enumerate(script_lines):
            try:
                img = bg_image.copy()
                draw = ImageDraw.Draw(img)
                font = ImageFont.truetype("malgun.ttf", 60)
                
                # 텍스트 중앙 정렬
                text_width = draw.textlength(line, font=font)
                draw.text(
                    ((1920 - text_width) // 2, 500),
                    line,
                    font=font,
                    fill="white",
                    stroke_width=2,
                    stroke_fill="black"
                )
                img.save(f"static/frame_{idx}.png")
                
                # 클립 추가
                clip = mp.ImageClip(f"static/frame_{idx}.png").set_duration(5)
                clips.append(clip)
            except Exception as e:
                print(f"⚠️ 프레임 {idx+1} 생성 실패: {str(e)[:100]}")
        
        # 3. 음악 추가
        audio = mp.AudioFileClip("static/music.mp3").subclip(0, sum(clip.duration for clip in clips))
        
        # 4. 최종 영상 생성
        final_clip = mp.concatenate_videoclips(clips).set_audio(audio)
        final_clip.write_videofile(
            "static/output.mp4",
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None  # 로그 출력 방지
        )
    except Exception as e:
        print(f"🚨 영상 생성 실패: {str(e)[:100]}")
        raise

# ========== 메인 실행 ==========
if __name__ == "__main__":
    for attempt in range(3):  # 최대 3회 재시도
        try:
            # 1. 트렌드 키워드 추출
            keyword = fetch_trend_keyword()
            print(f"🔍 오늘의 키워드: {keyword}")
            
            # 2. 스크립트 생성
            script = generate_video_script(keyword)
            print("📜 생성된 스크립트:", script)
            
            # 3. 리소스 준비
            download_background_music()
            
            # 4. 영상 제작
            render_video(script)
            
            # 5. 유튜브 업로드
            upload_video(
                video_path="static/output.mp4",
                title=f"{keyword} 🔥 자동 생성 영상",
                description=f"✔️ {keyword} 관련 최신 정보\n✔️ AI 자동 생성 콘텐츠",
                tags=["AI자동화", "트렌드", keyword]
            )
            break
        except Exception as e:
            print(f"🚨 메인 실행 실패 ({attempt+1}/3): {str(e)[:100]}")
            time.sleep(10)
    else:
        print("❌ 모든 시도 실패. 수동 확인 필요")
