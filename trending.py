from pytrends.request import TrendReq

def get_trending_topic():
    pytrends = TrendReq(hl='ko', tz=540)
    trending = pytrends.trending_searches(pn='south_korea')
    if not trending.empty:
        return trending[0]
    else:
        return "인기 주제"

