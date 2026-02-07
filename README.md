# PIXI - Global Startup Ecosystem Explorer

전 세계 스타트업/VC/엑셀러레이터/코워킹/행사 정보를 지도로 탐색하고, 도메인·스테이지·펀딩·성장 시그널로 즉석 비교할 수 있는 웹서비스

## 🚀 핵심 기능

### 지도 탐색 기능
- **월드 맵 탐색**: 도시/국가별 스타트업 클러스터 히트맵
- **엔티티 카드**: Startup/Investor/Accelerator/Space/Events 5종 표준화
- **스마트 필터링**: Domain, Stage, Funding, Hiring 여부
- **성장 시그널**: 웹트래픽, 깃허브, 채용, PR 등 합성 점수
- **실시간 비교**: 2~4개 회사 동시 비교 분석

### AI 공동창업자 기능 (aicofounder.com 스타일)
- **5단계 가이드**: 아이디어 → 조사 → 솔루션 → MVP → 런칭
- **실제 시장 데이터 연동**: 한국 스타트업 생태계 데이터 기반 경쟁사 분석
- **비주얼 캔버스**: 프로젝트 개념 시각화 및 정리
- **프로젝트 메모리**: 로컬 스토리지 기반 대화 기록 및 상태 저장
- **구조화된 가이드**: AI가 대화를 주도하며 단계별 진행
- **프로젝트 상태 요약**: 현재까지의 진행 상황을 한눈에 확인

## 🛠 기술 스택

### Frontend
- Next.js 14 (App Router)
- TypeScript
- Mapbox GL JS
- TanStack Table
- Zustand (상태관리)
- Tailwind CSS

### Backend
- FastAPI (Python)
- PostgreSQL + PostGIS
- Redis (캐시)
- Celery (비동기 작업)

### Infrastructure
- Vercel (프론트엔드)
- Fly.io (백엔드)
- Cloudflare (CDN/캐시)

## 📁 프로젝트 구조

```
PIXI/
├── frontend/          # Next.js 프론트엔드
├── backend/           # FastAPI 백엔드
├── data-pipeline/     # 데이터 수집/처리 파이프라인
├── docs/             # 프로젝트 문서
└── scripts/          # 유틸리티 스크립트
```

## 🚀 빠른 시작

### 1. 환경 변수 설정

#### Frontend (.env.local)
```bash
# frontend/.env.local 파일 생성
NEXT_PUBLIC_MAPBOX_TOKEN=your-mapbox-token-here
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
```

#### Backend (.env)
```bash
# backend/.env 파일 생성
DATABASE_URL=postgresql://user:password@localhost/pixi_db
REDIS_URL=redis://localhost:6379
MAPBOX_ACCESS_TOKEN=your-mapbox-token-here
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here  # AI 공동창업자 기능용
```

### 2. 데이터베이스 설정

```bash
# PostgreSQL 설치 및 데이터베이스 생성
createdb pixi_db

# PostGIS 확장 활성화
psql -d pixi_db -c "CREATE EXTENSION postgis;"
```

### 3. 프론트엔드 실행 (지도/탐색 페이지)

**로컬에서 "사이트에 연결할 수 없음" 오류가 나면** 개발 서버가 꺼져 있는 경우입니다. 아래처럼 실행한 뒤 브라우저에서 접속하세요.

```bash
cd frontend
npm install
npm run dev
```

실행 후 브라우저에서 접속:
- **메인 페이지**: http://localhost:3000
- **지도 탐색**: http://localhost:3000/explore
- **아이템 발굴**: http://localhost:3000/startup-idea
- **AI 공동창업자**: http://localhost:3000/cofounder

### 4. 백엔드 실행

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### 5. 데이터 파이프라인 실행 (선택사항)

```bash
cd data-pipeline
pip install -r requirements.txt

# Celery 워커 시작
celery -A schedulers.celery_app worker --loglevel=info

# Celery 비트 시작 (스케줄링)
celery -A schedulers.celery_app beat --loglevel=info
```

## 📊 데이터 모델

핵심 엔티티: Startup, Investor, Accelerator, Space, Event
- 위치 정보 (Geo)
- 펀딩 정보 (Funding rounds)
- 성장 시그널 (Growth signals)
- 채용 정보 (Hiring status)

## 🔄 개발 로드맵

### 완료된 기능
- ✅ 기본 맵 탐색, 엔티티 카드, 필터링
- ✅ AI 공동창업자 (5단계 가이드)
- ✅ 비주얼 캔버스
- ✅ 프로젝트 메모리 시스템
- ✅ 실제 시장 데이터 연동

### 향후 계획
- **R1 (3-6주)**: 성장 시그널, 채용 인사이트, 알림 시스템
- **R2**: 소셜 미디어 조사 통합 (Reddit, 네이버 카페)
- **R3**: 프로젝트 공유 및 협업 기능

## 🌐 API 문서

백엔드 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 개발 도구

### 프론트엔드 개발
```bash
cd frontend
npm run dev          # 개발 서버 시작
npm run build        # 프로덕션 빌드
npm run lint         # ESLint 실행
npm run type-check   # TypeScript 타입 체크
```

### 백엔드 개발
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pytest               # 테스트 실행
black .              # 코드 포맷팅
flake8 .             # 린팅
```

### 데이터베이스 관리
```bash
# Alembic 마이그레이션
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head

# 데이터베이스 백업
pg_dump pixi_db > backup.sql

# 데이터베이스 복원
psql pixi_db < backup.sql
```

## 🚨 문제 해결

### 일반적인 문제들

1. **Mapbox 토큰 오류**
   - Mapbox 계정에서 액세스 토큰 생성
   - frontend/.env.local에 토큰 설정

2. **데이터베이스 연결 오류**
   - PostgreSQL 서비스 실행 확인
   - 데이터베이스 URL 및 인증 정보 확인

3. **포트 충돌**
   - 8000번 포트 사용 중인 프로세스 확인
   - `lsof -i :8000` 또는 `netstat -an | grep 8000`

4. **의존성 설치 오류**
   - Python 버전 확인 (3.11+ 권장)
   - 가상환경 활성화 확인

## 📝 기여 가이드

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

MIT License

## 📞 지원

- GitHub Issues: [프로젝트 이슈 등록](https://github.com/your-username/pixi/issues)
- 이메일: support@pixi.com
- 문서: [프로젝트 위키](https://github.com/your-username/pixi/wiki)

---

**참고**: 이 프로젝트는 개발 중입니다. 최신 정보는 코드와 문서를 참조하세요.
