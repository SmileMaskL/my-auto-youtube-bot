import os
import random
import time
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_audio
from secure_generate_video import generate_video
from youtube_upload import upload_video
from pytrends.request import TrendReq

# 최대 업로드 수 설정 (YouTube API 제한에 맞춤)
MAX_VIDEOS_PER_DAY = 6

# OpenAI 키 목록에서 무작위 선택
OPENAI_KEYS = [os.getenv(f"OPENAI_API_KEY_{i}") for i in range(1, 11)]

def get_trending_keywords():
    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload(kw_list=['뉴스'])
    trending = pytrends.related_queries()['뉴스']['top']
    return [row['query'] for row in trending.head(MAX_VIDEOS_PER_DAY).to_dict('records')]

def main():
    trending_keywords = get_trending_keywords()
    print(f"오늘의 트렌드 주제: {trending_keywords}")

    for i, keyword in enumerate(trending_keywords):
        print(f"\n[{i+1}/{len(trending_keywords)}] '{keyword}' 콘텐츠 생성 시작")

        # API Key 무작위 선택
        openai_api_key = random.choice(OPENAI_KEYS)

        try:
            script_text = generate_script(keyword, openai_api_key=openai_api_key)
            audio_path = text_to_audio(script_text, f"audio_{i}.mp3")
            video_path = generate_video(script_text, audio_path, f"video_{i}.mp4")

            upload_video(
                video_path=video_path,
                title=f"{keyword} | 오늘의 트렌드 뉴스",
                description=script_text,
                tags=[keyword, "트렌드", "뉴스", "인공지능"]
            )

            print(f"'{keyword}' 영상 업로드 완료.\n")

            # 업로드 사이 시간 간격(1분): 유튜브 API 연속 요청 방지
            time.sleep(60)

        except Exception as e:
            print(f"에러 발생: {e}")

if __name__ == "__main__":
    main()

