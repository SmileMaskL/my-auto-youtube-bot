# secure_main.py
import os
import sys
import time
import random
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import Voice, VoiceSettings, generate as eleven_generate
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from pydantic import root_validator

# ========================
# 🛠️ 강화된 호환성 패치
# ========================
class APIConfigPatch:
    @root_validator(pre=True)
    @classmethod
    def validate_root(cls, values):
        if 'elevenlabs' not in sys.modules:
            subprocess.run("pip install elevenlabs==1.56.1 --quiet", shell=True)
        return values

# ========================
# 🔐 자동 의존성 설치
# ========================
def install_dependencies():
    required = {
        'pydantic': 'pydantic==2.5.3',
        'elevenlabs': 'elevenlabs==1.56.1',  # 최신 안정화 버전
        'moviepy': 'moviepy==1.0.3',
        'python-dotenv': 'python-dotenv==1.0.0'
    }
    
    for pkg, ver in required.items():
        try:
            __import__(pkg)
        except:
            subprocess.run(f"pip install {ver} --quiet", shell=True)
    
    if not os.path.exists("shorts_template.mp4"):
        ColorClip((1080,1920), color=(0,0,0), duration=15).write_videofile("shorts_template.mp4", fps=24, logger=None)

install_dependencies()

# ========================
# 🤖 프로덕션급 자동화 시스템
# ========================
class YouTubeAutomationPro:
    def __init__(self):
        self._init_apis()
        self.quota_tracker = {
            'openai': {'daily':0, 'monthly':0, 'limit_daily':4500, 'limit_monthly':95000},
            'youtube': {'daily':0, 'monthly':0, 'limit_daily':90, 'limit_monthly':2900},
            'elevenlabs': {'daily':0, 'monthly':0, 'limit_daily':9500, 'limit_monthly':295000}
        }
        self._last_reset = datetime.now()
        self.max_retries = 5

    def _init_apis(self):
        load_dotenv()
        
        # 🔑 OpenAI 초기화 (강화된 키 검증)
        self.openai_keys = [k.strip() for k in os.getenv('OPENAI_KEYS', '').split(',') if k.strip()]
        if not self.openai_keys:
            raise ValueError("❌ OPENAI_KEYS 환경변수 오류")
        self.current_key = random.randint(0, len(self.openai_keys)-1)
        
        # 🔊 ElevenLabs 초기화
        self.voice_config = Voice(
            voice_id=os.getenv('ELEVENLABS_VOICE_ID'),
            settings=VoiceSettings(
                stability=0.85,
                similarity_boost=0.95
            )
        )
        
        # 📺 YouTube API 빌드
        self.youtube = build('youtube', 'v3', credentials=Credentials.from_authorized_user_info({
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN')
        }))

    # ========================
    # 🔄 스마트 키 순환 시스템
    # ========================
    def _rotate_key(self):
        self.current_key = (self.current_key + 1) % len(self.openai_keys)
        print(f"🔄 OpenAI 키 순환: {self.current_key+1}번 키 활성화")

    # ========================
    # ⚙️ 쿼터 관리 시스템
    # ========================
    def _check_quota(self, service):
        now = datetime.now()
        if (now - self._last_reset).days >= 1:
            for s in self.quota_tracker:
                self.quota_tracker[s]['daily'] = 0
            self._last_reset = now
        
        if self.quota_tracker[service]['daily'] >= self.quota_tracker[service]['limit_daily']:
            sleep_time = (now.replace(hour=0, minute=0, second=0) + timedelta(days=1) - now).seconds
            time.sleep(sleep_time)
            self._check_quota(service)

    # ========================
    # 🎨 콘텐츠 생성 모듈
    # ========================
    def generate_script(self):
        for attempt in range(self.max_retries):
            try:
                self._check_quota('openai')
                client = OpenAI(api_key=self.openai_keys[self.current_key])
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{
                        "role": "system",
                        "content": f"한국어 YouTube 스크립트 생성 (800자 이상). 키워드: {os.getenv('TREND_KEYWORDS')}"
                    }]
                )
                self.quota_tracker['openai']['daily'] += 1
                return response.choices[0].message.content.strip()
            except Exception as e:
                self._rotate_key()
                time.sleep(2 ** attempt)
        raise Exception("스크립트 생성 실패")

    def text_to_speech(self, text):
        self._check_quota('elevenlabs')
        try:
            audio = eleven_generate(
                text=text[:5000],
                voice=self.voice_config,
                model="eleven_multilingual_v2"
            )
            with open("audio.mp3", "wb") as f:
                f.write(audio)
            self.quota_tracker['elevenlabs']['daily'] += len(text)
            return "audio.mp3"
        except Exception as e:
            raise Exception(f"음성 변환 실패: {str(e)}")

    # ========================
    # 🖼️ 썸네일 & 영상 처리
    # ========================
    def create_thumbnail(self, title):
        try:
            img = Image.new('RGB', (1280, 720), color=(30,30,30))
            d = ImageDraw.Draw(img)
            font_path = "malgun.ttf" if os.name == 'nt' else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            try:
                font = ImageFont.truetype(font_path, 60)
            except:
                font = ImageFont.load_default()
            wrapped_title = "\n".join([title[i:i+20] for i in range(0, len(title), 20)])
            d.multiline_text((100, 200), wrapped_title, fill=(255,255,0), font=font, spacing=30)
            img.save("thumbnail.jpg")
            return "thumbnail.jpg"
        except Exception as e:
            print("⚠️ 썸네일 생성 실패. 기본 이미지 사용")
            return "default_thumbnail.jpg"

    def create_video(self, audio_path):
        try:
            video = VideoFileClip("shorts_template.mp4")
            audio = AudioFileClip(audio_path)
            return video.set_audio(audio).set_duration(audio.duration)
        except Exception as e:
            raise Exception(f"영상 합성 오류: {str(e)}")

    # ========================
    # 🚀 업로드 모듈
    # ========================
    def upload_video(self, file_path):
        self._check_quota('youtube')
        try:
            title = f"{os.getenv('VIDEO_PREFIX')} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            request = self.youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title[:100],
                        "description": f"🔗 자동 생성 콘텐츠\n키워드: {os.getenv('TREND_KEYWORDS')}",
                        "categoryId": "22",
                        "thumbnails": {"default": {"url": self.create_thumbnail(title)}}
                    },
                    "status": {"privacyStatus": "public"}
                },
                media_body=file_path
            )
            response = request.execute()
            self.quota_tracker['youtube']['daily'] += 1
            return response['id']
        except Exception as e:
            raise Exception(f"업로드 실패: {str(e)}")

    def post_comment(self, video_id):
        try:
            self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": os.getenv('DEFAULT_COMMENT')
                            }
                        }
                    }
                }
            ).execute()
        except Exception as e:
            print("⚠️ 댓글 작성 실패 (쿼터 초과 가능성)")

    # ========================
    # �� 안정화 워크플로우
    # ========================
    def execute_workflow(self):
        for attempt in range(self.max_retries):
            try:
                script = self.generate_script()
                audio = self.text_to_speech(script)
                video = self.create_video(audio)
                video.write_videofile("final.mp4", codec='libx264', logger=None)
                
                video_id = self.upload_video("final.mp4")
                self.post_comment(video_id)
                
                print(f"✅ 성공: https://youtu.be/{video_id}")
                return True
            except Exception as e:
                print(f"🔄 재시도 {attempt+1}/{self.max_retries}")
                time.sleep(5 ** attempt)
        return False

# ========================
# 🚀 실행 블록
# ========================
if __name__ == "__main__":
    bot = YouTubeAutomationPro()
    total = int(os.getenv('DAILY_VIDEOS', 3))
    
    for idx in range(1, total+1):
        print(f"\n🎬 {idx}/{total} 영상 제작 시작")
        if bot.execute_workflow():
            print(f"✔️ {idx}번 완료")
        else:
            print(f"❌ {idx}번 실패 (모든 재시도 소진)")
        time.sleep(3600//total)

