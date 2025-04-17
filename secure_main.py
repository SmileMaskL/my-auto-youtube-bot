import os
from youtube_upload import upload_video, post_comment_to_video
from secure_generate_video import generate_video, convert_to_shorts_format

def main():
    print("\n✅ 트렌드 기반 영상 생성 시작")
    video_path = generate_video()

    shorts_path = "output/final_shorts.mp4"
    convert_to_shorts_format(video_path, shorts_path)

    print("\n✅ 유튜브 업로드 시작")
    video_id = upload_video(shorts_path, "[트렌드] 오늘의 짧은 영상", "대한민국 트렌드 기반 Shorts 영상입니다.", ["Shorts", "트렌드"])

    post_comment_to_video(video_id, "시청해주셔서 감사합니다! 더 많은 트렌드 영상 기대해주세요 😊")

if __name__ == "__main__":
    main()
