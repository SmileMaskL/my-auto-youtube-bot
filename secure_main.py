import os
import argparse
from dotenv import load_dotenv
from openai_manager import get_openai_response
from text_to_speech import text_to_speech
from secure_generate_video import generate_video
from youtube_uploader import upload_video
from thumbnail_generator import generate_thumbnail

load_dotenv()

def generate_script(topic="AI 트렌드 요약"):
    prompt = f"{topic}에 대해 한국어로 유튜브 영상 대본을 써줘. 짧고 명확하게."
    result = get_openai_response(prompt)
    return result['choices'][0]['text'].strip()

def main(auto=False, max_videos=1):
    for _ in range(max_videos):
        script = generate_script()
        audio_path = text_to_speech(script)
        video_path = generate_video(audio_path)
        thumbnail_path = generate_thumbnail(script)
        upload_video(video_path, script, "자동 생성 영상입니다.", thumbnail_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--max-videos", type=int, default=1)
    args = parser.parse_args()
    main(args.auto, args.max_videos)

