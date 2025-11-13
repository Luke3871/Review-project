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

**개요**: 통계 기반 리뷰 분석 엔진

**데이터 입력**:
- Pandas DataFrame (메모리 내 처리, DB 접근 없음)
- 필요 컬럼: `product_name`, `brand`, `channel`, `rating`, `review_text`, `review_date`

**분석 기능**:
1. **만족도 분석**: 평점 분포, 긍정/부정 비율 계산
2. **키워드 추출**: TF-IDF 기반, 평점별 분리 (긍정 4+, 부정 3-)
3. **시간 트렌드**: 월별 리뷰 수 추이 분석
4. **인사이트 생성**: 임계값 기반 규칙 (예: 평점 4.0+ → "높은 만족도")

**LLM 사용**: 없음

**특징**: 빠른 속도, 비용 없음, 통계 중심

---

### V2: LLM Report Generation

**개요**: GPT를 활용한 비즈니스 인사이트 생성 엔진

**데이터 입력**:
- Pandas DataFrame (V1과 동일)
- 필요 컬럼: `product_name`, `brand`, `channel`, `rating`, `review_text`, `review_date`

**분석 방식**:

**V2-A (데이터 직접 분석)**:
1. 통계 요약 생성: 리뷰 수, 평균 평점, 평점 분포, 긍정/부정 비율, 월별 트렌드, 주요 키워드
2. OpenAI API 호출 (GPT-4o-mini, temperature=0.7)
3. 프롬프트: "제품 강점, 만족도 패턴, 개선 기회, 시장 포지셔닝 분석"
4. 비즈니스 인사이트 보고서 생성 (max_tokens=2000)

**V2-B (키워드 해석)**:
1. V1에서 추출한 상위 20개 키워드 입력
2. OpenAI API 호출 (GPT-4o-mini, temperature=0.7)
3. 프롬프트: "키워드 패턴 분석, 제품 개선 방향, 마케팅 전략, 우선순위 액션"
4. 마케팅 전략 보고서 생성

**LLM 사용**:
- Model: GPT-4o-mini
- System Prompt: "화장품 리뷰 데이터 분석 전문가"
- Temperature: 0.7 (창의적 해석)

**특징**: 자연스러운 문장, 마케팅 관점 해석, V1 대비 깊이 있는 분석

**V1과의 차이**: 규칙 → LLM 기반, 통계 → 비즈니스 인사이트

---

### V3: Multi-Agent System

**개요**: 벡터 검색 기반 3-Agent 협업 시스템

**데이터 소스**:
- `reviews` 테이블 (PostgreSQL + pgvector)
- 필드: `review_id`, `product_name`, `brand`, `channel`, `category`, `rating`, `review_text`, `review_date`, `reviewer_skin_features`, `selected_option`, `embedding` (vector 1024차원)

**3-Agent 구조**:

**1. PlanningAgent**:
- 사용자 질문 분석
- 실행 계획 수립 (JSON 형식)
- LLM: GPT-4o-mini (temperature=0.1)
- 출력: `{"steps": [...], "answerable": true/false}`

**2. ExecutionAgent**:
- BGE-M3 모델로 질문 임베딩 생성 (1024차원)
- pgvector 코사인 유사도 검색 실행
- 필터 적용: brand, channel, category, min_rating, date_range, skin_features
- SQL: `SELECT * FROM reviews WHERE 1 - (embedding <=> query_vector) > threshold ORDER BY similarity LIMIT top_k`

**3. ResponseAgent**:
- 검색 결과 분석
- GPT-4o-mini로 최종 답변 생성 (마크다운)

**임베딩 모델**:
- BAAI/bge-m3 (로컬 실행)
- 1024차원 벡터
- 한글/영문 지원

**작동 흐름**:
```
질문 → PlanningAgent (계획) → ExecutionAgent (벡터 검색) → ResponseAgent (답변 생성)
```

**특징**: 의미 기반 검색, 대량 데이터 효율적 필터링

**V2와의 차이**: DataFrame → DB 벡터 검색, 단일 LLM → 3-Agent 협업

---

### V4: ReAct Agent

**개요**: ReAct 패턴 + 4단계 계층적 검색 + Map-Reduce 요약

**데이터 소스**:
- `reviews` 테이블 (PostgreSQL + pgvector)

