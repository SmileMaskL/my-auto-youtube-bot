import os
import requests
import random
import time
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from pytrends.request import TrendReq
from youtube_upload import upload_video
import moviepy.editor as mp

# ========== OpenAI 멀티 API 키 관리 시스템 ==========
OPENAI_KEYS = [
    os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)  # KEY_1 ~ KEY_10 자동 로드
]
current_key_index = random.randint(0, 9)  # 초기 랜덤 시작

def get_client():
    global current_key_index
    for _ in range(len(OPENAI_KEYS)):
        try:
            client = OpenAI(api_key=OPENAI_KEYS[current_key_index])
            return client
        except Exception as e:
            print(f"⚠️ API 키 {current_key_index+1} 실패: {str(e)[:50]}")
            current_key_index = (current_key_index + 1) % len(OPENAI_KEYS)
    raise Exception("🚨 모든 API 키 사용 불가!")

# ========== 핵심 기능 ==========
def get_trend_keyword():
    try:
        pytrends = TrendReq()
        return pytrends.today_searches(pn='KR')[0]
    except:
        return "AI 자동화"

def generate_script(keyword):
    client = get_client()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"'{keyword}' 주제의 1분 유튜브 스크립트를 생성. 문장 단위 줄바꿈."
        }]
    )
    return [line for line in response.choices[0].message.content.split('\n') if line.strip()]

def create_background_image(prompt):
    client = get_client()
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"유튜브 배경: {prompt}, 최신 트렌드, 고퀄리티",
            size="1024x1024"
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url, timeout=10).content
        with open("static/bg.png", "wb") as f:
            f.write(img_data)
        return Image.open("static/bg.png")
    except:
        return Image.new('RGB', (1920, 1080), (0, 0, 0))

def download_bgm():
    try:
        bgm_urls = [
            "https://cdn.pixabay.com/music/free/bg-music-168515.mp3",
            "https://cdn.pixabay.com/music/free/retro-80s-171304.mp3"
        ]
        response = requests.get(random.choice(bgm_urls), timeout=10)
        with open("static/music.mp3", "wb") as f:
            f.write(response.content)
    except:
        print("⚠️ BGM 다운로드 실패. 기본 음악 사용")

def create_video(script_lines):
    bg_image = create_background_image(script_lines[0])
    clips = []
    
    for idx, line in enumerate(script_lines):
        try:
            img = bg_image.copy()
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("malgun.ttf", 60)
            text_width = draw.textlength(line, font=font)
            draw.text(((1920-text_width)/2, 500), line, font=font, fill="white")
            img.save(f"static/frame_{idx}.png")
            
            clip = mp.ImageClip(f"static/frame_{idx}.png").set_duration(3)
            clips.append(clip)
        except Exception as e:
            print(f"⚠️ 프레임 {idx+1} 생성 실패: {str(e)[:50]}")

    try:
        audio = mp.AudioFileClip("static/music.mp3").subclip(0, len(clips)*3)
        final_clip = mp.concatenate_videoclips(clips).set_audio(audio)
        final_clip.write_videofile("static/output.mp4", fps=24, codec='libx264', logger=None)
    except:
        print("🚨 영상 생성 실패")

# ========== 메인 실행 ==========
if __name__ == "__main__":
    for attempt in range(3):  # 최대 3회 재시도
        try:
            keyword = get_trend_keyword()
            script = generate_script(keyword)
            download_bgm()
            create_video(script)
            upload_video(
                video_path="static/output.mp4",
                title=f"{keyword} 🔥 AI 자동생성 영상",
                description="✔️ 자동화 시스템으로 제작\n✔️ 매일 업로드",
                tags=["AI자동화", "트렌드", "유튜브자동업로드"]
            )
            break
        except Exception as e:
            print(f"🚨 메인 실행 실패 ({attempt+1}/3): {str(e)[:50]}")
            time.sleep(10)
