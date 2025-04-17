# secure_main.py
import os
import logging
from dotenv import load_dotenv
from trending import trend_analyzer
from secure_generate_script import script_generator
from secure_generate_audio import audio_generator
from thumbnail_generator import generate_thumbnail
from video_generator import VideoGenerator
from youtube_upload import upload_video, post_comment
from quota_manager import quota_manager
from openai_rotator import key_rotator

load_dotenv()
logging.basicConfig(level=logging.INFO)

class EnhancedVideoProducer:
    def __init__(self):
        self.video_count = 3  # 하루 생성 영상 수
        self.retry_policy = {
            'max_attempts': 3,
            'backoff_factor': 2
        }

    def produce_videos(self):
        for _ in range(self.video_count):
            try:
                trend = self._get_trend()
                script = self._generate_script(trend)
                audio_path = self._generate_audio(script)
                thumbnail = self._create_thumbnail(trend['topic'])
                video_path = self._render_video(audio_path, thumbnail)
                self._upload_content(video_path, thumbnail, script, trend)
            except Exception as e:
                logging.error(f"영상 생성 실패: {str(e)}")
                continue

    def _get_trend(self):
        for _ in range(self.retry_policy['max_attempts']):
            trend = trend_analyzer.get_daily_trend()
            if trend['score'] > 40:
                return trend
            time.sleep(self.retry_policy['backoff_factor'] ** _)
        raise Exception("적합한 트렌드 찾기 실패")

    def _generate_script(self, trend):
        return script_generator.generate_script(trend)

    def _generate_audio(self, script):
        return audio_generator.text_to_speech(script)

    def _create_thumbnail(self, text):
        return generate_thumbnail(text, "static/thumbnails")

    def _render_video(self, audio_path, thumbnail):
        return VideoGenerator().generate(
            audio_path=audio_path,
            image_path=thumbnail,
            output_dir="static/videos"
        )

    def _upload_content(self, video_path, thumbnail, script, trend):
        video_id = upload_video(
            video_path,
            title=f"{trend['topic']} | 최신 트렌드 분석",
            description=script[:5000],
            tags=["트렌드", "교육", "기술"]
        )
        post_comment(video_id, "📢 매일 업데이트 되는 트렌드! 구독 부탁드려요!")

if __name__ == "__main__":
    producer = EnhancedVideoProducer()
    producer.produce_videos()

