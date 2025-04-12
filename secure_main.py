import os, random, openai, json, base64
from pytrends.request import TrendReq
from gtts import gTTS
import subprocess
from datetime import datetime
from youtube_upload import upload_video
from dotenv import load_dotenv

load_dotenv()

# ✅ OpenAI API 키 로드 (랜덤 선택)
api_keys = [os.getenv(f'OPENAI_API_KEY_{i}') for i in range(1, 11)]
api_keys = [key for key in api_keys if key]
openai.api_key = random.choice(api_keys)

# ✅ 트렌드 수집 (대한민국)
def get_trends():
    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload(kw_list=[''])
    trending = pytrends.trending_searches(pn='south_korea')
    top_keywords = trending[0].tolist()[:5]
    return top_keywords

# ✅ 스크립트 생성
def generate_script(topic):
    prompt = f"'{topic}'에 대한 흥미롭고 짧은 유튜브 영상 스크립트를 200자 내외로 작성해줘."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['choices'][0]['message']['content']

# ✅ 텍스트를 mp3로 변환
def text_to_speech(text, filename):
    tts = gTTS(text=text, lang='ko')
    tts.save(filename)

# ✅ 영상 생성 (ffmpeg)
def create_video(image_path, audio_path, output_path):
    subprocess.run([
        'ffmpeg',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        '-y',
        output_path
    ])

# ✅ 메인 실행
def main():
    print("🔍 트렌드 수집 중...")
    trends = get_trends()
    print(f"✅ 추출된 트렌드: {trends}")

    if not trends:
        print("❌ 트렌드 없음")
        return

    topic = trends[0]
    script = generate_script(topic)
    print(f"📝 스크립트: {script}")

    today = datetime.now().strftime("%Y%m%d")
    audio_file = f"{today}.mp3"
    video_file = f"{today}.mp4"

    text_to_speech(script, audio_file)
    create_video("static/bg.png", audio_file, video_file)

    upload_video(video_file, topic, script)

if __name__ == "__main__":
    main()

