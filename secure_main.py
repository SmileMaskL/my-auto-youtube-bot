import os
import json
from datetime import datetime
import openai
import requests
from elevenlabs.api import generate
from youtube_upload import upload_video_to_youtube

# ✅ OpenAI API 키 자동 로테이션 리스트
OPENAI_KEYS = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]

# ✅ 트렌드 가져오기
def get_trending_keywords():
    try:
        response = requests.get("https://trends.google.com/trends/api/dailytrends?hl=ko&geo=KR&ns=15")
        data = json.loads(response.text[5:])
        trends = data["default"]["trendingSearchesDays"][0]["trendingSearches"]
        return [trend["title"]["query"] for trend in trends][:5]
    except Exception as e:
        print("트렌드 가져오기 실패:", e)
        return []

# ✅ OpenAI ChatGPT 스크립트 생성 (키 순차 시도)
def generate_script(keyword):
    prompt = f"{keyword}에 대해 3분 분량의 유튜브 영상 스크립트를 작성해줘."
    for key in OPENAI_KEYS:
        try:
            openai.api_key = key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[OpenAI 실패] 다음 키로 전환 중: {e}")
            continue
    print("❌ 모든 OpenAI 키 사용 실패.")
    return ""

# ✅ ElevenLabs 오디오 생성 (환경변수로 인증됨)
def generate_audio(text, voice_id):
    try:
        audio = generate(
            text=text,
            voice=voice_id,
            model="eleven_monolingual_v1"
        )
        return audio
    except Exception as e:
        print("오디오 생성 실패:", e)
        return None

# ✅ 오디오 저장
def save_audio(audio, filename="output.mp3"):
    with open(filename, "wb") as f:
        f.write(audio)

# ✅ 영상 생성 (정적 이미지 + 오디오)
def create_video(image_path, audio_path, output_path):
    os.system(f"ffmpeg -y -loop 1 -i {image_path} -i {audio_path} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest {output_path}")

# ✅ 메인 실행 함수
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
    if audio is None:
        return

    save_audio(audio, "output.mp3")

    if not os.path.exists("static"):
        os.makedirs("static")

    image_path = "static/background.jpg"
    video_path = f"static/{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    create_video(image_path, "output.mp3", video_path)
    upload_video_to_youtube(video_path, title, script[:100])

if __name__ == "__main__":
    main()

