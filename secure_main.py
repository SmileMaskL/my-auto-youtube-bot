import os
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from pytrends.request import TrendReq
from youtube_upload import upload_video
import moviepy.editor as mp
import time

# OpenAI 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_1"))

# 1. 실시간 트렌드 키워드 수집
def get_trend_keyword():
    try:
        pytrends = TrendReq()
        trends = pytrends.today_searches(pn='KR')
        return trends[0]
    except Exception as e:
        print(f"트렌드 수집 실패: {e}")
        return "AI 자동화"  # 기본 키워드

# 2. AI 스크립트 생성 (GPT-4)
def generate_script(keyword):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"'{keyword}' 주제로 1분 길이의 유튜브 스크립트를 생성해줘. 문장 단위로 줄바꿈."
        }]
    )
    return [line for line in response.choices[0].message.content.split('\n') if line.strip()]

# 3. 배경 이미지 생성 (DALL-E 3)
def create_background_image(prompt):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"유튜브 배경 이미지, {prompt}, 고퀄리티, 최신 트렌드",
            size="1024x1024",
            quality="standard"
        )
        img_url = response.data[0].url
        img_data = requests.get(img_url).content
        with open("static/bg.png", "wb") as f:
            f.write(img_data)
        return Image.open("static/bg.png")
    except Exception as e:
        print(f"이미지 생성 실패: {e}")
        return Image.new('RGB', (1920, 1080), color=(0, 0, 0))  # 검은 배경

# 4. 무료 BGM 다운로드
def download_bgm():
    try:
        bgm_url = "https://cdn.pixabay.com/music/free/bg-music-168515.mp3"  # 실제 무료 BGM
        response = requests.get(bgm_url)
        with open("static/music.mp3", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"BGM 다운로드 실패: {e}")

# 5. 영상 제작
def create_video(script_lines):
    clips = []
    bg_image = create_background_image(script_lines[0])
    
    for line in script_lines:
        # 텍스트 이미지 생성
        img = bg_image.copy()
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("malgun.ttf", 60)
        text_width = draw.textlength(line, font=font)
        draw.text(((1920-text_width)/2, 500), line, font=font, fill="white")
        img.save(f"static/temp_{line[:5]}.png")
        
        # 클립 생성
        clip = mp.ImageClip(f"static/temp_{line[:5]}.png").set_duration(3)
        clips.append(clip)
    
    # 음악 추가
    audio = mp.AudioFileClip("static/music.mp3").subclip(0, len(clips)*3)
    final_clip = mp.concatenate_videoclips(clips).set_audio(audio)
    final_clip.write_videofile("static/output.mp4", fps=24, codec='libx264')

if __name__ == "__main__":
    keyword = get_trend_keyword()
    script = generate_script(keyword)
    download_bgm()
    create_video(script)
    upload_video(
        video_path="static/output.mp4",
        title=f"{keyword} 🚀 AI 자동 생성 영상",
        description="이 영상은 완전 자동화 시스템으로 제작되었습니다.",
        tags=["AI자동화", "트렌드", "유튜브자동업로드"]
    )
