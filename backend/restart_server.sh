#!/bin/bash
# 백엔드 서버 재시작 스크립트

echo "백엔드 서버를 재시작합니다..."

# 실행 중인 서버 프로세스 찾기 및 종료
pkill -f "uvicorn main:app" || echo "실행 중인 서버가 없습니다."

# 잠시 대기
sleep 2

# 가상환경 활성화 및 서버 시작
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || echo "가상환경을 찾을 수 없습니다. 수동으로 활성화하세요."

echo "서버를 시작합니다..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
