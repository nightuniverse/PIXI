#!/bin/bash
# 백엔드 서버 실행 (main.py는 backend/ 폴더에 있음 → main:app 사용)
cd "$(dirname "$0")"
source ../venv/bin/activate
echo "백엔드 서버 시작: http://localhost:8000"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
