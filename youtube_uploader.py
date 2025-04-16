# youtube_uploader.py
import os
import logging
import random
import time
from datetime import datetime
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from quota_manager import quota_manager

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 기본 설정
VIDEO_CATEGORY_ID = "22"  # 사람 & 블로그
SHORTS_HASHTAGS = "#Shorts #YouTube #AI #자동화"
DEFAULT_TAGS = ["Shorts", "YouTube", "AI", "자동화", "트렌드", "정보"]

# 자동 댓글 생성용 템플릿
COMMENT_TEMPLATES = [
    "새 영상이 업로드 되었습니다! 이 영상이 마음에 드셨다면 구독과 좋아요 부탁드립니다 😊",
    "여러분의 의견이 궁금합니다! 댓글로 알려주세요 👇",
    "다음 영상에서 다루었으면 하는 주제가 있으신가요? 댓글로 알려주세요 ✨",
    "정기적으로 새로운 콘텐츠를 업로드하고 있습니다. 알림 설정 부탁드립니다 🔔",
    "영상이 도움이 되었다면 친구들에게 공유해 주세요 📱"
]

def upload_video_to_youtube(youtube, file_path, title, description, thumbnail_path=None, tags=None, is_shorts=True, auto_comment=True, privacy_status="public"):
    """동영상을 YouTube에 업로드하고 썸네일 및 댓글 설정"""
    logging.info(f"Starting YouTube upload process for video: {title}")
    
    # YouTube API 쿼터 확인
    if not quota_manager.check_youtube_quota(50):  # 업로드는 50 유닛 소비
        logging.error("YouTube API quota would be exceeded. Aborting upload.")
        return None
    
    # 업로드 날짜 형식화
    upload_date = datetime.now().strftime("%Y년 %m월 %d일")
    
    # 제목에 날짜 추가 (선택적)
    # title = f"{title} - {upload_date}"
    
    # Shorts 태그 추가
    if is_shorts:
        if "#Shorts" not in title and "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        if SHORTS_HASHTAGS not in description:
            description += f"\n\n{SHORTS_HASHTAGS}"
    
    # 기본 태그 설정
    if tags is None:
        tags = DEFAULT_TAGS
    elif isinstance(tags, str):
        tags = tags.split(',')
    
    # 동영상 메타데이터 설정
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": VIDEO_CATEGORY_ID
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }
    
    # 파일 존재 확인
    if not os.path.exists(file_path):
        logging.error(f"Video file not found: {file_path}")
        return None
    
    # 업로드 진행
    try:
        logging.info(f"Uploading file: {file_path}")
        media = MediaFileUpload(file_path, chunksize=1024*1024, resumable=True)
        
        # 업로드 요청 생성
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        # 업로드 진행
        response = None
        retries = 0
        max_retries = 3
        
        while response is None and retries < max_retries:
            try:
                status, response = request.next_chunk()
                if status:
                    logging.info(f"Upload progress: {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    retries += 1
                    logging.warning(f"Upload error (attempt {retries}/{max_retries}): {e}")
                    time.sleep(5 * retries)  # 지수 백오프
                else:
                    logging.error(f"Upload failed with HttpError: {e}")
                    return None
        
        if retries >= max_retries:
            logging.error("Upload failed after multiple retries")
            return None
        
        if not response:
            logging.error("Upload completed but no response received")
            return None
        
        video_id = response.get("id")
        logging.info(f"Video uploaded successfully! Video ID: {video_id}")
        
        # 썸네일 업로드 (있는 경우)
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                logging.info(f"Uploading thumbnail: {thumbnail_path}")
                
                # 썸네일 업로드 전 쿼터 확인
                if quota_manager.check_youtube_quota(50):
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logging.info("Thumbnail uploaded successfully!")
                else:
                    logging.warning("Skipping thumbnail upload due to quota limitations")
            except Exception as e:
                logging.error(f"Failed to upload thumbnail: {e}")
        
        # 자동 댓글 작성 (옵션)
        if auto_comment:
            try:
                # 댓글 작성 전 쿼터 확인
                if quota_manager.check_youtube_quota(50):
                    comment_text = random.choice(COMMENT_TEMPLATES)
                    youtube.commentThreads().insert(
                        part="snippet",
                        body={
                            "snippet": {
                                "videoId": video_id,
                                "topLevelComment": {
                                    "snippet": {
                                        "textOriginal": comment_text
                                    }
                                }
                            }
                        }
                    ).execute()
                    logging.info(f"Posted auto-comment: {comment_text}")
                else:
                    logging.warning("Skipping auto-comment due to quota limitations")
            except Exception as e:
                logging.error(f"Failed to post comment: {e}")
        
        return video_id
    
    except HttpError as e:
        logging.error(f"An HTTP error occurred during upload: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during upload: {e}")
        return None

def log_upload(video_id, title, description):
    """업로드 정보 로깅"""
    if not video_id:
        return
    
    log_file = "upload_history.csv"
    header = "timestamp,video_id,title,description\n"
    
    # 파일이 없으면 헤더 추가
    if not os.path.exists(log_file):
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(header)
    
    # 로그 추가
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        # CSV 형식으로 안전하게 저장 (쉼표 및 줄바꿈 처리)
        safe_title = title.replace(",", "，").replace("\n", " ")
        safe_desc = description.replace(",", "，").replace("\n", " ")
        f.write(f"{timestamp},{video_id},{safe_title},{safe_desc}\n")
    
    logging.info(f"Upload logged to {log_file}")

if __name__ == "__main__":
    # 테스트 코드
    from dotenv import load_dotenv
    load_dotenv()
    
    from secure_main import authenticate_youtube_api
    
    try:
        youtube = authenticate_youtube_api()
        
        # 테스트 파일 (실제 경로로 변경 필요)
        test_video = "generated_videos/test_video.mp4"
        test_thumbnail = "generated_thumbnails/test_thumbnail.jpg"
        
        if os.path.exists(test_video):
            video_id = upload_video_to_youtube(
                youtube=youtube,
                file_path=test_video,
                title="테스트 영상 #Shorts",
                description="이것은 API 테스트 영상입니다.\n\n자동화 시스템 테스트 중입니다.",
                thumbnail_path=test_thumbnail if os.path.exists(test_thumbnail) else None
            )
            
            if video_id:
                print(f"테스트 성공! 비디오 ID: {video_id}")
                log_upload(video_id, "테스트 영상", "테스트 설명")
            else:
                print("업로드 실패")
        else:
            print(f"테스트 비디오 파일이 없습니다: {test_video}")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
