#//==============================================================================//#
"""
output_generator_tool.py
최종 텍스트 출력 생성 Tool

쿼리 결과를 분석하여 사용자에게 전달할 마케팅 리포트 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.output_generator import OutputGenerator
from state import AgentState


@tool
def generate_output(state: Any) -> str:
    """
    SQL 쿼리 결과를 분석하여 최종 텍스트 리포트 생성

    이 도구는 execute_sql 도구의 결과를 받아서 사용자에게 전달할 최종 답변을 생성합니다.

    **생성되는 리포트 구조:**

    1. 핵심 요약:
       - 주요 수치 2-3문장 요약
       - 가장 중요한 발견사항

    2. 데이터 분석:
       - 패턴과 트렌드
       - 구체적 수치 (건수, 비율, 평균)
       - 제품특성, 감정요약, 장단점 (preprocessed_reviews 데이터인 경우)

    3. 리뷰 샘플:
       - 대표 긍정 리뷰 인용
       - 대표 부정 리뷰 인용
       (SQL 결과에 리뷰 원문이 있을 경우만)

    4. 마케팅 시사점:
       - 실무 제안
       - 캠페인 소구점
       - 개선 영역
       - 타겟 확장 기회

    5. 데이터 범위:
       - 분석 건수, 기간, 출처

    **작성 원칙:**

    - SQL 결과에 있는 데이터만 사용 (추정 금지)
    - 모든 주장에 구체적 수치 포함
    - 이모지 사용 금지
    - 간결하게 핵심만 전달
    - 마크다운 형식

    Args:
        user_query: 사용자의 원래 질문
            예: "빌리프와 VT의 최근 3개월 보습력 비교"

        parsed_entities: parse_entities 도구의 출력
            예: {
                "brands": ["빌리프", "VT"],
                "attributes": ["보습력"],
                "period": {"display": "최근 3개월"}
            }

        query_results: execute_sql 도구의 출력
            예: {
                "results": [
                    {
                        "data": [{"brand": "빌리프", "avg_moisturizing": 4.5}],
                        "row_count": 150,
                        "success": True
                    }
                ],
                "data_characteristics": {...}
            }

    Returns:
        마크다운 형식의 최종 리포트 텍스트

    **사용 예시:**

    질문: "빌리프 평점 어때?"
    → reviews 테이블 결과 분석
    → "빌리프 평균 평점은 4.5점입니다 (1,250건 기준)..."

    질문: "빌리프 보습력 어때?"
    → preprocessed_reviews 테이블 결과 분석
    → "빌리프 보습력 평가는 '촉촉함' 45%, '매우 촉촉' 30%로..."

    질문: "빌리프 평점도 알려주고 보습력도 분석해줘"
    → 2개 쿼리 결과 통합 분석
    → "### 평점 분석\n평균 4.5점...\n\n### 보습력 분석\n..."

    **주의사항:**

    - 데이터에 없는 내용은 절대 추정하지 않음
    - 리뷰 원문은 SQL 결과에 있는 것만 인용
    - 데이터가 없는 섹션은 생략
    - LG생활건강 마케팅팀을 위한 실무 중심 리포트

    **State 읽기:**
    - user_query: 사용자의 원래 질문
    - parsed_entities: parse_entities 도구가 추출한 엔티티
    - query_results: execute_sql 도구의 실행 결과

    **State 쓰기:**
    - final_response: 최종 리포트 텍스트

    **생성 예시:**

    질문: "빌리프 평점 어때?"
    → "빌리프의 평균 평점은 4.5점입니다 (1,250건 기준)..."

    질문: "빌리프와 마몽드 보습력 비교"
    → "### 핵심 요약\n빌리프는 보습력 4.5점, 마몽드는 4.2점...\n\n### 데이터 범위\npreprocessed_reviews 테이블, 총 300건 분석"

    **사용 시점:**
    - execute_sql 실행 후
    - 마지막 단계 (이후 사용자에게 답변 전달)

    Args:
        state: Agent 상태 (user_query, parsed_entities, query_results 포함)

    Returns:
        최종 리포트 텍스트 (마크다운 형식)
    """
    # State에서 데이터 읽기
    user_query = state["user_query"]
    parsed_entities = state.get("parsed_entities")
    query_results = state.get("query_results")

    if not parsed_entities:
        return "오류: 엔티티가 추출되지 않았습니다."

    if not query_results:
        return "오류: 쿼리 결과가 없습니다."

    # OutputGenerator 인스턴스 생성
    generator = OutputGenerator()

    # 텍스트 출력 생성
    output_text = generator._generate_text_output(
        user_query,
        parsed_entities,
        query_results
    )

    # State에 저장
    state["final_response"] = output_text

    # 최종 리포트 반환 (사용자에게 전달)
    return output_text
