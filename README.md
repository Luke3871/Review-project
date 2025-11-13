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
# 1. 저장소 클론
git clone https://github.com/Luke3871/Review-project.git
cd ReviewFW_LG_hnh

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정 (선택사항)
cp .env.example .env
# .env 파일을 열고 필요시 DB 비밀번호 수정

# 4. 데이터베이스 실행 (Docker)
docker-compose up -d

# 5. 데이터 복원
# 구글 드라이브에서 백업 파일(cosmetic_reviews_backup_20251113.sql.gz)을 다운로드하여 프로젝트 루트에 배치

# Docker 컨테이너 준비 대기 (10초 정도)
# Windows: docker ps | findstr pgvec
# macOS/Linux: docker ps | grep pgvec

# Windows (PowerShell/CMD): 먼저 압축 해제 후 복원
# gunzip cosmetic_reviews_backup_20251113.sql.gz
# docker exec -i pgvec psql -U postgres cosmetic_reviews < cosmetic_reviews_backup_20251113.sql

# Windows (Git Bash) 또는 macOS/Linux: 한 번에 복원
gunzip < cosmetic_reviews_backup_20251113.sql.gz | docker exec -i pgvec psql -U postgres cosmetic_reviews

# 6. API 키 설정
cd dashboard/.streamlit
cp secrets.toml.example secrets.toml
# secrets.toml 파일을 열고 API 키 입력

# 7. 대시보드 실행
cd ../
streamlit run main.py
```

브라우저에서 `http://localhost:8501` 접속

### 데이터 다운로드

리뷰 데이터(314,285건)는 용량이 커서 별도로 제공됩니다:

