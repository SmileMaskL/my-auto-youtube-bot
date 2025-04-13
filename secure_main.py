# secure_main.py

import os
import time
from secure_generate_script import generate_script
from secure_text_to_audio import text_to_audio
from secure_generate_video import generate_video
from youtube_upload import upload_video
from pytrends.request import TrendReq
from openai_rotate import get_openai_api_key
from dotenv import load_dotenv

load_dotenv()  # 로컬 실행 시 필요

MAX_VIDEOS_PER_DAY = 6

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

        openai_api_key = get_openai_api_key()  # ← 수정된 키 선택 방식

        try:
            script_text = generate_script(keyword, openai_api_key=openai_api_key)
            audio_path = text_to_audio(script_text, f"audio_{i}.mp3")
            video_path = generate_video(script_text, audio_path, f"video_{i}.mp4")

            # 썸네일 경로 추가
            thumbnail_path = "default_thumbnail.jpg"

            upload_video(
                video_path=video_path,
                title=f"{keyword} | 오늘의 트렌드 뉴스",
                description=script_text,
                thumbnail_path=thumbnail_path,
                tags=[keyword, "트렌드", "뉴스", "인공지능"]
            )

            print(f"'{keyword}' 영상 업로드 완료.\n")
            time.sleep(60)

        except Exception as e:
            print(f"에러 발생: {keyword} 처리 중 에러 - {e}")

if __name__ == "__main__":
    main()

