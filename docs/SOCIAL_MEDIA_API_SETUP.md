# 소셜 미디어 API 설정 가이드

AI 공동창업자 서비스에서 실제 사용자 니즈를 조사하기 위해 Reddit과 네이버 검색 API를 활용합니다.

## 1. Reddit API 설정

### 발급 방법
1. https://www.reddit.com/prefs/apps 접속
2. "create another app..." 클릭
3. 앱 정보 입력:
   - **name**: PIXI Startup Research (원하는 이름)
   - **type**: script 선택
   - **description**: Startup research bot (선택사항)
   - **redirect uri**: `http://localhost:8000` (개발용)
4. "create app" 클릭
5. 발급된 정보 확인:
   - **client_id**: 앱 이름 아래에 있는 문자열 (14자)
   - **client_secret**: "secret" 옆의 문자열

### 환경 변수 설정
```bash
REDDIT_CLIENT_ID=your-client-id-here
REDDIT_CLIENT_SECRET=your-client-secret-here
```

### 사용 제한
- **무료 사용 가능**: Reddit API는 무료로 사용 가능합니다
- **Rate Limit**: 분당 60회 요청 제한
- **상업적 사용**: 상업적 목적의 사용은 Reddit 승인이 필요할 수 있습니다

## 2. 네이버 검색 API 설정

### 발급 방법
1. https://developers.naver.com/apps/#/register 접속
2. 네이버 계정으로 로그인
3. "Application 등록" 클릭
4. 앱 정보 입력:
   - **애플리케이션 이름**: PIXI Startup Research
   - **사용 API**: 검색 API 선택
   - **비로그인 오픈API 서비스 환경**: Web 설정
   - **서비스 URL**: `http://localhost:3000` (개발용)
5. 등록 완료 후 발급된 정보 확인:
   - **Client ID**: 애플리케이션 정보에서 확인
   - **Client Secret**: 애플리케이션 정보에서 확인

### 환경 변수 설정
```bash
NAVER_CLIENT_ID=your-client-id-here
NAVER_CLIENT_SECRET=your-client-secret-here
```

### 사용 제한
- **일일 호출 한도**: 25,000회/일
- **무료 사용 가능**: 네이버 검색 API는 무료로 제공됩니다
- **카페 글 검색**: 공개된 카페 게시글만 검색 가능

## 3. 기능 설명

### 소셜 미디어 조사 기능
- **Reddit 검색**: 전 세계 사용자들의 실제 니즈와 문제점 파악
- **네이버 카페 검색**: 한국 시장의 실제 사용자 니즈 조사
- **자동 통합**: AI 공동창업자의 "조사(research)" 단계에서 자동으로 활용

### API 엔드포인트

#### 1. 소셜 미디어 검색
```bash
GET /api/v1/social-research/search?query=창업&source=all&limit=10
```

**파라미터:**
- `query`: 검색어 (필수)
- `source`: 소스 선택 (`reddit`, `naver_cafe`, `all`) - 기본값: `all`
- `limit`: 결과 개수 (1-50) - 기본값: 10

**응답 예시:**
```json
{
  "query": "창업",
  "source": "all",
  "count": 10,
  "results": [
    {
      "title": "스타트업 창업 후기",
      "content": "...",
      "url": "https://...",
      "source": "reddit",
      "score": 150,
      "comments": 45
    }
  ]
}
```

#### 2. 주제 종합 조사
```bash
POST /api/v1/social-research/research?topic=핀테크&keywords=금융,결제
```

**파라미터:**
- `topic`: 조사 주제 (필수)
- `keywords`: 추가 키워드 리스트 (선택)

**응답 예시:**
```json
{
  "total_results": 25,
  "reddit_count": 15,
  "naver_cafe_count": 10,
  "results": [...],
  "summary": "..."
}
```

## 4. AI 공동창업자 서비스 통합

소셜 미디어 조사 기능은 AI 공동창업자 서비스의 **조사(research) 단계**에서 자동으로 활용됩니다:

1. 사용자가 문제를 정의하면 (`idea` 단계 완료)
2. `research` 단계로 자동 전환
3. 정의된 문제를 키워드로 Reddit과 네이버 카페에서 검색
4. 검색 결과를 GPT-4o에 전달하여 실제 사용자 니즈 분석
5. 분석 결과를 바탕으로 구체적인 시장 검증 인사이트 제공

## 5. 주의사항

### Rate Limit 관리
- Reddit: 분당 60회 요청 제한
- 네이버: 일일 25,000회 제한
- 서비스에서 자동으로 요청 간격을 조절합니다

### 데이터 사용
- Reddit과 네이버 카페의 공개 데이터만 사용합니다
- 개인정보는 수집하지 않습니다
- 검색 결과는 분석 목적으로만 사용됩니다

### API 키 보안
- `.env` 파일에 API 키를 저장하세요
- `.env` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 포함됨)
- 프로덕션 환경에서는 환경 변수로 관리하세요

## 6. 테스트

API 키를 설정한 후, 다음 명령어로 테스트할 수 있습니다:

```bash
# Reddit 검색 테스트
curl "http://localhost:8000/api/v1/social-research/search?query=startup&source=reddit&limit=5"

# 네이버 카페 검색 테스트
curl "http://localhost:8000/api/v1/social-research/search?query=창업&source=naver_cafe&limit=5"

# 종합 조사 테스트
curl -X POST "http://localhost:8000/api/v1/social-research/research?topic=핀테크"
```

## 7. 문제 해결

### Reddit API 오류
- **"Invalid credentials"**: Client ID와 Secret을 확인하세요
- **"Rate limit exceeded"**: 요청 간격을 늘리세요 (현재 1초 대기)

### 네이버 API 오류
- **"Invalid client"**: Client ID와 Secret을 확인하세요
- **"API 호출 한도 초과"**: 일일 한도를 확인하세요 (25,000회)

### API 키 없이 사용하기
API 키가 없어도 서비스는 정상 작동합니다. 다만 소셜 미디어 조사 기능은 비활성화되며, GPT-4o만으로 분석을 수행합니다.
