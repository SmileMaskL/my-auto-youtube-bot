import os
import random
from thumbnail_generator import create_thumbnail
from shorts_converter import convert_to_shorts
from comment_generator import generate_comment
from text_to_speech import text_to_speech
from video_generator import generate_video
from youtube_upload import upload_video

def run(auto=False, max_videos=1):
    for i in range(max_videos):
        print(f"[{i+1}] 콘텐츠 생성 시작")

        # 1. 스크립트 생성
        script = f"오늘의 트렌드 내용입니다. 랜덤 값: {random.randint(100, 999)}"

        # 2. 음성 변환
        audio_path = text_to_speech(script)

        # 3. 영상 생성
        video_path = generate_video(audio_path, script)

        # 4. 썸네일 생성
        thumbnail_path = create_thumbnail(script)

        # 5. Shorts 변환
        shorts_path = convert_to_shorts(video_path)

        # 6. 댓글 생성
        comment_text = generate_comment(script)

        # 7. 업로드
        upload_video(
            title="자동 생성 영상",
            description="이 영상은 자동으로 생성되었습니다.\n" + comment_text,
            video_path=shorts_path,
            thumbnail_path=thumbnail_path
        )

        print(f"[{i+1}] 완료 ✅\n")

    print("🎉 모든 영상 자동 생성 및 업로드 완료!")