**구글 드라이브**:
- [DB 백업 파일 다운로드](https://drive.google.com/file/d/1TbibsQ1RcKGwkDGH6pGkVWQjdVrUdSqs/view?usp=sharing) (필수, 1.6GB)
  - 파일명: `cosmetic_reviews_backup_20251113.sql.gz`
  - 포함: reviews 테이블, preprocessed_reviews 테이블
  - 다운로드 후 **프로젝트 루트 디렉토리**(`ReviewFW_LG_hnh/`)에 배치
- [리뷰 이미지 파일 다운로드](https://drive.google.com/file/d/1cUSjNwkzJVXz--kvQQ0ujjC2bvz_Dhyt/view?usp=sharing) (선택, 2MB)

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

### V1: Rule-based Analysis

**개요**: 통계 기반 규칙으로 리뷰 분석 및 인사이트 생성

**데이터 소스**:
- `preprocessed_reviews` 테이블 사용
- 컬럼: `rating`, `pros_cons`, `attributes`, `emotions` 등

**작동 방식**:
1. DB에서 제품별 리뷰 데이터 집계
2. 규칙 기반 통계 계산 (평균 평점, 속성별 만족도)
3. 임계값 기반 인사이트 생성 (예: 평점 4.0 이상 → "높은 만족도")
4. 템플릿 기반 리포트 출력

**특징**: 빠르고 안정적이나 맥락 이해 제한적

---

### V2: LLM Report Generation

**개요**: GPT를 활용한 비즈니스 인사이트 생성

**데이터 소스**:
- `preprocessed_reviews` 테이블 직접 조회
- 또는 V1 분석 결과를 입력으로 사용

**작동 방식**:
- **V2-A (데이터 직접 분석)**:
  1. SQL로 리뷰 데이터 추출
  2. 데이터를 LLM 프롬프트에 삽입
  3. GPT가 비즈니스 인사이트 생성

- **V2-B (키워드 해석)**:
  1. V1 결과 (키워드, 통계)를 LLM에 전달
  2. LLM이 마케팅 관점에서 해석 및 전략 제안

**특징**: 자연스러운 분석 보고서, 맥락 이해 향상

---

### V3: Multi-Agent System

**개요**: 3개의 전문 에이전트가 협력하여 분석 수행

**데이터 소스**:
- `preprocessed_reviews` 테이블
- pgvector 확장으로 벡터 임베딩 검색

**구조**:
1. **PlanningAgent**: 사용자 질문을 분석하고 실행 계획 수립
2. **ExecutionAgent**: 계획에 따라 DB 쿼리 및 벡터 검색 실행
3. **ResponseAgent**: 결과를 종합하여 최종 응답 생성

**작동 방식**:
- 벡터 검색으로 의미적으로 유사한 리뷰 탐색
- SQL과 벡터 검색 결과를 결합하여 분석
- 에이전트 간 메시지 전달로 협업

**특징**: 복잡한 질문 처리 가능, 벡터 검색 활용

---

### V4: ReAct Agent

**개요**: 계층적 검색과 Map-Reduce 패턴으로 고품질 인사이트 생성

**데이터 소스**:
- `preprocessed_reviews` 테이블
- Vector/BM25/Hybrid 검색 지원

**핵심 컴포넌트**:
- **QueryHandler**: LLM으로 자연어 쿼리 파싱
- **HierarchicalRetrieval**: 3단계 검색 전략
  1. 키워드 기반 필터링
  2. 벡터 유사도 검색
  3. BM25 키워드 매칭
- **Map-Reduce**: 개별 리뷰 분석 후 통합 요약

**작동 방식**:
1. 사용자 질문 분석 (ReAct 패턴)
2. 검색 도구 선택 및 실행
3. Map: 각 리뷰에서 인사이트 추출
4. Reduce: 전체 인사이트 통합 및 요약

**특징**: 정확도 향상, 대량 리뷰 효율적 처리

---

### V5: LangGraph Basic

**개요**: LangGraph 프레임워크 기반 5개 노드 워크플로우

**데이터 소스**:
- `preprocessed_reviews` 테이블 전용 SQL 쿼리

**노드 구조**:
1. **Parser**: 사용자 질문에서 브랜드/제품/채널/의도 추출
2. **Validation**: 데이터 존재 여부 검증
3. **Router**: 의도에 따라 14개 분석 도구 선택
4. **Executor**: 선택된 도구로 DB 쿼리 실행
5. **Synthesizer**: LLM으로 최종 응답 생성

**14개 분석 도구**:
- AttributeTool, SentimentTool, KeywordTool
- ProductComparisonTool, PromotionMentionTool
- ProsTool, ConsTool, ComplaintTool
- PurchaseMotivationTool 등

**작동 방식**:
```
START → Parser → Validation → Router → Executor → Synthesizer → END
```

**특징**: 모듈화된 구조, 의도 기반 분석 도구 자동 선택

---

### V6: LangGraph Advanced (현재 메인 엔진)

**개요**: Text-to-SQL + 이미지 생성 통합 멀티모달 분석 시스템

**데이터 소스**:
- `reviews` 테이블 (원본 리뷰 텍스트)
- `preprocessed_reviews` 테이블 (전처리된 분석 데이터)
- 두 테이블을 조인하여 활용

**12개 노드 워크플로우**:

**[SQL 분석 경로]**
1. **EntityParser**: 브랜드/제품/채널 엔티티 추출
2. **CapabilityDetector**: 시스템 처리 가능 여부 판단
3. **ComplexityClassifier**: 질문 복잡도 분류 (단순/복잡)
4. **QuestionDecomposer**: 복잡한 질문을 하위 질문으로 분해
5. **SQLGenerator**: 자연어 → SQL 쿼리 자동 생성
6. **Executor**: SQL 실행 및 결과 반환
7. **SQLRefiner**: 결과 부족 시 쿼리 개선
8. **ResponsePlanner**: 응답 구조 계획 (차트/텍스트)
9. **OutputGenerator**: 시각화 및 데이터 포맷팅
10. **Synthesizer**: 최종 마크다운 응답 생성

**[이미지 생성 경로]**
1. **EntityParser**: 제품 정보 추출
2. **ImagePromptGenerator**: 제품 디자인 프롬프트 생성
3. **ImageGenerator**: Gemini API로 이미지 생성
4. **Synthesizer**: 이미지와 설명 통합

**핵심 기능**:

**Text-to-SQL**:
- 자연어 질문을 PostgreSQL 쿼리로 자동 변환
- 복잡한 JOIN, GROUP BY, HAVING 절 생성
- 예: "토리든 보습력 좋아?" → `SELECT AVG(attribute_moisture) FROM preprocessed_reviews WHERE brand='토리든'`

**적응형 워크플로우**:
- 질문 복잡도에 따라 분해 여부 결정
- SQL 실행 결과가 불충분하면 자동 재생성

**멀티모달 출력**:
- 텍스트 분석 + 차트 시각화
- 제품 패키징 디자인 생성 (예: "VT 다이소 버전 디자인")

**작동 예시**:
```
질문: "올리브영에서 보습력 좋은 제품 추천해줘"

1. EntityParser: 채널=올리브영, 속성=보습력 추출
2. CapabilityDetector: 처리 가능 확인
3. ComplexityClassifier: 단순 질문
4. SQLGenerator:
   SELECT brand, product_name, AVG(attribute_moisture) as moisture_score
   FROM preprocessed_reviews
   WHERE channel='OliveYoung' AND attribute_moisture > 3
   GROUP BY brand, product_name
   ORDER BY moisture_score DESC
   LIMIT 10
5. Executor: 쿼리 실행
6. ResponsePlanner: 표 + 바 차트 계획
7. OutputGenerator: 데이터 포맷팅
8. Synthesizer: "올리브영 보습력 TOP 10 제품..." 생성
```

**특징**:
- 가장 고도화된 엔진
- 동적 SQL 생성으로 유연한 분석
- 이미지 생성으로 창의적 활용
- 에러 복구 및 자동 개선

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
