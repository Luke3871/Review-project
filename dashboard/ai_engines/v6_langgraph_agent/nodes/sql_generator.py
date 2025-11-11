#//==============================================================================//#
"""
sql_generator.py
동적 SQL 생성 (각 sub-question마다)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import logging
from typing import Dict, Any, List
from openai import OpenAI

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import LLM_CONFIG
from ..errors import handle_exception, SQLGenerationError, LLMError
from ..state_validator import validate_state, validate_sql_query_structure

# 로거 설정
logger = logging.getLogger("v6_agent.sql_generator")


class SQLGenerator:
    """SQL 동적 생성"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["sql_generator"]  # 0.0
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def generate(self, state: AgentState) -> AgentState:
        """
        SQL 생성 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 로깅
            logger.info("SQLGenerator 시작")
            logger.debug(f"sub_questions: {state.get('sub_questions')}")
            logger.debug(f"parsed_entities: {state.get('parsed_entities')}")
            logger.debug(f"capabilities: {state.get('capabilities')}")

            # 1. 단계 시작
            sub_questions = state.get("sub_questions", [])

            # sub_questions 없으면 user_query를 기본 질문으로 사용
            if not sub_questions:
                logger.info("sub_questions 없음, fallback 사용")
                sub_questions = [{
                    "sub_question": state["user_query"],
                    "purpose": "단일 질문",
                    "dependency": None
                }]

            logger.info(f"최종 sub_questions 개수: {len(sub_questions)}")

            tracker.start_step(
                node_name="SQLGenerator",
                description="SQL 쿼리 생성 중...",
                substeps=[f"Q{i+1} SQL 생성" for i in range(len(sub_questions))]
            )

            # 2. 각 sub-question마다 SQL 생성
            sql_queries = []
            sql_metadata = []  # UI 표시용 SQL 메타데이터

            for i, sub_q in enumerate(sub_questions, 1):
                logger.debug(f"Q{i} SQL 생성 시작: {sub_q['sub_question']}")

                sql_info = self._generate_sql(
                    sub_q,
                    state["parsed_entities"],
                    state["capabilities"],
                    state  # Debug 추적을 위해 state 전달
                )

                sql_info["question_id"] = i
                sql_info["sub_question"] = sub_q["sub_question"]
                sql_queries.append(sql_info)

                # SQL 메타데이터 저장 (UI 표시용)
                sql_metadata.append({
                    "question_id": i,
                    "sub_question": sub_q["sub_question"],
                    "sql": sql_info["sql"],
                    "purpose": sql_info["purpose"],
                    "explanation": sql_info["explanation"],
                    "estimated_rows": sql_info["estimated_rows"]
                })

                logger.info(f"Q{i} SQL 생성 완료 (예상 {sql_info['estimated_rows']}건)")
                logger.debug(f"Q{i} SQL: {sql_info['sql'][:150]}...")
                tracker.update_substep(f"Q{i} SQL 생성 완료 (예상 {sql_info['estimated_rows']}건)")

            tracker.complete_step(summary=f"{len(sql_queries)}개 SQL 생성 완료")

            # State 업데이트
            state["sql_queries"] = sql_queries
            state["sql_metadata"] = sql_metadata  # UI용 메타데이터 추가
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "sql_generator")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"SQL 생성 성공: {len(sql_queries)}개 쿼리")
                    # 각 SQL 구조 검증
                    for i, sql_q in enumerate(sql_queries, 1):
                        sql_errors = validate_sql_query_structure(sql_q)
                        if sql_errors:
                            logger.warning(f"Q{i} SQL 구조 검증 경고: {sql_errors}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except json.JSONDecodeError as e:
            # JSON 파싱 실패 (LLM 출력 형식 오류)
            logger.error(f"SQL 생성 실패 - JSON 파싱 오류: {e}", exc_info=True)

            tracker.error_step(
                error_msg="SQL 생성 형식 오류 (LLM 응답 파싱 실패)",
                suggestion="질문을 더 구체적으로 말씀해주세요"
            )

            state["error"] = SQLGenerationError("SQLGenerator", f"JSON 파싱 실패: {str(e)}", original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except Exception as e:
            # 일반 예외
            logger.error(f"SQLGenerator 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"SQL 생성 오류: {str(e)}",
                suggestion="질문을 다시 확인해주세요"
            )

            state["error"] = handle_exception("SQLGenerator", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _generate_sql(
        self,
        sub_question: Dict[str, Any],
        entities: Dict[str, Any],
        capabilities: Dict[str, Any],
        state: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        LLM을 사용하여 SQL 생성

        Args:
            sub_question: 하위 질문
            entities: 엔티티
            capabilities: 분석 전략
            state: AgentState (디버그 추적용, 옵션)

        Returns:
            SQL 정보
        """
        prompt = f"""당신은 PostgreSQL Text-to-SQL 전문가입니다.
하위 질문을 분석하여 필요한 데이터를 가져오는 SQL 쿼리를 생성하세요.

**데이터베이스 스키마:**

preprocessed_reviews 테이블 (5,000건 - GPT 분석 완료 + 원본 데이터):
   컬럼:
   - id (integer, PRIMARY KEY)
   - review_id (varchar, UNIQUE)
   - brand (varchar) - 브랜드명
   - product_name (varchar) - 제품명
   - channel (varchar) - 채널 (OliveYoung, Coupang, Daiso)
   - category (varchar) - 카테고리
   - review_clean (text) - 전처리된 리뷰 원문
   - rating (text) - 평점 (숫자로 변환: CAST(rating AS FLOAT))
   - review_date (text) - 리뷰 날짜 (날짜로 변환: CAST(review_date AS DATE))
   - ranking (text) - 제품 순위
   - product_price_sale (text) - 판매가
   - product_price_origin (text) - 정가
   - analysis (JSONB) - GPT-4o-mini 분석 결과:
     * analysis->'제품특성' → {{"보습력": "촉촉함", "발림성": "부드러움", "향": "무향", ...}}
     * analysis->'감정요약' → {{"전반적평가": "긍정적", "표현": [...]}}
     * analysis->'장점' → ["발색 좋음", "지속력 좋음", ...] (배열)
     * analysis->'단점' → ["끈적임", "가격 비쌈", ...] (배열)
     * analysis->'구매동기' → {{"재구매": true, "추천": true, ...}}
     * analysis->'키워드' → ["보습", "촉촉", "발림", ...] (배열)

**JSONB 쿼리 방법:**

1. 특정 속성 존재 확인:
   WHERE analysis->'제품특성'->'보습력' IS NOT NULL

2. 특정 값 조회:
   WHERE analysis->'감정요약'->>'전반적평가' = '긍정적'

3. 배열 요소 개수:
   jsonb_array_length(analysis->'장점')

4. 배열 펼치기:
   SELECT jsonb_array_elements_text(analysis->'키워드') as keyword

5. 배열에 특정 값 포함:
   WHERE analysis->'키워드' @> '["보습"]'

**SQL 작성 규칙:**

1. 항상 preprocessed_reviews 테이블만 사용 (단일 테이블 구조)
2. 필요한 컬럼만 SELECT
3. WHERE 절로 브랜드/제품/채널/기간 필터링
4. 집계 필요 시 GROUP BY 사용
5. 날짜는 CAST(review_date AS DATE) 변환
6. 평점은 CAST(rating AS FLOAT) 변환
7. LIMIT은 샘플 필요 시만 (기본 없음)
8. 리뷰 원문 샘플 제공 시 review_clean 컬럼 사용

**LIMIT 사용 규칙 (IMPORTANT):**

preprocessed_reviews 테이블은 총 5,000건의 작은 데이터셋입니다.
쿼리 유형에 따라 다음 규칙을 따르세요:

1. **종합 분석/전체 데이터 필요 시**: LIMIT 없음 또는 LIMIT 200
   - "제품 종합 분석", "전체 리뷰 분석", "모든 리뷰" 등
   - 예: SELECT * FROM preprocessed_reviews WHERE brand = '빌리프' (LIMIT 없음)

2. **집계 쿼리 (GROUP BY)**: LIMIT 20-50
   - 브랜드별/제품별/속성별 집계
   - 예: SELECT brand, COUNT(*) ... GROUP BY brand LIMIT 30

3. **샘플 리뷰만 필요**: LIMIT 10-20
   - "샘플 보여줘", "예시 리뷰", "몇 개만"
   - 예: SELECT review_clean ... LIMIT 10

4. **reviews 테이블 (314,285건)**: 항상 LIMIT 필수
   - 대용량 데이터이므로 LIMIT 100-1000 사용

**필터링 규칙 (IMPORTANT):**

1. 브랜드명 필터: 정확한 매칭 사용
   - WHERE brand = '브랜드명'
   - 예: WHERE brand = '빌리프'

2. 제품명 필터: 부분 매칭 사용 (LIKE 필수)
   - WHERE product_name LIKE '%제품명%'
   - 예: WHERE product_name LIKE '%모이스춰라이징밤%'
   - 이유: DB에 "빌리프 더 트루 크림 모이스춰라이징 밤" 등 전체 제품명이 저장되어 있음

3. 채널명 필터: 정확한 매칭 사용
   - WHERE channel = '채널명'

**예시:**

예시 1 - 단순 속성 분석:
질문: "빌리프 보습력 평가"
entities: {{"brands": ["빌리프"], "attributes": ["보습력"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "simple"}}
→ SQL:
```sql
SELECT
    brand,
    product_name,
    analysis->'제품특성'->>'보습력' as 보습력평가,
    COUNT(*) as review_count
FROM preprocessed_reviews
WHERE brand = '빌리프'
  AND analysis->'제품특성'->'보습력' IS NOT NULL
GROUP BY brand, product_name, analysis->'제품특성'->>'보습력'
ORDER BY review_count DESC
```

예시 1-2 - 제품명 포함 속성 분석:
질문: "빌리프 모이스춰라이징밤 보습력"
entities: {{"brands": ["빌리프"], "products": ["모이스춰라이징밤"], "attributes": ["보습력"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "simple"}}
→ SQL:
```sql
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
```

예시 2 - 평점 트렌드:
질문: "빌리프 최근 3개월 평점 트렌드"
entities: {{"brands": ["빌리프"], "period": {{"start": "2025-07-29", "end": "2025-10-29"}}}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "time_series"}}
→ SQL:
```sql
SELECT
    DATE_TRUNC('month', CAST(review_date AS DATE)) as month,
    AVG(CAST(rating AS FLOAT)) as avg_rating,
    COUNT(*) as review_count
FROM preprocessed_reviews
WHERE brand = '빌리프'
  AND CAST(review_date AS DATE) >= '2025-07-29'
  AND CAST(review_date AS DATE) <= '2025-10-29'
GROUP BY DATE_TRUNC('month', CAST(review_date AS DATE))
ORDER BY month
```

예시 3 - 장점 분석 (리뷰 원문 샘플 포함):
질문: "빌리프 모이스춰라이징밤 장점"
entities: {{"brands": ["빌리프"], "products": ["모이스춰라이징밤"], "attributes": ["장점"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "keyword_frequency"}}
→ SQL:
```sql
WITH advantage_keywords AS (
    SELECT
        jsonb_array_elements_text(analysis->'장점') as advantage,
        review_clean,
        rating,
        review_date
    FROM preprocessed_reviews
    WHERE brand = '빌리프'
      AND product_name LIKE '%모이스춰라이징밤%'
      AND jsonb_array_length(analysis->'장점') > 0
)
SELECT
    advantage,
    COUNT(*) as count,
    jsonb_agg(
        jsonb_build_object(
            'review_clean', review_clean,
            'rating', rating,
            'review_date', review_date
        )
    ) FILTER (WHERE review_clean IS NOT NULL) as review_samples
FROM advantage_keywords
GROUP BY advantage
ORDER BY count DESC
LIMIT 10
```

예시 4 - 샘플 리뷰:
질문: "빌리프 샘플 리뷰"
entities: {{"brands": ["빌리프"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "simple"}}
→ SQL:
```sql
SELECT
    brand,
    product_name,
    rating,
    review_date,
    review_clean,
    analysis->'감정요약'->>'전반적평가' as sentiment
FROM preprocessed_reviews
WHERE brand = '빌리프'
ORDER BY CAST(review_date AS DATE) DESC
LIMIT 10
```

예시 5 - 제품 특정 리뷰:
질문: "VT 시카크림 샘플 리뷰"
entities: {{"brands": ["VT"], "products": ["시카크림"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "simple"}}
→ SQL:
```sql
SELECT
    brand,
    product_name,
    rating,
    review_date,
    review_clean,
    analysis->'감정요약'->>'전반적평가' as sentiment
FROM preprocessed_reviews
WHERE brand = 'VT'
  AND product_name LIKE '%시카크림%'
ORDER BY CAST(review_date AS DATE) DESC
LIMIT 10
```

예시 6 - 제품 종합 분석 (전체 analysis 포함):
질문: "빌리프 모이스춰라이징밤 리뷰 종합 분석"
entities: {{"brands": ["빌리프"], "products": ["모이스춰라이징밤"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "analysis_depth": "keyword"}}
→ SQL:
```sql
SELECT
    brand,
    product_name,
    channel,
    rating,
    review_date,
    review_clean,
    analysis
FROM preprocessed_reviews
WHERE brand = '빌리프'
  AND product_name LIKE '%모이스춰라이징밤%'
ORDER BY CAST(review_date AS DATE) DESC
LIMIT 100
```
**하위 질문:**
{sub_question['sub_question']}

**목적:**
{sub_question['purpose']}

**엔티티:**
{json.dumps(entities, ensure_ascii=False, indent=2)}

**분석 전략:**
{json.dumps(capabilities, ensure_ascii=False, indent=2)}

**다음 형식으로 JSON 반환:**
{{
    "sql": "SQL 쿼리 (세미콜론 없이)",
    "purpose": "이 쿼리의 목적 (한 줄)",
    "estimated_rows": 예상 결과 행 수 (숫자),
    "uses_index": 인덱스 활용 여부 (true/false),
    "explanation": "쿼리 설명 (2-3줄)"
}}

**JSON만 반환하세요:**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        result_text = response.choices[0].message.content.strip()

        # JSON 파싱
        try:
            # 코드 블록 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            sql_info = json.loads(result_text)

            # Debug 추적 (state가 있을 때만)
            if state:
                self._add_debug_trace(
                    state=state,
                    step=f"generate_sql_{sub_question.get('sub_question', '')[:30]}",
                    prompt=prompt,
                    llm_response=result_text,
                    parsed_result=sql_info
                )

            return sql_info

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {result_text[:200]}... (error: {str(e)})")

    def _add_debug_trace(
        self,
        state: Dict[str, Any],
        step: str,
        prompt: str,
        llm_response: str,
        parsed_result: Any = None
    ):
        """
        Debug 모드일 때 LLM 추적 정보 저장

        Args:
            state: AgentState
            step: 단계 이름
            prompt: LLM 프롬프트
            llm_response: LLM 원본 응답
            parsed_result: 파싱된 결과 (옵션)
        """
        if state.get("debug_mode", False):
            state.setdefault("debug_traces", []).append({
                "node": "SQLGenerator",
                "step": step,
                "prompt": prompt[:1000] if len(prompt) > 1000 else prompt,  # 처음 1000자
                "llm_response": llm_response[:1000] if len(llm_response) > 1000 else llm_response,
                "parsed_result": parsed_result
            })
