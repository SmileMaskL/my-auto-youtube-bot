# secure_main.py

import os
import random
import time
from dotenv import load_dotenv
from trending import get_trending_topic
from video_maker import make_video
from youtube_upload import upload_video
from elevenlabs import text_to_speech, save
import openai

# 환경변수 불러오기
load_dotenv()

# ElevenLabs 설정
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# OpenAI API Key 로테이션용 리스트 구성
OPENAI_KEYS = [v for k, v in os.environ.items() if k.startswith("OPENAI_API_KEY_")]

def generate_script(topic):
    for api_key in OPENAI_KEYS:
        openai.api_key = api_key
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "너는 인기 트렌드에 대해 짧고 흥미로운 설명을 제공하는 AI야."},
                    {"role": "user", "content": f"{topic}에 대해 3문장으로 설명해줘."}
                ]
            )
            return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(f"[WARN] API Key {api_key} - Rate limit. 다음 키로 시도 중...")
            time.sleep(1)
            continue
    raise Exception("모든 OpenAI API 키의 요청 제한이 초과되었습니다.")

# 트렌드 주제 가져오기
topic = get_trending_topic()
print(f"📈 트렌드 주제: {topic}")

# 텍스트 콘텐츠 생성 (OpenAI 사용)
content = generate_script(topic)
print(f"📝 생성된 콘텐츠:\n{content}")

# 음성 생성
audio = text_to_speech(
    text=content,
    voice=VOICE_ID,
    model="eleven_multilingual_v2"
)

# mp3 저장
output_path = "output.mp3"
save(audio, output_path)
print(f"🔊 오디오 저장 완료: {output_path}")

# 영상 생성
video_path = make_video(topic, output_path)
print(f"🎬 영상 생성 완료: {video_path}")

# 유튜브 업로드
upload_video(video_path, title=topic, description=f"{topic}에 대한 자동 생성 콘텐츠입니다.")
print("✅ YouTube 업로드 완료!")

