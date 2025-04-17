# 환경 변수(키) 검증 파일
import os
from dotenv import load_dotenv

def check_env():
    load_dotenv()
    errors = []

    REQUIRED_KEYS = {
        'ELEVENLABS_KEY': 'ElevenLabs API 키',
        'ELEVENLABS_VOICE_ID': 'ElevenLabs 보이스 ID',
        'OPENAI_API_KEYS': 'OpenAI API 키들 (세미콜론 구분)',
        'GOOGLE_CREDS': 'Google 인증 정보 (JSON)',
        'YOUTUBE_CLIENT_SECRETS_JSON': 'YouTube 클라이언트 시크릿 (JSON)'
    }

    print("="*50)
    print("환경 변수 검증 시작")
    print("="*50)

    for key, description in REQUIRED_KEYS.items():
        value = os.getenv(key)
        if not value:
            errors.append(f"❌ {description}({key}) 누락됨")
        else:
            print(f"✅ {description}: {'설정됨' if len(value) < 20 else '설정됨 (길이:' + str(len(value)) + ')'}")

    if 'OPENAI_API_KEYS' in os.environ:
        key_count = len(os.getenv('OPENAI_API_KEYS').split(';'))
        print(f"\n🔑 OpenAI 키 개수: {key_count}개")
        if key_count < 5:
            errors.append("❌ OpenAI 키는 최소 5개 이상 필요합니다")

    if errors:
        print("\n⚠️ 발견된 오류:")
        for error in errors:
            print(error)
        print("\n💡 해결 방법:")
        print("1. .env 파일을 프로젝트 루트에 생성하세요")
        print("2. GitHub Secrets에 필요한 키들을 추가하세요")
        print("3. OPENAI_API_KEYS=key1;key2;key3 형식으로 입력하세요")
    else:
        print("\n🎉 모든 환경 변수가 정상적으로 설정되었습니다!")

if __name__ == "__main__":
    check_env()
