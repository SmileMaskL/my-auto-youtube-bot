import os
from elevenlabs import set_api_key, text_to_speech, save  # 수정된 import
from dotenv import load_dotenv
from trending import get_trending_topic
from video_maker import make_video
from youtube_upload import upload_video
import random
import time

# .env 파일 로드
load_dotenv()

# ElevenLabs API 키 설정
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
set_api_key(ELEVENLABS_API_KEY)

# OpenAI API 키 로테이션 (API 키가 만료되었을 경우 새 키로 자동 로딩)
def rotate_openai_key():
    openai_keys = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]
    for key in openai_keys:
        if key:
            return key
    return None  # 키가 없으면 None 반환

OPENAI_API_KEY = rotate_openai_key()
if OPENAI_API_KEY:
    print("OpenAI API 키 로드 완료!")
else:
    print("OpenAI API 키가 없습니다.")

# 트렌드 주제 추출
topic = get_trending_topic()
print(f"트렌드 주제: {topic}")

# 텍스트 콘텐츠 생성 (예시)
content = f"오늘의 인기 주제는 {topic}입니다. 이 내용에 대해 자세히 알아보겠습니다."

# 음성 생성
audio = text_to_speech(  # generate -> text_to_speech로 수정
    text=content,
    voice=VOICE_ID,
    model="eleven_multilingual_v2"
)

# mp3 파일로 저장
output_path = "output.mp3"
save(audio, output_path)
print(f"오디오 저장 완료: {output_path}")

# 영상 생성
video_path = make_video(topic, output_path)
print(f"영상 생성 완료: {video_path}")

# YouTube 업로드
upload_video(video_path, title=topic, description=f"{topic}에 대한 자동 생성 콘텐츠입니다.")
print("YouTube 업로드 완료!")

