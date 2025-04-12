from dotenv import load_dotenv
load_dotenv()

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
        *[f"OPENAI_API_KEY_{i}" for i in range(1, 11)],
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"❌ 누락된 환경 변수: {', '.join(missing)}")

validate_environment()

# ========== OpenAI 클라이언트 초기화 (프록시 설정 제거) ==========
OPENAI_KEYS = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]
current_key_index = random.randint(0, 9)

def get_openai_client():
    global current_key_index
    for _ in range(len(OPENAI_KEYS)):
        key = OPENAI_KEYS[current_key_index]
        
        try:
            # 프록시 매개변수 완전 제거 ▼
            client = OpenAI(api_key=key)  # proxies={...} 삭제
            client.models.list()
            return client
        except Exception as e:
            print(f"⚠️ API 키 {current_key_index+1} 실패: {str(e)[:100]}")
            current_key_index = (current_key_index + 1) % len(OPENAI_KEYS)
    raise RuntimeError("🚨 모든 OpenAI API 키가 유효하지 않습니다.")

# ========== Google 트렌드 조회 (404 오류 해결) ==========
def fetch_trend_keyword():
    try:
        pytrends = TrendReq(hl='ko-KR', tz=540)  # 한국 설정 강화
        df = pytrends.trending_searches(pn='south_korea')  # 올바른 지역 코드
        return df[0].values[0] if not df.empty else "AI 자동화"
    except Exception as e:
        print(f"⚠️ 트렌드 조회 실패: {str(e)[:100]}")
        return "AI 자동화"

# ========== AI 스크립트 생성 ==========
def generate_video_script(keyword):
    client = get_openai_client()
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"'{keyword}' 주제의 1분 유튜브 스크립트를 생성해줘. 문장 단위로 줄바꿈."
            }]
        )
        return [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]
    except Exception as e:
        print(f"⚠️ 스크립트 생성 실패: {str(e)[:100]}")
        return [f"{keyword}에 대한 최신 정보를 전달드립니다."]

# ========== 배경 이미지 생성 ==========
def generate_background_image(prompt):
    client = get_openai_client()
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"유튜브 배경: {prompt}, 고퀄리티, 최신 트렌드",
            size="1024x1024"
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url, timeout=15).content
        with open("static/background.png", "wb") as f:
            f.write(img_data)
        return Image.open("static/background.png")
    except Exception as e:
        print(f"⚠️ 이미지 생성 실패: {str(e)[:100]}")
        return Image.new('RGB', (1920, 1080), (0, 0, 0))

# ========== 음악 다운로드 ==========
def download_background_music():
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

# ========== 영상 렌더링 ==========
def render_video(script_lines):
    try:
        bg_image = generate_background_image(script_lines[0])
        clips = []
        
        for idx, line in enumerate(script_lines):
            img = bg_image.copy()
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("malgun.ttf", 60)
            text_width = draw.textlength(line, font=font)
            draw.text(((1920 - text_width) // 2, 500), line, font=font, fill="white")
            img.save(f"static/frame_{idx}.png")
            clips.append(mp.ImageClip(f"static/frame_{idx}.png").set_duration(5))
        
        audio = mp.AudioFileClip("static/music.mp3").subclip(0, sum(clip.duration for clip in clips))
        final_clip = mp.concatenate_videoclips(clips).set_audio(audio)
        final_clip.write_videofile("static/output.mp4", fps=24, codec="libx264")
    except Exception as e:
        print(f"🚨 영상 생성 실패: {str(e)[:100]}")
        raise

# ========== 메인 실행 ==========
if __name__ == "__main__":
    for attempt in range(3):
        try:
            keyword = fetch_trend_keyword()
            print(f"🔍 오늘의 키워드: {keyword}")
            
            script = generate_video_script(keyword)
            print("📜 생성된 스크립트:", script)
            
            download_background_music()
            render_video(script)
            
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
