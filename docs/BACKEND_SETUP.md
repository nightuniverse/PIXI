# 백엔드 서버 실행 가이드

AI 공동창업자 기능을 사용하려면 백엔드 서버가 실행 중이어야 합니다.

## 빠른 시작

### 1. 가상환경 활성화

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 2. 의존성 설치 (처음 한 번만)

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일이 있는지 확인하고, 없으면 `.env.example`을 복사하세요:

```bash
cp .env.example .env
```

`.env` 파일에 다음이 설정되어 있어야 합니다:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### 4. 서버 실행

```bash
uvicorn main:app --reload
```

서버가 성공적으로 시작되면 다음 메시지가 표시됩니다:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 5. 서버 확인

브라우저에서 다음 URL을 열어 서버가 정상 작동하는지 확인하세요:

- http://localhost:8000 - API 루트
- http://localhost:8000/docs - Swagger UI (API 문서)
- http://localhost:8000/health - 헬스 체크

## 문제 해결

### 404 Not Found 오류가 발생하는 경우

**원인**: 백엔드 서버가 코드 변경사항을 반영하지 않았거나, `social_research` 모듈 import 오류로 인해 라우터가 로드되지 않았을 수 있습니다.

**해결 방법**:

1. **서버 재시작**:
   ```bash
   # 실행 중인 서버 종료 (Ctrl+C)
   # 그 다음 다시 시작
   uvicorn main:app --reload
   ```

2. **또는 스크립트 사용**:
   ```bash
   ./restart_server.sh
   ```

3. **서버가 제대로 시작되었는지 확인**:
   ```bash
   curl http://localhost:8000/health
   # 또는 브라우저에서 http://localhost:8000/docs 열기
   ```

4. **라우터가 등록되었는지 확인**:
   브라우저에서 http://localhost:8000/docs 를 열어 `/api/v1/cofounder/chat` 엔드포인트가 보이는지 확인하세요.

### 포트 8000이 이미 사용 중인 경우

다른 포트로 실행:

```bash
uvicorn main:app --reload --port 8001
```

그리고 프론트엔드의 `.env.local` 파일에 다음을 추가:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

### 가상환경이 없는 경우

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # 또는 venv\Scripts\activate (Windows)
pip install -r requirements.txt
```

### OPENAI_API_KEY 오류

`.env` 파일에 올바른 OpenAI API 키가 설정되어 있는지 확인하세요:

```bash
# backend/.env
OPENAI_API_KEY=sk-proj-...
```

### 모듈을 찾을 수 없는 오류

의존성이 설치되지 않았을 수 있습니다:

```bash
pip install -r requirements.txt
```

## 자동 실행 스크립트 (선택사항)

`backend/start.sh` 파일을 생성하여 편리하게 실행할 수 있습니다:

```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn main:app --reload
```

실행 권한 부여:

```bash
chmod +x backend/start.sh
```

실행:

```bash
./backend/start.sh
```

## 프로덕션 실행

프로덕션 환경에서는 `--reload` 옵션 없이 실행:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

또는 Gunicorn 사용:

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
