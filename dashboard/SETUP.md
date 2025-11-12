# Dashboard Setup Guide

리뷰 분석 대시보드 설치 및 실행 가이드입니다.

---

## 📋 Prerequisites

- **Python**: 3.9 이상
- **PostgreSQL**: 13 이상 (pgvector extension 필요)
- **Docker** (선택사항): PostgreSQL 설치를 간편하게 하려면 권장

---

## 🚀 Quick Start

### 1. 저장소 클론

```bash
git clone <repository-url>
cd ReviewFW_LG_hnh/dashboard
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

메인 프로젝트 루트의 `requirements.txt`를 사용하세요.

### 3. 환경변수 설정

#### Option A: Streamlit Secrets 사용 (권장)

`.streamlit/secrets.toml` 파일 생성:

```bash
# dashboard/.streamlit/ 디렉토리로 이동
cd .streamlit

# 예시 파일 복사
cp secrets.toml.example secrets.toml
```

`secrets.toml` 파일을 열고 실제 API 키 입력:

```toml
# Streamlit Secrets Configuration
GEMINI_API_KEY = "your-actual-gemini-api-key"
GOOGLE_API_KEY = "your-actual-google-api-key"
OPENAI_API_KEY = "your-actual-openai-api-key"
```

#### Option B: 환경변수 사용

`.env` 파일 생성:

```bash
# dashboard/ 디렉토리에서
cp .env.example .env
```

`.env` 파일을 열고 설정 입력:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cosmetic_reviews
DB_USER=postgres
DB_PASSWORD=your-secure-password

# API Keys
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key

# Optional: User Authentication
DASHBOARD_USERS=admin:securepass,user1:pass123
```

**Note**: `.env` 파일을 사용하는 경우 `python-dotenv`를 설치하고 `main.py`에서 로드해야 합니다.

```python
from dotenv import load_dotenv
load_dotenv()
```

### 4. PostgreSQL 데이터베이스 설정

#### Docker 사용 (권장)

프로젝트 루트에 `docker-compose.yml`이 있다면:

```bash
cd ..  # 프로젝트 루트로 이동
docker-compose up -d
```

#### 수동 설치

PostgreSQL 설치 후:

```sql
CREATE DATABASE cosmetic_reviews;
```

pgvector extension 설치:

```sql
CREATE EXTENSION vector;
```

데이터베이스에 데이터 임포트 (데이터 덤프 파일이 있는 경우):

```bash
psql -U postgres -d cosmetic_reviews < cosmetic_reviews_backup.sql
```

### 5. 대시보드 실행

```bash
cd dashboard
streamlit run main.py
```

브라우저가 자동으로 열리고 `http://localhost:8501`에서 대시보드에 접속할 수 있습니다.

---

## 🔑 API Keys 발급 방법

### Google Gemini API

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 방문
2. Google 계정으로 로그인
3. "Get API Key" 클릭
4. 생성된 API 키 복사

### OpenAI API

1. [OpenAI Platform](https://platform.openai.com/api-keys) 방문
2. OpenAI 계정으로 로그인
3. "Create new secret key" 클릭
4. 생성된 API 키 복사 (한 번만 표시됨)

---

## 📁 Project Structure

```
dashboard/
├── main.py                    # 로그인 엔트리 포인트
├── dashboard_config.py        # 전역 설정
├── pages/                     # 분석 페이지
│   ├── main_tab.py           # 메인 허브
│   ├── ai_chatbot_v6.py      # V6 AI 챗봇 (최신)
│   └── ...
├── ai_engines/
│   └── v6_langgraph_agent/   # V6 AI 엔진 (메인)
├── analyzer/                  # 통계 분석 모듈
├── utils/                     # 유틸리티
├── .streamlit/
│   ├── config.toml           # Streamlit 설정
│   ├── secrets.toml.example  # API 키 예시
│   └── secrets.toml          # 실제 API 키 (Git 제외)
├── .env.example              # 환경변수 예시
└── SETUP.md                  # 이 문서
```

---

## 🔐 Security Best Practices

### ⚠️ 중요: API 키 보호

1. **절대로 Git에 커밋하지 마세요**:
   - `secrets.toml`
   - `.env`
   - API 키가 포함된 모든 파일

2. `.gitignore` 확인:
   ```gitignore
   # .streamlit/secrets.toml은 이미 제외됨
   .streamlit/secrets.toml
   .env
   *.env
   ```

3. **API 키가 노출된 경우**:
   - 즉시 해당 API 키를 폐기하세요
   - 새 API 키를 발급받으세요
   - Git 히스토리에서 키를 제거하세요 (BFG Repo-Cleaner 사용)

### 사용자 인증 변경

기본 사용자 정보를 변경하려면:

1. 환경변수 사용:
   ```env
   DASHBOARD_USERS=admin:your-secure-password,user2:another-password
   ```

2. 또는 코드 수정:
   - `dashboard_config.py`의 `_load_users()` 함수 수정
   - `main.py`의 `_load_users()` 함수 수정

---

## 🐛 Troubleshooting

### PostgreSQL 연결 실패

**에러**: `psycopg2.OperationalError: could not connect to server`

**해결**:
1. PostgreSQL이 실행 중인지 확인
2. `.env` 또는 `secrets.toml`의 DB 설정 확인
3. 방화벽 설정 확인

### 한글 폰트 깨짐

**문제**: 워드클라우드나 차트에서 한글이 깨져 보임

**해결**:
- **Windows**: 시스템에 맑은 고딕 또는 나눔고딕 설치
- **macOS**: AppleGothic 폰트 자동 사용
- **Linux**: NanumGothic 설치
  ```bash
  sudo apt-get install fonts-nanum
  ```

### API 키 오류

**에러**: `Invalid API key` 또는 `401 Unauthorized`

**해결**:
1. API 키가 올바르게 입력되었는지 확인 (공백 없이)
2. API 키가 활성화되어 있는지 확인
3. API 사용량 한도를 초과하지 않았는지 확인

### 모듈 Import 에러

**에러**: `ModuleNotFoundError: No module named 'xxx'`

**해결**:
```bash
pip install -r requirements.txt --upgrade
```

---

## 🌐 Cross-Platform Support

이 대시보드는 다음 플랫폼에서 테스트되었습니다:

- ✅ Windows 10/11
- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (Ubuntu 20.04+)

### Platform-Specific Notes

**Windows**:
- 기본 폰트: 맑은 고딕
- Docker Desktop 권장

**macOS**:
- 기본 폰트: AppleGothic
- Homebrew로 PostgreSQL 설치 가능

**Linux**:
- NanumGothic 폰트 수동 설치 필요
- Docker 사용 권장

---

## 📞 Support

문제가 발생하면:

1. 이 가이드의 Troubleshooting 섹션 확인
2. GitHub Issues에 문제 보고
3. 프로젝트 문서 참조

---

## 📝 Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector Extension](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google Gemini API Documentation](https://ai.google.dev/docs)

---

**Last Updated**: 2025-01-12
**Version**: 1.0.0