**ReAct 패턴 (Reason + Act + Observation)**:

**THOUGHT 1: 질문 분석**
- QueryHandler: LLM으로 질문 파싱 (GPT-4o-mini, temperature=0.1)
- 추출: brands, keywords, channels, query_type (general/aspect/comparison 등)

**THOUGHT 2: 전략 선택**
- Playbook: 질문 타입에 따른 검색 전략 결정

**ACTION: 4단계 계층적 검색**

1. **Stage 1 - Vector 검색** (넓게):
   - BGE-M3 임베딩 생성
   - pgvector 검색: 최대 10,000건 추출

2. **Stage 2 - BM25 재정렬** (중간):
   - rank-bm25 라이브러리 사용
   - 키워드 매칭 점수 계산
   - 상위 1,000건 선택

3. **Stage 3 - Hybrid 최종선별** (좁게):
   - Hybrid Score = 0.7 × Vector Score + 0.3 × BM25 Score
   - 상위 200건 최종 선택

4. **Stage 4 - Map-Reduce 요약**:
   - Map: 200건을 20건씩 10개 청크로 분할 → 각 청크 요약 (GPT-4o-mini)
   - Reduce: 10개 요약을 최종 통합 (GPT-4o-mini)

**OBSERVATION: 결과 반환**
- 최종 요약 (2000 tokens)

**작동 흐름**:
```
질문 → QueryHandler (파싱) → Vector (10K) → BM25 (1K) → Hybrid (200) → Map-Reduce (요약)
```

**LLM 사용**:
- Query 파싱: GPT-4o-mini (temp=0.1)
- Map 요약: GPT-4o-mini (temp=0.3, max_tokens=800)
- Reduce 통합: GPT-4o-mini (temp=0.3, max_tokens=2000)

**특징**: 고정확도, 대량 데이터 효율 처리, 단계별 필터링

**V3와의 차이**: 단일 검색 → 4단계 계층적, 직접 요약 → Map-Reduce

---

### V5: LangGraph Basic

**개요**: LangGraph 기반 5-Node 순차 워크플로우 + 14개 Tool

**데이터 소스**:
- `preprocessed_reviews` 테이블 (PostgreSQL)

**5개 노드 (순차 실행)**:

**1. ParserNode**:
- LLM으로 질문 파싱 (GPT-4o-mini, temp=0.1)
- 추출: `{"brands": [...], "products": [...], "channels": [...], "intent": "attribute_analysis"}`
- 13가지 의도: attribute_analysis, sentiment_analysis, comparison, keyword_extraction, promotion_analysis, positioning_analysis, full_review, keyword_sentiment, pros_analysis, cons_analysis, complaint_analysis, motivation_analysis, comparison_mention

**2. ValidationNode**:
- DB 데이터 존재 확인
- SQL: `SELECT COUNT(*) FROM preprocessed_reviews WHERE brand IN (...) AND product_name IN (...)`
- 최소 리뷰 수 (MIN_REVIEW_COUNT=1) 체크
- 결과: `{"count": N, "sufficient": true/false}`

**3. RouterNode**:
- 의도 → Tool 매핑 (config.py의 INTENT_TO_TOOLS)
- 예: "attribute_analysis" → ["AttributeTool"]
- 예: "full_review" → ["AttributeTool", "SentimentTool", "ProsTool", "ConsTool", "PurchaseMotivationTool"]

**4. ExecutorNode**:
- 선택된 각 Tool 순차 실행
- 각 Tool은 preprocessed_reviews에서 SQL 쿼리 실행
- Tool 결과: `{"AttributeTool": {"status": "success", "data": {...}}, ...}`

**5. SynthesizerNode**:
- Tool 결과들을 종합
- GPT-4o로 최종 답변 생성 (temp=0.7)
- 마크다운 형식 출력

**14개 분석 Tool**:
1. AttributeTool: 속성별 만족도 (보습력, 발림성, 향, 가격 등)
2. SentimentTool: 긍정/부정 감성 분석
3. KeywordTool: 주요 키워드 추출
4. PositioningTool: 제품 포지셔닝 분석
5. ProductComparisonTool: 제품 비교
6. PromotionMentionTool: 기획/프로모션 언급
7. PromotionAnalysisTool: 기획 타입별 반응
8. ComparisonMentionTool: 타제품 언급 분석
9. KeywordSentimentTool: 키워드-감성 연계
10. ProsTool: 장점 분석
11. ConsTool: 단점 분석
12. ComplaintTool: 불만사항 분석
13. PurchaseMotivationTool: 구매동기 분석
14. ChannelCategoryTool: 채널별 카테고리 반응

