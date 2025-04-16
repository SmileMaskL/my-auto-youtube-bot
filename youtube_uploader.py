import os
import logging
from googleapiclient.http import MediaFileUpload

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def upload_video(youtube, video_path, title, description, thumbnail_path=None):
    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_path, resumable=True)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logging.info(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    logging.info(f"Video uploaded successfully, ID: {video_id}")

    if thumbnail_path:
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        logging.info("Thumbnail uploaded successfully.")

    return video_id

if __name__ == "__main__":
    from secure_main import authenticate_youtube_api

    youtube = authenticate_youtube_api()
    video_id = upload_video(
        youtube=youtube,
        video_path="output_video.mp4",
        title="Test Video",
        description="This is a test video."
    )
    logging.info(f"Video ID: {video_id}")
