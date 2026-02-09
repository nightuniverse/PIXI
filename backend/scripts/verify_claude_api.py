#!/usr/bin/env python3
"""
Claude API 키·모델 연동 검증 스크립트.
프로젝트 루트에서: cd backend && ../venv/bin/python scripts/verify_claude_api.py
또는: cd backend && ../venv/bin/python -m scripts.verify_claude_api
"""
import os
import sys

# backend/app 을 path에 넣어서 app.core.config 로드
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def main():
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-anthropic-api-key-here":
        print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다. backend/.env 에 키를 넣어주세요.")
        return 1

    try:
        from anthropic import Anthropic
    except ImportError:
        print("❌ anthropic 패키지 없음. backend에서: ../venv/bin/pip install -r requirements.txt")
        return 1

    client = Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL") or "claude-sonnet-4-20250514"

    print("1. 사용 가능한 모델 목록 조회 중...")
    try:
        page = client.models.list()
        ids = [m.id for m in page]
        print(f"   조회된 모델 수: {len(ids)}")
        for i, mid in enumerate(ids[:10]):
            print(f"   - {mid}")
        if len(ids) > 10:
            print(f"   ... 외 {len(ids) - 10}개")
    except Exception as e:
        print(f"   ❌ 모델 목록 조회 실패: {e}")
        return 1

    if model not in ids:
        print(f"\n⚠️  설정된 모델 '{model}' 이 목록에 없습니다. 위 목록에서 ID를 골라 .env 에 ANTHROPIC_MODEL 로 넣어주세요.")

    print(f"\n2. 메시지 API 호출 테스트 (모델: {model})...")
    try:
        r = client.messages.create(
            model=model,
            max_tokens=64,
            messages=[{"role": "user", "content": "한 줄로 '연동 성공' 이라고만 답해주세요."}],
        )
        text = r.content[0].text if r.content and hasattr(r.content[0], "text") else ""
        print(f"   ✅ 응답: {text.strip()[:100]}")
    except Exception as e:
        print(f"   ❌ 메시지 호출 실패: {e}")
        return 1

    print("\n✅ Claude API 연동이 정상입니다.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
