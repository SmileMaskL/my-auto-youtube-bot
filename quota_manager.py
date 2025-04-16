import os
import json
import time
import logging
import random
from datetime import datetime, timedelta

# 쿼터 상태를 저장할 파일
QUOTA_FILE = "quota_status.json"

class QuotaManager:
    """API 서비스 쿼터 관리 클래스"""
    
    def __init__(self):
        self.quota_data = self._load_quota_data()
        
    def _load_quota_data(self):
        """쿼터 상태 데이터 로드"""
        if os.path.exists(QUOTA_FILE):
            try:
                with open(QUOTA_FILE, 'r') as f:
                    data = json.load(f)
                    logging.info(f"Loaded quota data from {QUOTA_FILE}")
                    return data
            except Exception as e:
                logging.error(f"Error loading quota data: {e}")
        
        # 기본 쿼터 데이터 구조
        return {
            "openai": {
                "daily_limit": 500,  # 일일 요청 한도
                "daily_used": 0,
                "last_reset": datetime.now().strftime("%Y-%m-%d"),
                "keys": {}  # 각 키별 사용량
            },
            "elevenlabs": {
                "monthly_limit": 10000,  # 월간 글자 수 한도 (무료 플랜)
                "monthly_used": 0,
                "last_reset": datetime.now().strftime("%Y-%m"),
                "last_used": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "youtube": {
                "daily_limit": 10000,  # 일일 유닛 한도
                "daily_used": 0,
                "last_reset": datetime.now().strftime("%Y-%m-%d"),
                "last_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    def _save_quota_data(self):
        """쿼터 상태 데이터 저장"""
        try:
            with open(QUOTA_FILE, 'w') as f:
                json.dump(self.quota_data, f, indent=2)
                logging.info(f"Saved quota data to {QUOTA_FILE}")
        except Exception as e:
            logging.error(f"Error saving quota data: {e}")
    
    def _reset_if_needed(self, service, period="daily"):
        """필요시 사용량 리셋 (일간/월간)"""
        now = datetime.now()
        
        if period == "daily":
            last_reset = datetime.strptime(self.quota_data[service]["last_reset"], "%Y-%m-%d")
            if now.date() > last_reset.date():
                logging.info(f"Resetting daily quota for {service}")
                self.quota_data[service]["daily_used"] = 0
                self.quota_data[service]["last_reset"] = now.strftime("%Y-%m-%d")
                self._save_quota_data()
                
        elif period == "monthly":
            last_reset = datetime.strptime(self.quota_data[service]["last_reset"], "%Y-%m")
            if now.strftime("%Y-%m") > self.quota_data[service]["last_reset"]:
                logging.info(f"Resetting monthly quota for {service}")
                self.quota_data[service]["monthly_used"] = 0
                self.quota_data[service]["last_reset"] = now.strftime("%Y-%m")
                self._save_quota_data()
    
    def check_openai_quota(self, api_key):
        """OpenAI API 쿼터 확인 및 업데이트"""
        self._reset_if_needed("openai", "daily")
        
        # 키 ID 생성 (앞 8자리 사용)
        key_id = api_key[:8] + "..."
        
        # 키별 사용량 초기화 (필요시)
        if key_id not in self.quota_data["openai"]["keys"]:
            self.quota_data["openai"]["keys"][key_id] = 0
        
        # 일일 한도 확인
        if self.quota_data["openai"]["daily_used"] >= self.quota_data["openai"]["daily_limit"]:
            logging.warning(f"OpenAI daily quota exceeded: {self.quota_data['openai']['daily_used']}/{self.quota_data['openai']['daily_limit']}")
            return False
        
        # 키별 사용량 업데이트 (예측값: 평균 1 요청당 1 포인트로 가정)
        usage_estimate = 1
        self.quota_data["openai"]["daily_used"] += usage_estimate
        self.quota_data["openai"]["keys"][key_id] += usage_estimate
        self._save_quota_data()
        
        return True
    
    def log_openai_usage(self, api_key, tokens_used):
        """실제 OpenAI 사용량 기록"""
        key_id = api_key[:8] + "..."
        self.quota_data["openai"]["keys"][key_id] += tokens_used
        self._save_quota_data()
    
    def check_elevenlabs_quota(self, text_length):
        """ElevenLabs 쿼터 확인 및 업데이트"""
        self._reset_if_needed("elevenlabs", "monthly")
        
        # 월간 한도 확인
        if self.quota_data["elevenlabs"]["monthly_used"] + text_length > self.quota_data["elevenlabs"]["monthly_limit"]:
            logging.warning(f"ElevenLabs monthly character quota would be exceeded: {self.quota_data['elevenlabs']['monthly_used']}/{self.quota_data['elevenlabs']['monthly_limit']}")
            return False
        
        # 요청 간 딜레이 확인 (무료 플랜은 요청 속도 제한이 있을 수 있음)
        last_used = datetime.strptime(self.quota_data["elevenlabs"]["last_used"], "%Y-%m-%d %H:%M:%S")
        elapsed_seconds = (datetime.now() - last_used).total_seconds()
        
        if elapsed_seconds < 5:  # 최소 5초 간격
            delay = 5 - elapsed_seconds
            logging.info(f"Rate limiting ElevenLabs API. Waiting {delay:.2f} seconds...")
            time.sleep(delay)
        
        # 사용량 업데이트
        self.quota_data["elevenlabs"]["monthly_used"] += text_length
        self.quota_data["elevenlabs"]["last_used"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_quota_data()
        
        return True
    
    def check_youtube_quota(self, operation_cost=50):
        """YouTube API 쿼터 확인 및 업데이트"""
        self._reset_if_needed("youtube", "daily")
        
        # 일일 한도 확인
        if self.quota_data["youtube"]["daily_used"] + operation_cost > self.quota_data["youtube"]["daily_limit"]:
            logging.warning(f"YouTube API daily quota would be exceeded: {self.quota_data['youtube']['daily_used']}/{self.quota_data['youtube']['daily_limit']}")
            return False
        
        # 업로드 간 딜레이 확인 (레이트 리밋 방지)
        last_upload = datetime.strptime(self.quota_data["youtube"]["last_upload"], "%Y-%m-%d %H:%M:%S")
        elapsed_seconds = (datetime.now() - last_upload).total_seconds()
        
        if elapsed_seconds < 60 and operation_cost > 5:  # 업로드는 최소 1분 간격
            delay = 60 - elapsed_seconds
            logging.info(f"Rate limiting YouTube API uploads. Waiting {delay:.2f} seconds...")
            time.sleep(delay)
        
        # 사용량 업데이트
        self.quota_data["youtube"]["daily_used"] += operation_cost
        self.quota_data["youtube"]["last_upload"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_quota_data()
        
        return True
    
    def get_best_openai_key(self):
        """가장 사용량이 적은 OpenAI API 키 선택"""
        available_keys = []
        
        # 환경 변수에서 키 목록 가져오기
        i = 1
        while True:
            key = os.getenv(f"OPENAI_API_KEY_{i}")
            if key:
                available_keys.append(key)
                i += 1
            else:
                if i > 10:  # 최대 10개 키까지 확인
                    break
                break
        
        if not available_keys:
            logging.error("No OpenAI API keys found in environment variables.")
            raise ValueError("OpenAI API key not found")
        
        # 각 키의 사용량 확인
        key_usage = {}
        for key in available_keys:
            key_id = key[:8] + "..."
            if key_id in self.quota_data["openai"]["keys"]:
                key_usage[key] = self.quota_data["openai"]["keys"][key_id]
            else:
                key_usage[key] = 0  # 새 키는 사용량 0으로 초기화
        
        # 사용량이 가장 적은 키 선택 (동일하면 랜덤 선택)
        min_usage = min(key_usage.values())
        candidates = [k for k, v in key_usage.items() if v == min_usage]
        selected_key = random.choice(candidates)
        
        logging.info(f"Selected OpenAI API key: {selected_key[:8]}...")
        return selected_key

# 글로벌 인스턴스
quota_manager = QuotaManager()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    
    # 테스트
    test_key = quota_manager.get_best_openai_key()
    print(f"Selected key: {test_key[:8]}...")
    
    if quota_manager.check_openai_quota(test_key):
        print("OpenAI quota check passed")
    else:
        print("OpenAI quota check failed")
    
    if quota_manager.check_elevenlabs_quota(100):
        print("ElevenLabs quota check passed for 100 characters")
    else:
        print("ElevenLabs quota check failed")
    
    if quota_manager.check_youtube_quota():
        print("YouTube quota check passed")
    else:
        print("YouTube quota check failed")
