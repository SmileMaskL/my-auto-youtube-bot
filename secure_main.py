import os
import json
from datetime import datetime
import openai
import requests
from elevenlabs import generate
from youtube_upload import upload_video_to_youtube

# ✅ OpenAI API 키 자동 로테이션
OPENAI_KEYS = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]

# ✅ 트렌드 키워드 수집
def get_trending_keywords():
    try:
        res = requests.get("https://trends.google.com/trends/api/dailytrends?hl=ko&geo=KR&ns=15")
        data = json.loads(res.text[5:])
        trends = data["default"]["trendingSearchesDays"][0]["trendingSearches"]
        return [t["title"]["query"] for t in trends][:5]
    except Exception as e:
        print("트렌드 수집 실패:", e)
        return []

# ✅ 스크립트 생성 with OpenAI
def generate_script(keyword):
    prompt = f"{keyword}에 대해 3분 분량의 유튜브 영상 스크립트를 작성해줘."
    for key in OPENAI_KEYS:
        try:
            openai.api_key = key
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return res["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[OpenAI 실패] 다음 키로 전환: {e}")
            continue
    print("❌ 모든 키 실패")
    return ""

# ✅ 오디오 생성 (ElevenLabs)
def generate_audio(text):
    try:
        audio = generate(
            text=text,
            voice=os.getenv("ELEVENLABS_VOICE_ID"),
            model="eleven_monolingual_v1"
        )
        return audio
    except Exception as e:
        print("🎤 오디오 생성 실패:", e)
        return None

# ✅ 오디오 저장
def save_audio(audio, filename="output.mp3"):
    with open(filename, "wb") as f:
        f.write(audio)

# ✅ 영상 생성
def create_video(image_path, audio_path, output_path):
    os.system(
        f"ffmpeg -y -loop 1 -i {image_path} -i {audio_path} "
        f"-c:v libx264 -tune stillimage -c:a aac -b:a 192k "
        f"-pix_fmt yuv420p -shortest {output_path}"
    )

# ✅ 메인 프로세스
def main():
    keywords = get_trending_keywords()
    print("트렌드 추출 완료:", keywords)
    if not keywords:
        return

    title = keywords[0]
    script = generate_script(title)
    if not script:
        return

    audio = generate_audio(script)
    if not audio:
        return

    save_audio(audio)

    if not os.path.exists("static"):
        os.makedirs("static")

    image_path = "static/background.jpg"
    video_path = f"static/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    create_video(image_path, "output.mp3", video_path)
    upload_video_to_youtube(video_path, title, script[:100])

if __name__ == "__main__":
    main()

