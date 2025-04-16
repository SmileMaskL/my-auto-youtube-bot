import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from moviepy.editor import VideoFileClip
from quota_manager import quota_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class YouTubeUploader:
    def __init__(self, credentials):
        self.service = build('youtube', 'v3', credentials=credentials)
        self.max_retries = 3

    def _convert_to_shorts(self, video_path):
        try:
            clip = VideoFileClip(video_path)
            if clip.duration > 60:
                new_path = video_path.replace('.mp4', '_shorts.mp4')
                clip = clip.subclip(0, min(60, clip.duration))
                clip.write_videofile(new_path, codec='libx264', audio_codec='aac')
                logging.info(f"Converted to shorts: {new_path}")
                return new_path
            return video_path
        except Exception as e:
            logging.error(f"Shorts conversion failed: {str(e)}")
            return video_path

    def upload_video(self, file_path, title, description, thumbnail_path=None, is_shorts=True):
        for attempt in range(self.max_retries):
            if not quota_manager.check_quota('youtube'):
                logging.error("YouTube API daily quota exhausted")
                return None

            try:
                # 쇼츠 변환
                final_path = self._convert_to_shorts(file_path) if is_shorts else file_path

                body = {
                    'snippet': {
                        'title': title,
                        'description': description,
                        'categoryId': '22'
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False
                    }
                }

                if is_shorts:
                    body['contentDetails'] = {'duration': 'PT60S'}

                media = MediaFileUpload(final_path, chunksize=-1, resumable=True)
                request = self.service.videos().insert(
                    part='snippet,status,contentDetails',
                    body=body,
                    media_body=media
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        logging.info(f"Upload progress: {int(status.progress() * 100)}%")

                quota_manager.update_usage('youtube', 1600)  # 비디오 업로드: 1600 quota units
                logging.info(f"Successfully uploaded video ID: {response['id']}")

                # 썸네일 업로드
                if thumbnail_path and os.path.exists(thumbnail_path):
                    self.upload_thumbnail(response['id'], thumbnail_path)

                return response['id']

            except Exception as e:
                logging.error(f"Upload attempt {attempt+1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(5 ** attempt)  # Exponential backoff

    def upload_thumbnail(self, video_id, thumbnail_path):
        try:
            media = MediaFileUpload(thumbnail_path)
            self.service.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            logging.info(f"Thumbnail uploaded for video {video_id}")
        except Exception as e:
            logging.error(f"Thumbnail upload failed: {str(e)}")

    def post_comment(self, video_id, comment_text):
        try:
            self.service.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': comment_text
                            }
                        }
                    }
                }
            ).execute()
            logging.info(f"Comment posted on video {video_id}")
        except Exception as e:
            logging.error(f"Failed to post comment: {str(e)}")

