#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Tuple

# 모듈 임포트
from openai_manager import openai_manager
from quota_manager import quota_manager
from trending import trend_analyzer
from secure_generate_script import script_generator
from secure_generate_audio import audio_generator
from secure_generate_video import video_generator
from youtube_uploader import youtube_uploader

# 환경 설정
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('static/logs/auto_bot.log'),
        logging.StreamHandler()
    ]
)

class YouTubeAutoBot:
    def __init__(self):
        self._setup_directories()
        self.max_daily_videos = 3
        self.video_counter = 0
        self.session_start = datetime.now().strftime('%Y%m%d_%H%M%S')

    def _setup_directories(self):
        """필요한 디렉토리 생성"""
        required_dirs = [
            'static/videos',
            'static/audio',
            'static/thumbnails',
            'static/logs'
        ]
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)

    def _get_trending_topic(self) -> Dict[str, Any]:
        """트렌드 주제 가져오기"""
        try:
            topic = trend_analyzer.get_daily_trend()
            logging.info(f"오늘의 트렌드 주제: {topic['topic']} (카테고리: {topic['category']})")
            return topic
        except Exception as e:
            logging.error(f"트렌드 주제 가져오기 실패: {str(e)}")
            return {
                'topic': 'AI와 자동화의 미래',
                'category': '기술',
                'score': 75
            }

    def _generate_content(self, trend_data: Dict[str, Any]) -> Optional[str]:
        """AI로 콘텐츠 생성"""
        try:
            script = script_generator.generate_script(trend_data)
            if not script:
                raise ValueError("생성된 스크립트가 없습니다.")
            
            logging.info("스크립트 생성 완료:\n" + "\n".join([f"{i+1}. {line}" 
                          for i, line in enumerate(script.split('\n'))]))
            return script
        except Exception as e:
            logging.error(f"콘텐츠 생성 실패: {str(e)}")
            return None

    def _generate_audio(self, script: str) -> Optional[str]:
        """텍스트를 음성으로 변환"""
        try:
            audio_path = audio_generator.text_to_speech(script)
            if not audio_path or not os.path.exists(audio_path):
                raise ValueError("오디오 파일 생성 실패")
            
            logging.info(f"오디오 파일 생성 완료: {audio_path}")
            return audio_path
        except Exception as e:
            logging.error(f"오디오 생성 실패: {str(e)}")
            return None

    def _generate_video(self, title: str, audio_path: str) -> Optional[Tuple[str, str, float]]:
        """동영상 생성"""
        try:
            video_path, thumbnail_path, duration = video_generator.generate_video(title, audio_path)
            if not all([video_path, thumbnail_path, duration > 0]):
                raise ValueError("동영상 생성 실패")
            
            logging.info(f"동영상 생성 완료: {video_path} (길이: {duration:.2f}초)")
            return video_path, thumbnail_path, duration
        except Exception as e:
            logging.error(f"동영상 생성 실패: {str(e)}")
            return None

    def _upload_to_youtube(self, video_path: str, title: str, description: str, 
                         thumbnail_path: str) -> Optional[str]:
        """유튜브에 업로드"""
        try:
            video_id = youtube_uploader.upload_video(
                video_path=video_path,
                title=title,
                description=description,
                thumbnail_path=thumbnail_path
            )
            
            if not video_id:
                raise ValueError("업로드 실패 - 비디오 ID 없음")
            
            logging.info(f"유튜브 업로드 성공! 비디오 ID: {video_id}")
            return video_id
        except Exception as e:
            logging.error(f"유튜브 업로드 실패: {str(e)}")
            return None

    def run_pipeline(self) -> bool:
        """전체 프로세스 실행"""
        if self.video_counter >= self.max_daily_videos:
            logging.warning(f"일일 최대 영상 생성 수({self.max_daily_videos})에 도달했습니다.")
            return False

        try:
            # 1. 트렌드 주제 가져오기
            trend_data = self._get_trending_topic()
            title = f"{trend_data['topic']} #shorts"

            # 2. 스크립트 생성
            script = self._generate_content(trend_data)
            if not script:
                return False

            # 3. 오디오 생성
            audio_path = self._generate_audio(script)
            if not audio_path:
                return False

            # 4. 동영상 생성
            video_data = self._generate_video(title, audio_path)
            if not video_data:
                return False

            video_path, thumbnail_path, duration = video_data

            # 5. 유튜브 업로드
            description = f"""이 영상은 AI로 자동 생성되었습니다.
주제: {trend_data['topic']}
카테고리: {trend_data['category']}
인기 점수: {trend_data['score']}/100

#shorts #AI #자동생성"""
            
            video_id = self._upload_to_youtube(video_path, title, description, thumbnail_path)
            if not video_id:
                return False

            self.video_counter += 1
            logging.info(f"성공적으로 파이프라인 완료! (오늘 생성 영상: {self.video_counter}/{self.max_daily_videos})")
            return True

        except Exception as e:
            logging.error(f"파이프라인 실행 중 치명적 오류: {str(e)}", exc_info=True)
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YouTube AutoBot Pro Ultra')
    parser.add_argument('--auto', action='store_true', help='자동 모드 실행')
    parser.add_argument('--max-videos', type=int, default=3, help='최대 생성 영상 수 (기본값: 3)')
    args = parser.parse_args()

    bot = YouTubeAutoBot()
    bot.max_daily_videos = args.max_videos

    if args.auto:
        success = bot.run_pipeline()
        sys.exit(0 if success else 1)
    else:
        print("YouTube AutoBot Pro Ultra - 수동 모드")
        print("자동 모드로 실행하려면 --auto 옵션을 사용하세요.")
        print(f"최대 일일 영상 수: {bot.max_daily_videos}")
        sys.exit(0)
