import os
import json
import random
from pathlib import Path
from pytrends.request import TrendReq
from openai import OpenAI
from youtube_upload import upload_video_to_youtube
from elevenlabs import generate_audio
from utils import text_to_speech, create_video, clean_folder

# 필수 디렉토리 생성
Path("static").mkdir(exist_ok=True)
Path("static/audio").mkdir(parents=True, exist_ok=True)
Path("static/video").mkdir(parents=True, exist_ok=True)

# 로그 파일 초기화
log_path = ".secure_log.txt"
with open(log_path, "w") as f:
    f.write("=== LOG START ===\n")

# 트렌드 추출
def get_trending_keywords():
    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload(kw_list=["뉴스"])
    trending = pytrends.related_queries()["뉴스"]["rising"]
    if trending is None:
        return []
    return [item["query"] for item in trending.head(5).to_dict("records")]

keywords = get_trending_keywords()
with open(log_path, "a") as f:
    f.write(f"트렌드 추출 완료: {keywords}\n")

if not keywords:
    raise Exception("트렌드 키워드가 없습니다.")

# ChatGPT로 스크립트 생성
def generate_script(topic):
    openai_api_keys = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]
    openai.api_key = random.choice(openai_api_keys)

    prompt = f"'{topic}'에 대해 약 500자 분량의 한국어 뉴스 스크립트를 작성해줘."
    response = OpenAI().chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

# 작업 시작
for topic in keywords:
    try:
        with open(log_path, "a") as f:
            f.write(f"스크립트 생성 중: {topic}\n")

        script = generate_script(topic)

        # 텍스트를 음성으로 변환 (mp3)
        audio_path = text_to_speech(script, topic)

        # 비디오 생성
        video_path = create_video(audio_path, topic)

        # 유튜브 업로드
        upload_video_to_youtube(video_path, topic, script)

        # 생성된 파일 삭제
        clean_folder()

    except Exception as e:
        with open(log_path, "a") as f:
            f.write(f"에러 발생 - {topic}: {str(e)}\n")

