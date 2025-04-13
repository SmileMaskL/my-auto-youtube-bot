# trending.py
from pytrends.request import TrendReq

def get_trending_topic():
    pytrends = TrendReq(hl='ko', tz=540)
    
    try:
        kw_list = ['AI', 'ChatGPT', '유튜브', '게임', '뉴스']  # 예비 키워드 리스트
        pytrends.build_payload(kw_list, cat=0, timeframe='now 1-d', geo='KR', gprop='')
        interest = pytrends.interest_over_time()

        if not interest.empty:
            top_keyword = interest.sum().sort_values(ascending=False).index[0]
            return top_keyword
        else:
            return "오늘의 인기 주제"
    except Exception as e:
        print(f"[트렌드 추출 오류] {e}")
        return "오늘의 인기 주제"

