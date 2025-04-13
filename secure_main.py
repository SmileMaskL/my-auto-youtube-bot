import os
import json
from datetime import datetime
from gtts import gTTS
import openai
import requests
from elevenlabs import set_api_key
from elevenlabs.api import generate
from youtube_upload import upload_video_to_youtube

# ElevenLabs API 키 설정
set_api_key(os.getenv("ELEVENLABS_KEY"))

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY_1")
openai.api_key = os.getenv("OPENAI_API_KEY_2")
openai.api_key = os.getenv("OPENAI_API_KEY_3")
openai.api_key = os.getenv("OPENAI_API_KEY_4")
openai.api_key = os.getenv("OPENAI_API_KEY_5")
openai.api_key = os.getenv("OPENAI_API_KEY_6")
openai.api_key = os.getenv("OPENAI_API_KEY_7")
openai.api_key = os.getenv("OPENAI_API_KEY_8")
openai.api_key = os.getenv("OPENAI_API_KEY_9")
openai.api_key = os.getenv("OPENAI_API_KEY_10")

# 트렌드 가져오기
def get_trending_keywords():
    try:
        response = requests.get("https://trends.google.com/trends/api/dailytrends?hl=ko&geo=KR&ns=15")
        data = json.loads(response.text[5:])
        trends = data["default"]["trendingSearchesDays"][0]["trendingSearches"]
        return [trend["title"]["query"] for trend in trends][:5]
    except Exception as e:
        print("트렌드 가져오기 실패:", e)
        return []

# ChatGPT로 콘텐츠 생성
def generate_script(keyword):
    prompt = f"{keyword}에 대해 3분 분량의 유튜브 영상 스크립트를 작성해줘."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print("스크립트 생성 실패:", e)
        return ""

# ElevenLabs로 오디오 생성
def generate_audio(text, voice_id):
    audio = generate(
        text=text,
        voice=voice_id,
        model="eleven_monolingual_v1"
    )
    return audio

# 오디오 저장
def save_audio(audio, filename="output.mp3"):
    with open(filename, "wb") as f:
        f.write(audio)

# 영상 생성 (간단하게 정적 이미지 사용)
def create_video(image_path, audio_path, output_path):
    os.system(f"ffmpeg -y -loop 1 -i {image_path} -i {audio_path} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest {output_path}")

# 메인 실행
def main():
    keywords = get_trending_keywords()
    print("트렌드 추출 완료:", keywords)

    if not keywords:
        return

    title = keywords[0]
    script = generate_script(title)

    if not script:
        return

    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    audio = generate_audio(script, voice_id)
    save_audio(audio, "output.mp3")

    if not os.path.exists("static"):
        os.makedirs("static")

    image_path = "static/background.jpg"  # 기본 배경 이미지 경로
    video_path = f"static/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    create_video(image_path, "output.mp3", video_path)
    upload_video_to_youtube(video_path, title, script[:100])

if __name__ == "__main__":
    main()

