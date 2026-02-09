#!/bin/bash
# 백엔드 서버 실행 (venv의 python으로 실행)
cd "$(dirname "$0")"
VENV_PYTHON="../venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
  echo "venv가 없습니다. 프로젝트 루트에서: python -m venv venv && venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi
echo "백엔드 서버 시작: http://localhost:8000"
exec "$VENV_PYTHON" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
