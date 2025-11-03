#//==============================================================================//#
"""
sql_generator.py
동적 SQL 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
from typing import Dict, Any, List
from openai import OpenAI

import sys
from pathlib import Path

# V7 config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LLM_CONFIG


class SQLGenerator:
    """SQL 동적 생성"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["sql_generator"]  # 0.0
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def _generate_sql(
        self,
        user_query: str,
        entities: Dict[str, Any],
        capabilities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        LLM을 사용하여 SQL 생성

        data_scope="both"인 경우 두 개의 SQL 반환 (reviews, preprocessed_reviews)

        Args:
            user_query: 사용자 질문
            entities: 엔티티
            capabilities: 분석 전략

        Returns:
            SQL 정보 리스트 (data_scope="both"이면 2개, 아니면 1개)
        """
        data_scope = capabilities.get("data_scope", "reviews")

        # data_scope="both"이면 두 개로 분리
        if data_scope == "both":
            sql_queries = []

            # 1. reviews 테이블 쿼리
            reviews_caps = capabilities.copy()
            reviews_caps["data_scope"] = "reviews"
            sql_info_reviews = self._generate_single_sql(
                user_query,
                entities,
                reviews_caps,
                table_name="reviews"
            )
            sql_queries.append(sql_info_reviews)

            # 2. preprocessed_reviews 테이블 쿼리
            preprocessed_caps = capabilities.copy()
            preprocessed_caps["data_scope"] = "preprocessed_reviews"
            sql_info_preprocessed = self._generate_single_sql(
                user_query,
                entities,
                preprocessed_caps,
                table_name="preprocessed_reviews"
            )
            sql_queries.append(sql_info_preprocessed)

            return sql_queries
        else:
            # 단일 테이블 쿼리
            sql_info = self._generate_single_sql(user_query, entities, capabilities)
            return [sql_info]

    def _generate_single_sql(
        self,
        user_query: str,
        entities: Dict[str, Any],
        capabilities: Dict[str, Any],
        table_name: str = None
    ) -> Dict[str, Any]:
        """
        단일 SQL 생성

        Args:
            user_query: 사용자 질문
            entities: 엔티티
            capabilities: 분석 전략
            table_name: 강제 테이블명 (both 분리 시 사용)

        Returns:
            SQL 정보
        """
        prompt = f"""당신은 PostgreSQL Text-to-SQL 전문가입니다.
사용자 질문을 분석하여 필요한 데이터를 가져오는 SQL 쿼리를 생성하세요.

**데이터베이스 스키마:**

1. reviews 테이블 (314,285건 - 원본 데이터):
   컬럼:
   - review_id (text, PRIMARY KEY)
   - brand (text) - 브랜드명
   - product_name (text) - 제품명
   - channel (text) - 채널 (OliveYoung, Coupang, Daiso)
   - category (text) - 카테고리
   - rating (text) - 평점 (숫자로 변환 필요: CAST(rating AS FLOAT))
   - review_date (text) - 리뷰 날짜 (날짜로 변환 필요: CAST(review_date AS DATE))
   - review_text (text) - 리뷰 원문
   - review_clean (text) - 전처리된 리뷰
   - reviewer_skin_features (text) - 리뷰어 피부 정보

2. preprocessed_reviews 테이블 (5,000건 - GPT 분석 완료):
   컬럼:
   - id (integer, PRIMARY KEY)
   - review_id (varchar, UNIQUE, FK → reviews.review_id)
   - brand (varchar) - 브랜드명
   - product_name (varchar) - 제품명
   - channel (varchar) - 채널
   - category (varchar) - 카테고리
   - analysis (JSONB) - GPT-4o-mini 분석 결과:
     * analysis->'원본_제품명' → 원본 제품명
     * analysis->'표준_브랜드' → 표준 브랜드명
     * analysis->'표준_제품명' → 표준 제품명
     * analysis->'제품_카테고리' → 카테고리
     * analysis->'용량_및_수량' → 용량/수량 정보
     * analysis->'색상_옵션' → 색상 옵션
     * analysis->'기획여부' → 기획 상품 여부
     * analysis->'제품특성' → {{"보습력": "촉촉함", "발림성": "부드러움", "향": "무향", ...}}
     * analysis->'기획정보' → 기획 상품 관련 정보
     * analysis->'감정요약' → {{"전반적평가": "긍정적", "표현": [...]}}
     * analysis->'장점' → ["발색 좋음", "지속력 좋음", ...] (배열)
     * analysis->'단점' → ["끈적임", "가격 비쌈", ...] (배열)
     * analysis->'불만사항' → {{"용기/패키지 디자인": [...], "용기 내구성": [...], ...}}
     * analysis->'구매동기' → {{"인플루언서": true, "재구매": true, ...}}
     * analysis->'타제품비교' → 다른 제품과의 비교 내용
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

**테이블 선택 기준:**

- data_scope="reviews": reviews 테이블만 (평점, 리뷰 수, 날짜, 원문 샘플)
- data_scope="preprocessed_reviews": preprocessed_reviews 테이블만 (텍스트 분석 - 장점, 단점, 속성, 감정)
{"- 강제 테이블: " + table_name if table_name else ""}

**SQL 작성 규칙:**

1. 필요한 컬럼만 SELECT
2. WHERE 절로 브랜드/제품/채널/기간 필터링
3. 집계 필요 시 GROUP BY 사용
4. 날짜는 CAST(review_date AS DATE) 변환
5. 평점은 CAST(rating AS FLOAT) 변환
6. LIMIT은 샘플 필요 시만 (기본 없음)

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

예시 2 - 평점 트렌드:
질문: "빌리프 최근 3개월 평점 트렌드"
entities: {{"brands": ["빌리프"], "period": {{"start": "2025-07-29", "end": "2025-10-29"}}}}
capabilities: {{"data_scope": "reviews", "aggregation_type": "time_series"}}
→ SQL:
```sql
SELECT
    DATE_TRUNC('month', CAST(review_date AS DATE)) as month,
    AVG(CAST(rating AS FLOAT)) as avg_rating,
    COUNT(*) as review_count
FROM reviews
WHERE brand = '빌리프'
  AND CAST(review_date AS DATE) >= '2025-07-29'
  AND CAST(review_date AS DATE) <= '2025-10-29'
GROUP BY DATE_TRUNC('month', CAST(review_date AS DATE))
ORDER BY month
```

예시 3 - 장점 분석:
질문: "빌리프 장점"
entities: {{"brands": ["빌리프"], "attributes": ["장점"]}}
capabilities: {{"data_scope": "preprocessed_reviews", "aggregation_type": "keyword_frequency"}}
→ SQL:
```sql
SELECT
    jsonb_array_elements_text(analysis->'장점') as advantage,
    COUNT(*) as count
FROM preprocessed_reviews
WHERE brand = '빌리프'
  AND jsonb_array_length(analysis->'장점') > 0
GROUP BY advantage
ORDER BY count DESC
LIMIT 20
```

예시 4 - 샘플 리뷰:
질문: "빌리프 샘플 리뷰"
entities: {{"brands": ["빌리프"]}}
capabilities: {{"data_scope": "reviews", "aggregation_type": "simple"}}
→ SQL:
```sql
SELECT
    brand,
    product_name,
    rating,
    review_date,
    review_text
FROM reviews
WHERE brand = '빌리프'
ORDER BY CAST(review_date AS DATE) DESC
LIMIT 10
```

**사용자 질문:**
{user_query}

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

            # table_name 추가 (both 분리 시 식별용)
            if table_name:
                sql_info["table_name"] = table_name

            return sql_info

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {result_text[:200]}... (error: {str(e)})")
