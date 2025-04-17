import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs import Voice, VoiceSettings, generate, set_api_key
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

class UltimateYouTubeAutomator:
    def __init__(self):
        # 10개 OpenAI 키 순환 시스템
        self.openai_keys = os.getenv('OPENAI_KEYS').split(',')
        self.current_key_index = random.randint(0,9)
        self.max_retries = 5
        
        # ElevenLabs 음성 보안 확인
        self.voice_id = self._verify_elevenlabs_voice(os.getenv('ELEVENLABS_VOICE_ID'))
        
        # YouTube API 초기화
        self.youtube = build('youtube', 'v3', credentials=self._get_google_creds())
        
        # 쿼터 관리 강화 시스템
        self.quota_tracker = {
            'openai': {'daily':0, 'monthly':0},
            'youtube': {'daily':0, 'monthly':0}
        }
        self.quota_limits = {
            'openai': {'daily': int(os.getenv('OPENAI_DAILY_LIMIT', 200)), 'monthly': 5000},
            'youtube': {'daily': int(os.getenv('YT_DAILY_LIMIT', 100)), 'monthly': 3000}
        }

    def _verify_elevenlabs_voice(self, voice_id):
        set_api_key(os.getenv('ELEVENLABS_KEY'))
        try:
            voice = Voice.from_id(voice_id)
            if not voice.settings.public:
                raise Exception("음성 설정이 비공개 상태입니다. ElevenLabs 대시보드에서 공개로 변경 필요")
            return voice_id
        except Exception as e:
            print(f"ElevenLabs 오류: {str(e)}")
            exit(1)

    def _rotate_openai_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.openai_keys)
        os.environ['OPENAI_API_KEY'] = self.openai_keys[self.current_key_index]
        print(f"🔑 키 로테이션 완료: 현재 키 인덱스 {self.current_key_index+1}/{len(self.openai_keys)}")

    def _get_google_creds(self):
        return Credentials.from_authorized_user_info({
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN')
        })

    def _quota_check(self, service):
        if self.quota_tracker[service]['daily'] >= self.quota_limits[service]['daily']:
            raise Exception(f"{service.upper()} 일일 한도 초과")
        if self.quota_tracker[service]['monthly'] >= self.quota_limits[service]['monthly']:
            raise Exception(f"{service.upper()} 월간 한도 초과")

    def _auto_thumbnail(self, title):
        img = Image.new('RGB', (1280, 720), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("malgun.ttf", 40)
        d.text((100,300), title[:50], fill=(255,255,255), font=font)
        img.save("thumbnail.jpg")
        return "thumbnail.jpg"

    def generate_script(self):
        for attempt in range(self.max_retries):
            try:
                self._quota_check('openai')
                client = OpenAI()
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[{
                        "role": "system",
                        "content": f"{os.getenv('TREND_KEYWORDS')} 키워드 기반 YouTube 시나리오 작성. 한국어로 500자 이상"
                    }]
                )
                self.quota_tracker['openai']['daily'] += 1
                self.quota_tracker['openai']['monthly'] += 1
                return response.choices[0].message.content
            except Exception as e:
                if "quota" in str(e).lower():
                    self._rotate_openai_key()
                print(f"시도 {attempt+1} 실패: {str(e)}")
                time.sleep(2**attempt)
        raise Exception("스크립트 생성 최종 실패")

    def text_to_speech(self, text):
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=self.voice_id,
                settings=VoiceSettings(stability=0.7, similarity_boost=0.8)
            ),
            model="eleven_multilingual_v2"
        )
        with open("audio.mp3", "wb") as f:
            f.write(audio)
        return "audio.mp3"

    def create_shorts(self, content):
        clip = VideoFileClip("shorts_template.mp4").subclip(0,15)
        txt_clip = TextClip(content[:100], fontsize=40, color='white', font='malgun').set_position('center').set_duration(15)
        final = CompositeVideoClip([clip, txt_clip])
        final.write_videofile("shorts.mp4", fps=24, codec='libx264')

    def upload_video(self, file_path, is_shorts=False):
        self._quota_check('youtube')
        request_body = {
            "snippet": {
                "title": file_path[:100] + (" #shorts" if is_shorts else ""),
                "description": "자동 생성 콘텐츠",
                "categoryId": "22"
            },
            "status": {"privacyStatus": "public"}
        }
        insert_request = self.youtube.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=file_path
        )
        response = insert_request.execute()
        self.quota_tracker['youtube']['daily'] += 1
        self.quota_tracker['youtube']['monthly'] += 1
        return response['id']

    def auto_comment(self, video_id):
        comment = "🤖 자동 생성 댓글: 콘텐츠가 유익하네요! 더 많은 영상 기대합니다!"
        self.youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {
                            "textOriginal": comment
                        }
                    }
                }
            }
        ).execute()

    def full_workflow(self):
        try:
            # 1. 콘텐츠 생성
            script = self.generate_script()
            
            # 2. 미디어 생성
            audio_path = self.text_to_speech(script)
            self.create_shorts(script)
            thumbnail = self._auto_thumbnail(script)
            
            # 3. 영상 조합
            video_clip = VideoFileClip(audio_path).set_audio(AudioFileClip(audio_path))
            video_clip.write_videofile("final_video.mp4", codec='libx264')
            
            # 4. 업로드 실행
            main_video_id = self.upload_video("final_video.mp4")
            shorts_video_id = self.upload_video("shorts.mp4", is_shorts=True)
            
            # 5. 후처리 작업
            self.auto_comment(main_video_id)
            print(f"✅ 업로드 완료: 메인 영상 {main_video_id} | 쇼츠 {shorts_video_id}")
            
        except Exception as e:
            print(f"⚠️ 크리티컬 에러: {str(e)}")
            print("재시도 대기 중...")
            time.sleep(60)
            self.full_workflow()

if __name__ == "__main__":
    bot = UltimateYouTubeAutomator()
    for i in range(int(os.getenv('DAILY_VIDEOS', 8))):
        print(f"\n🔥 {i+1}번째 영상 생성 시작")
        bot.full_workflow()
        time.sleep(3600//int(os.getenv('DAILY_VIDEOS',8)))

