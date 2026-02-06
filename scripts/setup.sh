#!/bin/bash

echo "🚀 PIXI 프로젝트 초기 설정을 시작합니다..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수 정의
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. 시스템 의존성 확인
print_status "시스템 의존성을 확인합니다..."

# Node.js 확인
if ! command -v node &> /dev/null; then
    print_error "Node.js가 설치되지 않았습니다. https://nodejs.org/에서 설치해주세요."
    exit 1
fi

# Python 확인
if ! command -v python3 &> /dev/null; then
    print_error "Python 3가 설치되지 않았습니다."
    exit 1
fi

# PostgreSQL 확인
if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL이 설치되지 않았습니다. 데이터베이스 기능을 사용할 수 없습니다."
fi

# Redis 확인
if ! command -v redis-cli &> /dev/null; then
    print_warning "Redis가 설치되지 않았습니다. 캐시 기능을 사용할 수 없습니다."
fi

print_status "시스템 의존성 확인 완료"

# 2. 프론트엔드 설정
print_status "프론트엔드를 설정합니다..."
cd frontend

if [ ! -d "node_modules" ]; then
    print_status "npm 패키지를 설치합니다..."
    npm install
else
    print_status "npm 패키지가 이미 설치되어 있습니다."
fi

# .env.local 파일 생성
if [ ! -f ".env.local" ]; then
    print_status ".env.local 파일을 생성합니다..."
    cat > .env.local << EOF
# Mapbox 설정
NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token-here

# API 설정
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# 환경 설정
NEXT_PUBLIC_ENVIRONMENT=development
EOF
    print_warning "frontend/.env.local 파일을 생성했습니다. Mapbox 토큰을 설정해주세요."
else
    print_status ".env.local 파일이 이미 존재합니다."
fi

cd ..

# 3. 백엔드 설정
print_status "백엔드를 설정합니다..."
cd backend

# 가상환경 생성
if [ ! -d "venv" ]; then
    print_status "Python 가상환경을 생성합니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
print_status "가상환경을 활성화합니다..."
source venv/bin/activate

# 패키지 설치
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt 파일을 찾을 수 없습니다."
    exit 1
fi

print_status "Python 패키지를 설치합니다..."
pip install -r requirements.txt

# .env 파일 생성
if [ ! -f ".env" ]; then
    print_status ".env 파일을 생성합니다..."
    cat > .env << EOF
# 데이터베이스 설정
DATABASE_URL=postgresql://user:password@localhost/pixi_db
POSTGRES_SERVER=localhost
POSTGRES_USER=pixi_user
POSTGRES_PASSWORD=pixi_password
POSTGRES_DB=pixi_db

# Redis 설정
REDIS_URL=redis://localhost:6379

# Mapbox 설정
MAPBOX_ACCESS_TOKEN=your-mapbox-token-here

# 보안 설정
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=11520
EOF
    print_warning "backend/.env 파일을 생성했습니다. 데이터베이스 정보를 설정해주세요."
else
    print_status ".env 파일이 이미 존재합니다."
fi

deactivate
cd ..

# 4. 데이터 파이프라인 설정
print_status "데이터 파이프라인을 설정합니다..."
cd data-pipeline

# requirements.txt가 있는 경우에만 설치
if [ -f "requirements.txt" ]; then
    print_status "데이터 파이프라인 패키지를 설치합니다..."
    pip install -r requirements.txt
else
    print_warning "data-pipeline/requirements.txt 파일이 없습니다."
fi

cd ..

# 5. 환경 변수 설정 가이드
echo ""
echo "🎉 PIXI 프로젝트 초기 설정이 완료되었습니다!"
echo ""
echo "📋 다음 단계를 진행해주세요:"
echo ""
echo "1. Mapbox 액세스 토큰 설정:"
echo "   - https://account.mapbox.com/access-tokens/에서 토큰 생성"
echo "   - frontend/.env.local과 backend/.env에 설정"
echo ""
echo "2. 데이터베이스 설정:"
echo "   - PostgreSQL 설치 및 pixi_db 데이터베이스 생성"
echo "   - backend/.env의 데이터베이스 정보 수정"
echo ""
echo "3. 서비스 실행:"
echo "   - 프론트엔드: cd frontend && npm run dev"
echo "   - 백엔드: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "📚 자세한 내용은 README.md를 참조하세요."
echo ""
