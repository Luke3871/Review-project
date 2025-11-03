#//==============================================================================//#
"""
executor_tool.py
SQL 쿼리 실행 Tool

생성된 SQL을 PostgreSQL에서 실행하고 결과 반환

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any, List
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.executor import Executor
from state import AgentState


@tool
def execute_sql(state: Any) -> str:
    """
    PostgreSQL 데이터베이스에서 SQL 쿼리 실행

    이 도구는 generate_sql 도구가 생성한 SQL 쿼리를 실행하고 결과를 반환합니다.

    **실행 프로세스:**

    1. PostgreSQL 데이터베이스 연결
    2. 각 SQL 쿼리 순차 실행
    3. 결과를 딕셔너리 리스트로 변환
    4. 데이터 특성 자동 분석 (시계열, 비교, 분포, 키워드 등)
    5. 연결 종료 및 결과 반환

    **에러 처리:**

    - SQL 실행 실패 시 해당 쿼리만 에러로 표시하고 계속 진행
    - 각 결과의 `success` 필드로 성공/실패 확인 가능
    - 에러 발생 시 `error` 필드에 상세 메시지 포함

    **데이터 특성 분석:**

    자동으로 다음 특성을 감지합니다:
    - time_series: 시계열 데이터 (month, date 컬럼)
    - multi_entity: 여러 엔티티 비교 (brand, product_name 컬럼)
    - has_distribution: 분포 데이터 (count, percentage 컬럼)
    - keyword_count: 키워드 데이터 개수

    이 정보는 OutputGenerator가 시각화 방식을 결정하는 데 사용됩니다.

    Args:
        sql_queries: generate_sql 도구의 출력 (SQL 정보 리스트)
            예: [
                {
                    "sql": "SELECT brand, AVG(CAST(rating AS FLOAT)) ... FROM reviews ...",
                    "purpose": "브랜드별 평균 평점 조회",
                    "estimated_rows": 150,
                    "table_name": "reviews"  # (data_scope="both" 시에만)
                }
            ]

    Returns:
        쿼리 실행 결과:
        {
            "results": [
                {
                    "query_index": 1,
                    "sql": "SELECT ...",
                    "purpose": "...",
                    "table_name": "reviews",  # (있으면)
                    "data": [
                        {"brand": "빌리프", "avg_rating": 4.5, "review_count": 1250},
                        {"brand": "VT", "avg_rating": 4.3, "review_count": 980}
                    ],
                    "columns": ["brand", "avg_rating", "review_count"],
                    "row_count": 2,
                    "duration": 0.15,
                    "success": true,
                    "error": null
                }
            ],
            "total_queries": 1,
            "total_duration": 0.15,
            "data_characteristics": {
                "total_rows": 2,
                "successful_queries": 1,
                "failed_queries": 0,
                "time_series": false,
                "multi_entity": true,
                "has_distribution": true,
                "keyword_count": 0
            }
        }

    **사용 예시:**

    질문: "빌리프 평점 어때?"
    → execute_sql 실행 → reviews 테이블에서 평점 조회 → 평균 4.5점 반환

    질문: "빌리프 보습력 어때?"
    → execute_sql 실행 → preprocessed_reviews 테이블에서 보습력 분석 → 평가 분포 반환

    질문: "빌리프 평점도 알려주고 보습력도 분석해줘"
    → execute_sql 실행 (2개 SQL) → reviews + preprocessed_reviews 결과 반환

    **State 읽기:**
    - sql_queries: generate_sql 도구가 생성한 SQL 쿼리 리스트

    **State 쓰기:**
    - query_results: 쿼리 실행 결과 (results, total_queries, data_characteristics)

    **실행 예시:**

    sql_queries: [{"sql": "SELECT AVG(rating)...", "purpose": "평균 평점"}]
    → query_results: {
        "results": [{"data": [...], "row_count": 150, "success": True}],
        "total_queries": 1,
        "data_characteristics": {"total_rows": 150, ...}
    }

    **사용 시점:**
    - generate_sql 실행 후
    - generate_output 실행 전

    **주의사항:**
    - 쿼리 실행 시간이 오래 걸릴 수 있음 (대용량 데이터)
    - 각 쿼리는 독립적으로 실행되며, 하나 실패해도 나머지 계속 진행

    Args:
        state: Agent 상태 (sql_queries 포함)

    Returns:
        실행 완료 메시지 (query_results는 State에 저장됨)
    """
    # State에서 데이터 읽기
    sql_queries = state.get("sql_queries")

    if not sql_queries:
        return "오류: SQL 쿼리가 생성되지 않았습니다. generate_sql을 먼저 실행하세요."

    # Executor 인스턴스 생성
    executor = Executor()

    # SQL 쿼리 실행
    query_results = executor._execute_queries(sql_queries)

    # State에 저장
    state["query_results"] = query_results

    # 간단한 완료 메시지 반환
    total_queries = query_results.get("total_queries", 0)
    total_rows = query_results.get("data_characteristics", {}).get("total_rows", 0)

    return f"SQL 실행 완료: {total_queries}개 쿼리, 총 {total_rows}건 조회"
