# PIXI 데이터 파이프라인

전 세계 스타트업 생태계 데이터를 수집, 처리, 분석하는 파이프라인입니다.

## 🏗 구조

```
data-pipeline/
├── scrapers/          # 웹 스크래핑 모듈
├── processors/        # 데이터 처리 및 정규화
├── enrichers/         # 데이터 보강 (위치, 태깅 등)
├── analyzers/         # 성장 시그널 분석
├── schedulers/        # 작업 스케줄링
└── utils/             # 유틸리티 함수
```

## 🚀 주요 기능

### 1. 데이터 수집 (Scrapers)
- **공개 데이터**: 정부/지자체 스타트업 명단
- **퍼미션드 API**: 스타트업 단체, 코워킹, 액셀러레이터 네트워크
- **웹 크롤링**: 회사 웹사이트, 채용 페이지, 블로그, 깃허브
- **사용자 제보**: 창업자/운영자 직접 수정

### 2. 데이터 처리 (Processors)
- **정규화**: Pydantic 모델로 스키마 표준화
- **중복 제거**: 회사명, 웹사이트 기반 중복 검사
- **품질 검증**: 필수 필드 검증 및 데이터 정합성 확인

### 3. 데이터 보강 (Enrichers)
- **지리 정보**: 주소 → 좌표 변환 (Geocoding)
- **도메인 태깅**: LLM + 룰 기반 카테고리 분류
- **펀딩 정보**: Crunchbase, 투자 뉴스 크롤링
- **채용 정보**: 채용 페이지 스크래핑

### 4. 성장 시그널 분석 (Analyzers)
- **웹 트래픽**: SimilarWeb, Google Trends 데이터
- **깃허브 활동**: 스타, 커밋, 릴리즈 빈도
- **채용 강도**: 채용 공고 수, 직군 분포
- **PR 빈도**: 뉴스 기사, 소셜 미디어 언급

## 📊 데이터 모델

### 핵심 엔티티
```python
class Entity:
    id: int
    type: Literal["startup", "investor", "accelerator", "space", "event"]
    name: str
    description: Optional[str]
    website: Optional[str]
    domains: List[str]
    founded_year: Optional[int]
    
    # 위치 정보
    country: Optional[str]
    city: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    
    # 펀딩 정보
    funding_rounds: List[FundingRound]
    
    # 인력 정보
    headcount_estimate: Optional[int]
    headcount_growth_12m_pct: Optional[float]
    
    # 채용 정보
    is_hiring: bool
    hiring_roles: List[str]
    remote_ratio: Optional[float]
    
    # 성장 시그널
    growth_score: Optional[float]
    signals: Dict[str, Any]
```

## 🔄 워크플로우

### 1. 일일 수집 (Daily Collection)
```bash
# 스케줄러 실행
python -m schedulers.daily_collector

# 주요 작업:
# - 새로운 회사 웹사이트 스크래핑
# - 채용 페이지 업데이트 확인
# - 펀딩 뉴스 모니터링
# - 깃허브 활동 추적
```

### 2. 주간 분석 (Weekly Analysis)
```bash
# 성장 시그널 계산
python -m analyzers.growth_signal_calculator

# 주요 작업:
# - 웹 트래픽 트렌드 분석
# - 깃허브 활동 점수 계산
# - 채용 강도 측정
# - 종합 성장 점수 산출
```

### 3. 월간 정리 (Monthly Cleanup)
```bash
# 데이터 품질 관리
python -m processors.data_quality_manager

# 주요 작업:
# - 중복 데이터 정리
# - 품질 점수 낮은 데이터 플래그
# - 사용자 제보 데이터 검증
# - 아카이브 데이터 관리
```

## 🛠 기술 스택

- **Python 3.11+**: 메인 언어
- **Playwright**: 안정적인 웹 스크래핑
- **BeautifulSoup4**: HTML 파싱
- **Pandas**: 데이터 처리 및 분석
- **Celery**: 비동기 작업 큐
- **Redis**: 캐시 및 작업 상태 관리
- **PostgreSQL**: 메인 데이터베이스
- **Pydantic**: 데이터 검증 및 직렬화

## 📋 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# 필요한 값 설정:
# - DATABASE_URL
# - REDIS_URL
# - CRUNCHBASE_API_KEY
# - SIMILARWEB_API_KEY
# - GOOGLE_TRENDS_API_KEY
```

### 3. 데이터베이스 초기화
```bash
python -m utils.db_init
```

### 4. 스케줄러 실행
```bash
# Celery 워커 시작
celery -A schedulers.celery_app worker --loglevel=info

# Celery 비트 시작 (스케줄링)
celery -A schedulers.celery_app beat --loglevel=info
```

### 5. 투자자·액셀러레이터 대량 크롤링 후 지도 표시
```bash
# data-pipeline 디렉터리에서 실행
cd data-pipeline
python run_bulk_crawler.py
```
- **더브이씨(THE VC)** 투자자 목록을 스크롤하며 전량 수집 (수천 건)
- **액셀러레이터** 확장 목록(40여 개) 병합
- 완료 후 `export_for_frontend`가 `frontend/public/data/koreanEcosystemData.json`을 갱신
- 브라우저에서 `/explore` 페이지를 새로 고침하면 지도에 반영됨

## 📈 모니터링

### 1. 작업 상태 모니터링
```bash
# Celery Flower (웹 UI)
celery -A schedulers.celery_app flower

# 작업 로그 확인
tail -f logs/celery.log
```

### 2. 데이터 품질 모니터링
```bash
# 데이터 품질 리포트 생성
python -m utils.quality_report

# 주요 메트릭:
# - 수집 성공률
# - 데이터 완성도
# - 중복률
# - 최신성
```

## 🔒 보안 및 규정 준수

### 1. 웹 크롤링 규정
- `robots.txt` 준수
- 요청 속도 제한 (초당 1-2회)
- User-Agent 명시
- 캐시 활용으로 서버 부하 최소화

### 2. 데이터 개인정보 보호
- 개인 이메일/전화번호 수집 금지
- 공개 기업 데이터만 수집
- 데이터 삭제 요청 처리 경로 마련

### 3. API 사용 정책
- 공식 API 우선 사용
- Rate limiting 준수
- 사용량 모니터링
- 비용 효율적 사용

## 🚨 문제 해결

### 일반적인 문제들

1. **스크래핑 실패**
   - 웹사이트 구조 변경 확인
   - IP 차단 여부 확인
   - User-Agent 업데이트

2. **데이터 품질 저하**
   - 소스 데이터 검증
   - 파싱 로직 점검
   - 수동 검토 필요 데이터 플래그

3. **성능 이슈**
   - 병렬 처리 최적화
   - 캐시 활용도 증가
   - 데이터베이스 인덱스 최적화

## 📞 지원

문제가 발생하거나 개선 제안이 있으시면:
- GitHub Issues 등록
- 개발팀 이메일 연락
- 문서 업데이트 PR 제출

---

**참고**: 이 파이프라인은 지속적으로 개선되고 있습니다. 최신 정보는 코드와 문서를 참조하세요.
