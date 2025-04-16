python3 -c "
from quota_manager import quota_manager
from openai_rotate import openai_manager
from youtube_uploader import YouTubeUploader

# 초기화 테스트
print('Quota Manager:', quota_manager.get_status())
print('OpenAI Keys:', openai_manager.keys[:2])
print('YouTube Uploader initialized')
"

