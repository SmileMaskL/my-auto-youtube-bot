# trending.py
from pytrends.request import TrendReq  # ← 이 줄 추가 필요

def get_trending_topic():
    pytrends = TrendReq(hl='ko', tz=540)
    
    try:
        trending = pytrends.trending_searches(pn='korea')  # ← 'korea'로 수정
        top_topic = trending[0][0]
        return top_topic
    except Exception as e:
        print(f"[트렌드 추출 오류] {e}")
        return "오늘의 인기 주제"

