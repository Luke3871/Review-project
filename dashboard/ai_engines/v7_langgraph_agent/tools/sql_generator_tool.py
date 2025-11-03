#//==============================================================================//#
"""
sql_generator_tool.py
SQL 쿼리 생성 Tool

엔티티와 분석 전략을 바탕으로 PostgreSQL 쿼리 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any, List
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.sql_generator import SQLGenerator
from state import AgentState


@tool
def generate_sql(state: Any) -> str:
    """
    PostgreSQL SQL 쿼리 생성 (Text-to-SQL)

    이 도구는 사용자 질문, 엔티티, 분석 전략을 바탕으로 데이터베이스 쿼리를 자동 생성합니다.

    **지원하는 테이블:**

    1. reviews 테이블 (314,285건):
       - 평점 조회, 리뷰 수 집계, 트렌드 분석, 원문 샘플
       - 컬럼: review_id, brand, product_name, channel, category, rating, review_date, review_text

    2. preprocessed_reviews 테이블 (5,000건):
       - GPT-4o-mini 분석 완료 데이터
       - 속성별 평가, 장단점, 감정 분석, 키워드 추출, 불만사항, 구매동기
       - JSONB 컬럼: analysis (제품특성, 감정요약, 장점, 단점, 불만사항, 구매동기, 키워드 등)

    **특별 기능: data_scope="both"**

    평점과 텍스트 분석을 모두 필요로 할 때, 두 테이블을 각각 쿼리합니다 (JOIN 하지 않음):
    - SQL 1: reviews 테이블 쿼리 (평점, 리뷰 수 등)
    - SQL 2: preprocessed_reviews 테이블 쿼리 (속성 분석, 장단점 등)

    **생성되는 SQL 유형:**

    1. 시계열 트렌드:
       - 월별/일별 평점 변화
       - 리뷰 수 추이

    2. 비교 분석:
       - 브랜드 간 평점 비교
       - 제품 간 속성 비교

    3. 분포 분석:
       - 평점 분포 (1-5점)
       - 카테고리별 리뷰 분포

    4. 키워드 빈도:
       - 장점 키워드 TOP 20
       - 단점 키워드 TOP 20

    5. 단순 조회:
       - 특정 제품 속성 평가
       - 샘플 리뷰 10개

    Args:
        user_query: 사용자의 자연어 질문
            예: "빌리프와 VT의 최근 3개월 보습력 비교"

        parsed_entities: parse_entities 도구로 추출한 엔티티
            예: {
                "brands": ["빌리프", "VT"],
                "attributes": ["보습력"],
                "period": {"start": "2025-08-02", "end": "2025-11-02"}
            }

        capabilities: detect_capabilities 도구로 결정한 분석 전략
            예: {
                "data_scope": "preprocessed_reviews",
                "aggregation_type": "comparison",
                "group_by": "brand",
                "analysis_depth": "attribute"
            }

    Returns:
        SQL 정보 리스트 (보통 1개, data_scope="both"이면 2개):
        [
            {
                "sql": "SELECT ... FROM preprocessed_reviews WHERE ...",
                "purpose": "빌리프와 VT의 보습력 평가 비교",
                "estimated_rows": 150,
                "uses_index": true,
                "explanation": "두 브랜드의 보습력 평가를 집계하여 비교합니다.",
                "table_name": "preprocessed_reviews"  # (both 분리 시에만)
            }
        ]

    **State 읽기:**
    - user_query: 사용자의 원래 질문
    - parsed_entities: parse_entities 도구가 추출한 엔티티
    - capabilities: detect_capability 도구가 결정한 분석 전략

    **State 쓰기:**
    - sql_queries: 생성된 SQL 쿼리 리스트 (1개 또는 2개)

    **생성 예시:**

    질문: "빌리프 평점 어때?"
    → sql_queries: [{"sql": "SELECT AVG(rating)...", "purpose": "평균 평점 조회"}]

    질문: "빌리프 보습력 어때?"
    → sql_queries: [{"sql": "SELECT analysis->'제품특성'...", "purpose": "보습력 분석"}]

    질문: "빌리프 평점도 알려주고 보습력도 분석해줘"
    → sql_queries: [
        {"sql": "SELECT AVG(rating)...", "purpose": "평균 평점", "table_name": "reviews"},
        {"sql": "SELECT analysis->'제품특성'...", "purpose": "보습력 분석", "table_name": "preprocessed_reviews"}
    ]

    질문: "빌리프와 마몽드 평점 비교"
    → sql_queries: [{"sql": "SELECT brand, AVG(rating)... GROUP BY brand", "purpose": "브랜드 비교"}]

    **사용 시점:**
    - detect_capability 실행 후
    - execute_sql 실행 전

    Args:
        state: Agent 상태 (user_query, parsed_entities, capabilities 포함)

    Returns:
        실행 완료 메시지 (sql_queries는 State에 저장됨)
    """
    # State에서 데이터 읽기
    user_query = state["user_query"]
    parsed_entities = state.get("parsed_entities")
    capabilities = state.get("capabilities")

    if not parsed_entities:
        return "오류: 엔티티가 추출되지 않았습니다. parse_entities를 먼저 실행하세요."

    if not capabilities:
        return "오류: 분석 전략이 결정되지 않았습니다. detect_capability를 먼저 실행하세요."

    # SQLGenerator 인스턴스 생성
    generator = SQLGenerator()

    # SQL 생성 (data_scope="both"이면 2개 반환)
    sql_queries = generator._generate_sql(user_query, parsed_entities, capabilities)

    # State에 저장
    state["sql_queries"] = sql_queries

    # 간단한 완료 메시지 반환
    num_queries = len(sql_queries)
    return f"SQL 쿼리 생성 완료: {num_queries}개 쿼리"
