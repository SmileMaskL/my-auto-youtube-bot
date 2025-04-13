# youtube_upload.py

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.client import OAuth2Credentials
import os
import json

def upload_video(video_path, title, description, thumbnail_path):
    # 인증 정보 로드
    creds_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    creds_dict = json.loads(creds_json)
    creds = OAuth2Credentials.from_json(json.dumps(creds_dict))

    youtube = build("youtube", "v3", credentials=creds)

    # 비디오 업로드
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": [title],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response.get("id")
    print(f"업로드 완료: https://www.youtube.com/watch?v={video_id}")

    # 썸네일 업로드
    youtube.thumbnails().set(videoId=video_id, media_body=thumbnail_path).execute()
    print("썸네일 업로드 완료")

    # 댓글 등록
    post_comment(youtube, video_id, f"{title}에 대한 자동 생성 콘텐츠입니다.")
    print("댓글 등록 완료")

    # 로그 저장
    with open(".secure_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()}: {video_id} 업로드 완료\n")

def post_comment(youtube, video_id, text):
   
::contentReference[oaicite:0]{index=0}
 

