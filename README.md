# Korean Cosmetics Review Analysis Framework

한국 화장품 리뷰 데이터 분석 프레임워크

---

## 개요

한국 주요 이커머스 플랫폼(쿠팡, 다이소, 올리브영)의 화장품 리뷰를 수집하고 AI 기반 분석을 제공하는 시스템입니다.

### 주요 기능

- 자동 리뷰 수집 (314,285건)
- V6 LangGraph 기반 AI 분석 엔진
- Streamlit 인터랙티브 대시보드
- 자연어 질의 및 자동 시각화
- 제품 패키징 디자인 생성

---

## 설치

### 필수 요구사항

- Python 3.9+
- PostgreSQL 13+ (pgvector extension)
- Docker (선택)

### 설치 방법

```bash
# 저장소 클론
git clone https://github.com/Luke3871/Review-project.git
cd ReviewFW_LG_hnh

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (선택사항)
cp .env.example .env
# .env 파일을 열고 필요시 DB 비밀번호 수정

# 데이터베이스 실행 (Docker)
docker-compose up -d

# API 키 설정
cd dashboard/.streamlit
cp secrets.toml.example secrets.toml
# secrets.toml 파일을 열고 API 키 입력

# 대시보드 실행
cd dashboard
streamlit run main.py
```

브라우저에서 `http://localhost:8501` 접속

---

## API 키 설정

`dashboard/.streamlit/secrets.toml` 파일에 다음 키를 입력하세요:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
GOOGLE_API_KEY = "your-google-api-key"
OPENAI_API_KEY = "your-openai-api-key"
```

**API 키 발급:**
- Google Gemini: https://makersuite.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys

---

## 사용 예시

### AI 챗봇 질의

```
"토리든 전반적으로 어때?"
"올리브영에서 보습력 좋은 제품 추천해줘"
"라운드랩이랑 토리든 비교해줘"
"VT 다이소 버전 디자인 만들어줘"
```

---

## 프로젝트 구조

```
ReviewFW_LG_hnh/
├── collector/              # 리뷰 수집 시스템
├── dashboard/              # Streamlit 대시보드
│   ├── main.py            # 진입점
│   ├── pages/             # 분석 페이지
│   ├── ai_engines/        # AI 엔진 (v1-v6)
│   │   └── v6_langgraph_agent/  # 메인 엔진
│   └── .streamlit/        # 설정 및 API 키
├── preprocessor2/         # 데이터 전처리
└── docker-compose.yml     # PostgreSQL 설정
```

---

## 데이터

- 총 리뷰: 314,285건
- 채널: 쿠팡, 다이소, 올리브영
- 브랜드: 576개
- 카테고리: 34개 (스킨케어, 메이크업 등)

---

## AI 엔진 버전

| 버전 | 특징 |
|------|------|
| V1 | Rule-based |
| V2 | LLM Report |
| V3 | Multi-Agent |
| V4 | ReAct Agent |
| V5 | LangGraph Basic |
| **V6** | **LangGraph Advanced + Image Generation** |

---

## 환경변수

`.env.example` 파일을 `.env`로 복사하여 사용하세요.

```env
# Database (docker-compose.yml에서 사용)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cosmetic_reviews
DB_USER=postgres
DB_PASSWORD=postgres

# API Keys (dashboard/.streamlit/secrets.toml에서도 설정 필요)
GEMINI_API_KEY=your-key
GOOGLE_API_KEY=your-key
OPENAI_API_KEY=your-key
```

**참고**: `.env` 파일은 로컬 개발용이며, 프로덕션 환경에서는 반드시 강력한 비밀번호로 변경하세요.

---

## 추가 문서

- [dashboard/SETUP.md](dashboard/SETUP.md) - 상세 설치 가이드
- [DATABASE_TRANSFER_GUIDE.md](DATABASE_TRANSFER_GUIDE.md) - DB 마이그레이션 가이드

---

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

---

**Last Updated**: 2025-11-13
