from pytrends.request import TrendReq
import logging
import os
import random
from typing import Optional, List
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static/logs/trending.log'),
        logging.StreamHandler()
    ]
)

DEFAULT_KEYWORDS = [
    'AI', '머신러닝', '딥러닝', '기술', '프로그래밍', 
    '파이썬', '자바스크립트', '개발', '코딩', 'IT',
    '과학', '미래기술', '자동화', '로봇', '빅데이터',
    '클라우드', '보안', '해킹', '블록체인', '메타버스',
    '가상현실', '증강현실', 'NFT', '암호화폐', '비트코인',
    '인공지능', '사물인터넷', '5G', '자율주행', '드론'
]

class TrendAnalyzer:
    def __init__(self):
        self.pytrends = TrendReq(
            hl='ko-KR',
            tz=540,  # KST (UTC+9)
            timeout=(10, 25),
            retries=3,
            backoff_factor=0.3
        )
        self.cache_file = 'static/logs/trend_cache.json'
        self.cache_expiry = timedelta(hours=6)
        self.last_fetch_time = None
        self.cached_data = None

    def _load_cached_data(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    cache_time = datetime.fromisoformat(data['timestamp'])
                    if datetime.now() - cache_time < self.cache_expiry:
                        return data['trends']
            except:
                pass
        return None

    def _save_to_cache(self, trends):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'trends': trends
            }, f)

    def get_trending_topics(self, keywords: Optional[List[str]] = None) -> List[dict]:
        """인기 있는 트렌드 주제 목록 반환"""
        try:
            # 캐시 확인
            cached = self._load_cached_data()
            if cached:
                logging.info("캐시된 트렌드 데이터 사용")
                return cached

            if not keywords:
                env_keywords = os.getenv("TREND_KEYWORDS")
                keywords = [k.strip() for k in env_keywords.split(',')] if env_keywords else DEFAULT_KEYWORDS

            # 지난 3일간의 데이터 요청
            self.pytrends.build_payload(
                keywords,
                cat=0,
                timeframe='now 3-d',
                geo='KR',
                gprop=''
            )

            # 관련 쿼리 가져오기
            related_queries = self.pytrends.related_queries()
            trending_topics = []

            for kw in keywords:
                if kw in related_queries and related_queries[kw]['top'] is not None:
                    top_queries = related_queries[kw]['top'].head(5)
                    for _, row in top_queries.iterrows():
                        trending_topics.append({
                            'keyword': kw,
                            'query': row['query'],
                            'value': row['value']
                        })

            # 결과가 없으면 기본 키워드 중 랜덤 선택
            if not trending_topics:
                logging.warning("트렌드 데이터 없음. 기본 키워드 사용")
                return [{'keyword': '기술', 'query': random.choice(DEFAULT_KEYWORDS), 'value': 50}]

            # 값에 따라 정렬
            trending_topics.sort(key=lambda x: x['value'], reverse=True)

            # 캐시 저장
            self._save_to_cache(trending_topics)

            return trending_topics[:10]  # 상위 10개만 반환

        except Exception as e:
            logging.error(f"트렌드 분석 실패: {str(e)}")
            # 실패 시 기본 키워드 반환
            return [{'keyword': '기술', 'query': random.choice(DEFAULT_KEYWORDS), 'value': 50}]

    def get_daily_trend(self) -> dict:
        """일일 최고 트렌드 주제 반환"""
        trends = self.get_trending_topics()
        if not trends:
            return {
                'topic': random.choice(DEFAULT_KEYWORDS),
                'score': 50,
                'category': '기술'
            }
        
        top_trend = trends[0]
        return {
            'topic': top_trend['query'],
            'score': top_trend['value'],
            'category': top_trend['keyword']
        }

# 트렌드 분석기 인스턴스
trend_analyzer = TrendAnalyzer()

if __name__ == "__main__":
    try:
        trends = trend_analyzer.get_trending_topics()
        print("=== 오늘의 상위 트렌드 ===")
        for i, trend in enumerate(trends[:5], 1):
            print(f"{i}. {trend['query']} (관련어: {trend['keyword']}, 점수: {trend['value']})")
        
        daily_trend = trend_analyzer.get_daily_trend()
        print("\n=== 오늘의 추천 주제 ===")
        print(f"주제: {daily_trend['topic']}")
        print(f"카테고리: {daily_trend['category']}")
        print(f"인기 점수: {daily_trend['score']}")
    except Exception as e:
        print(f"트렌드 분석 중 오류 발생: {e}")