**작동 흐름**:
```
질문 → Parser (의도 파악) → Validation (데이터 확인) → Router (Tool 선택) → Executor (Tool 실행) → Synthesizer (답변 생성)
```

**LLM 사용**:
- Parser: GPT-4o-mini (temp=0.1)
- Synthesizer: GPT-4o (temp=0.7)

**특징**: 모듈화된 Tool, 의도 기반 자동 선택, 선형 워크플로우

**V4와의 차이**: 검색 기반 → 구조화된 DB 쿼리, ReAct → LangGraph, Map-Reduce → Tool 조합

---

### V6: LangGraph Advanced (현재 메인 엔진)

**개요**: LangGraph 기반 12-Node 조건부 라우팅 워크플로우 + Text-to-SQL + 이미지 생성

**데이터 입력**:
- `preprocessed_reviews` 테이블 (5,000건 - GPT-4o-mini 분석 완료)
  - 컬럼: `brand`, `product_name`, `channel`, `rating`, `review_date`, `review_clean`, `analysis` (JSONB)
  - JSONB analysis 구조: `제품특성` (보습력, 발림성 등), `감정요약`, `장점`, `단점`, `구매동기`, `키워드`
- `reviews` 테이블 (314,285건 - 원본 리뷰)

**12개 노드 구성 (조건부 분기)**:

**[시작] EntityParser** (GPT-4o-mini, temp=0.0)
- 사용자 질문에서 브랜드/제품/속성/기간/채널 추출
- 대화 히스토리 맥락 반영 (최근 6개 메시지)
- 576개 브랜드 표준명 매핑 (`brand_list.txt`, `brand_mapping.txt`)
- **라우팅**: 이미지 생성 키워드 감지 시 → `ImagePromptGenerator`, 아니면 → `CapabilityDetector`

**[SQL 워크플로우 경로 - 총 9개 노드]**

1. **CapabilityDetector** (GPT-4o-mini, temp=0.0)
   - 시스템 처리 가능 여부 판단 (`data_scope`, `aggregation_type`)

2. **ComplexityClassifier** (GPT-4o-mini, temp=0.0)
   - 질문 복잡도 분류: `simple` / `medium` / `complex`
   - **라우팅**: `simple` → SQLGenerator 직행, `medium/complex` → QuestionDecomposer

3. **QuestionDecomposer** (GPT-4o-mini, temp=0.0)
   - 복잡한 질문을 여러 하위 질문으로 분해
   - 예: "빌리프와 VT 비교" → ["빌리프 리뷰 수집", "VT 리뷰 수집", "비교 분석"]

4. **SQLGenerator** (GPT-4o-mini, temp=0.0)
   - 각 하위 질문마다 SQL 쿼리 자동 생성
   - PostgreSQL Text-to-SQL 변환
   - JSONB 쿼리 자동 생성 (`analysis->'장점'`, `jsonb_array_elements_text()` 등)
   - 프롬프트: 494라인의 상세한 스키마 + 예시 6개 + 필터링 규칙
   - 브랜드명 필터: `WHERE brand = '브랜드명'`
   - 제품명 필터: `WHERE product_name LIKE '%제품명%'` (부분 매칭)

5. **Executor**
   - PostgreSQL에 SQL 실행
   - 결과 DataFrame 반환
   - **라우팅**: `complex` 질문이고 실패 쿼리 있으면 → SQLRefiner, 아니면 → ResponsePlanner

6. **SQLRefiner** (GPT-4o-mini, temp=0.0)
   - 실패한 쿼리를 에러 메시지 기반으로 재작성
   - 최대 1회 재시도

7. **ResponsePlanner** (GPT-4o-mini, temp=0.0)
   - 시각화 전략 결정 (`visualization_strategy`: `none` / `auto` / `suggest`)
   - Confidence 계산: `time_series` (0.7), `multi_comparison` (0.35), `distribution` (0.3) 등
   - Auto threshold: 0.7 이상이면 자동 시각화 생성

