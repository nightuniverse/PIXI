#!/bin/bash

echo "🕷️ PIXI 스타트업 크롤링 시스템 시작"
echo "=================================="

# 디렉토리 생성
echo "📁 디렉토리 생성 중..."
mkdir -p data-pipeline/data
mkdir -p data-pipeline/logs

# Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo "🐍 Python 가상환경 생성 중..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 가상환경 활성화 중..."
source venv/bin/activate

# 의존성 설치
echo "📦 의존성 패키지 설치 중..."
pip install -r data-pipeline/requirements.txt

# Playwright 브라우저 설치
echo "🌐 Playwright 브라우저 설치 중..."
playwright install chromium

# 간단한 크롤링 실행 (테스트용)
echo "🚀 간단한 크롤링 실행 중..."
cd data-pipeline
python scripts/simple_crawler.py

echo "=================================="
echo "🎉 크롤링 완료!"
echo "📁 데이터 위치: data-pipeline/data/"
echo "📊 결과 파일:"
ls -la data/

# 크롤링된 데이터 미리보기
echo ""
echo "📋 크롤링된 데이터 미리보기:"
if [ -f "data/all_crawled_data.json" ]; then
    echo "전체 데이터 개수: $(jq length data/all_crawled_data.json)"
    echo "첫 번째 항목:"
    jq '.[0]' data/all_crawled_data.json
fi
