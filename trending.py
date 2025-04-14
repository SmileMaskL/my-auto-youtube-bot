from pytrends.request import TrendReq
import logging
import os
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 트렌드 검색 시 사용할 기본 키워드 목록
DEFAULT_KEYWORDS = ['AI', '뉴스', '게임', 'IT', '기술', '경제', '유튜브']

def get_trending_topic(keywords=None):
    """Google Trends에서 현재 인기 있는 주제(키워드)를 가져옵니다."""
    logging.info("Fetching trending topic from Google Trends...")

    # 환경 변수 또는 기본값에서 키워드 목록 가져오기
    if keywords is None:
        keywords_str = os.getenv("TREND_KEYWORDS")
        if keywords_str:
            keywords = [kw.strip() for kw in keywords_str.split(',')]
            logging.info(f"Using keywords from TREND_KEYWORDS env var: {keywords}")
        else:
            keywords = DEFAULT_KEYWORDS
            logging.info(f"Using default keywords: {keywords}")

    if not keywords:
        logging.warning("No keywords provided for trending topic search. Returning default.")
        return "오늘의 주요 토픽" # 키워드가 없을 경우 기본값 반환

    try:
        # 한국 지역, 시간대 설정
        pytrends = TrendReq(hl='ko-KR', tz=540) # tz=540은 KST (UTC+9)

        # 지난 1일간의 데이터 요청
        pytrends.build_payload(keywords, cat=0, timeframe='now 1-d', geo='KR', gprop='')

        # 시간별 관심도 데이터 가져오기
        interest_over_time_df = pytrends.interest_over_time()

        if interest_over_time_df.empty or 'isPartial' in interest_over_time_df.columns and len(interest_over_time_df.columns) == 1:
            logging.warning("Google Trends returned no significant data for the keywords. Selecting a random keyword.")
            # 데이터가 없거나 'isPartial' 열만 있는 경우, 제공된 키워드 중 하나를 무작위 반환
            return random.choice(keywords) if keywords else "오늘의 주요 토픽"

        # 'isPartial' 열 제외 (존재하는 경우)
        if 'isPartial' in interest_over_time_df.columns:
            interest_over_time_df = interest_over_time_df.drop(columns=['isPartial'])

        # 합계 내림차순으로 정렬하여 가장 관심도가 높은 키워드 찾기
        # 간혹 모든 키워드 관심도가 0일 수 있음
        if interest_over_time_df.sum().max() == 0:
             logging.warning("All keywords have zero interest in the specified timeframe. Selecting a random keyword.")
             return random.choice(keywords) if keywords else "오늘의 주요 토픽"

        # 가장 관심도 높은 키워드 선택
        top_keyword = interest_over_time_df.sum().idxmax()
        logging.info(f"Top trending keyword identified: {top_keyword}")
        return top_keyword

    except Exception as e:
        # pytrends 라이브러리 관련 오류 또는 네트워크 문제
        logging.error(f"Error fetching trending topics from Google Trends: {e}")
        logging.info("Returning a default topic due to error.")
        # 오류 발생 시 기본 주제 또는 랜덤 키워드 반환
        return random.choice(keywords) if keywords else "오늘의 주요 토픽"

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # 로컬 테스트 시 .env 파일 로드 가능
    # from dotenv import load_dotenv
    # load_dotenv()
    topic = get_trending_topic()
    print(f"오늘의 추천 트렌드 토픽: {topic}")