8. **OutputGenerator** (GPT-4o, temp=0.3)
   - SQL 결과를 자연어 요약 텍스트로 변환
   - 시각화 생성: Plotly 차트 (막대그래프, 선그래프, 히트맵 등)
   - 비교 테이블 생성 (브랜드/제품 비교 시)

9. **Synthesizer** (temp=0.3)
   - 최종 답변 통합 (텍스트 + 시각화 + 테이블 + 메타데이터)

**[이미지 생성 워크플로우 경로 - 3개 노드]**

10. **ImagePromptGenerator** (GPT-4o, temp=0.7)
    - 다이소 채널 리뷰 분석 → 디자인 키워드 추출
    - Gemini 2.5 Flash용 Image-to-Image 프롬프트 생성

11. **ImageGenerator** (Gemini 2.5 Flash Image)
    - 3가지 패키징 옵션 자동 생성:
      1. 7일치 샤쉐 파우치 (7ml)
      2. 3일 트라이얼 키트 (9ml)
      3. 10ml 미니 보틀
    - 원본 제품 이미지 → 다이소 최적화 디자인 변환
    - 저장 경로: `dashboard/generated_images/daiso/`

12. **Synthesizer** (공통)
    - SQL 워크플로우: 텍스트 + 시각화 통합
    - 이미지 워크플로우: 3개 이미지 + 설명 통합

**워크플로우 다이어그램**:
```
EntityParser → [이미지 키워드?]
   ├─ Yes → ImagePromptGenerator → ImageGenerator → Synthesizer
   └─ No  → CapabilityDetector → ComplexityClassifier → [복잡도?]
              ├─ simple → SQLGenerator
              └─ medium/complex → QuestionDecomposer → SQLGenerator
                                    ↓
                                 Executor → [실패 쿼리?]
                                    ├─ Yes (complex만) → SQLRefiner → ResponsePlanner
                                    └─ No → ResponsePlanner
                                               ↓
                                          OutputGenerator → Synthesizer
```

**LLM 사용**:
- **GPT-4o-mini** (temp=0.0): EntityParser, CapabilityDetector, ComplexityClassifier, QuestionDecomposer, SQLGenerator, SQLRefiner, ResponsePlanner
- **GPT-4o** (temp=0.3): OutputGenerator
- **GPT-4o** (temp=0.7): ImagePromptGenerator
- **Gemini 2.5 Flash Image**: ImageGenerator (Image-to-Image)

**SQL 생성 예시**:
```sql
-- 예시 1: 속성별 집계 (JSONB 쿼리)
SELECT
    brand,
    product_name,
    analysis->'제품특성'->>'보습력' as 보습력평가,
    COUNT(*) as review_count
FROM preprocessed_reviews
WHERE brand = '빌리프'
  AND product_name LIKE '%모이스춰라이징밤%'
  AND analysis->'제품특성'->'보습력' IS NOT NULL
GROUP BY brand, product_name, analysis->'제품특성'->>'보습력'
ORDER BY review_count DESC

-- 예시 2: 장점 키워드 빈도 (JSONB 배열 펼치기)
WITH advantage_keywords AS (
    SELECT
        jsonb_array_elements_text(analysis->'장점') as advantage,
        review_clean,
        rating
    FROM preprocessed_reviews
    WHERE brand = '빌리프'
      AND product_name LIKE '%모이스춰라이징밤%'
      AND jsonb_array_length(analysis->'장점') > 0
)
SELECT
    advantage,
    COUNT(*) as count,
    jsonb_agg(jsonb_build_object('review_clean', review_clean)) as samples
FROM advantage_keywords
GROUP BY advantage
ORDER BY count DESC
LIMIT 10
```

**V5 대비 개선점**:
- V5: 5-Node 순차, 14개 Tool 순차 실행 → V6: 12-Node 조건부 분기, 동적 SQL 생성
- V5: 고정된 Tool → V6: LLM이 자동으로 SQL 생성 (유연성 ↑)
- V5: 텍스트만 → V6: 텍스트 + 이미지 생성 (멀티모달)
- V5: 단일 워크플로우 → V6: SQL / 이미지 생성 워크플로우 자동 라우팅
- V6: 복잡도별 최적화 (simple 질문은 QuestionDecomposer 스킵)

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
