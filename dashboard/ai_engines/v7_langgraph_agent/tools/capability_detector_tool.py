#//==============================================================================//#
"""
capability_detector_tool.py
분석 전략 결정 Tool

사용자 질문과 엔티티를 바탕으로 최적의 데이터 소스와 분석 방법 결정

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.capability_detector import CapabilityDetector
from state import AgentState


@tool
def detect_capability(state: Any) -> str:
    """
    사용자 질문의 분석 전략 결정 (데이터 소스, 집계 방식, 분석 깊이)

    이 도구는 사용자 질문과 추출된 엔티티를 분석하여 최적의 데이터 분석 전략을 결정합니다:

    **결정 항목:**

    1. data_scope (데이터 소스):
       - "reviews": 평점, 리뷰 수, 트렌드 등 기본 통계 (314,285건)
       - "preprocessed_reviews": 속성별 분석, 장단점, 감정 분석 등 심층 분석 (5,000건)
       - "both": 평점과 텍스트 분석을 모두 필요로 할 때 (각각 따로 쿼리)

    2. aggregation_type (집계 방식):
       - "time_series": 시간별 트렌드 분석 (월별, 일별 변화)
       - "comparison": 여러 대상 비교 (브랜드, 제품 간 비교)
       - "distribution": 분포 분석 (평점 분포, 카테고리 분포)
       - "keyword_frequency": 키워드 빈도 분석
       - "simple": 단순 조회

    3. group_by (그룹화 기준):
       - "brand": 브랜드별 그룹화
       - "product": 제품별 그룹화
       - "channel": 채널별 그룹화
       - "period": 기간별 그룹화 (시계열)
       - "none": 그룹화 없음

    4. analysis_depth (분석 깊이):
       - "overview": 전반적 요약 (평점, 리뷰 수)
       - "attribute": 속성별 분석 (보습력, 발림성 등)
       - "sentiment": 감정 분석 (긍정/부정)
       - "keyword": 키워드 분석
       - "pros_cons": 장단점 분석

    5. metric (측정 지표):
       - "rating": 평점
       - "count": 개수
       - "percentage": 비율

    Args:
        user_query: 사용자의 자연어 질문
            예: "빌리프와 VT의 최근 3개월 보습력 비교"

        parsed_entities: parse_entities 도구로 추출한 엔티티 정보
            예: {
                "brands": ["빌리프", "VT"],
                "attributes": ["보습력"],
                "period": {"start": "2025-08-02", "end": "2025-11-02", "display": "최근 3개월"}
            }

    Returns:
        Dict 형식의 분석 전략:
        {
            "data_scope": "preprocessed_reviews",
            "aggregation_type": "comparison",
            "group_by": "brand",
            "analysis_depth": "attribute",
            "metric": "count"
        }

    **사용 예시:**

    **State 읽기:**
    - user_query: 사용자의 원래 질문
    - parsed_entities: parse_entities 도구가 추출한 엔티티

    **State 쓰기:**
    - capabilities: 분석 전략 (data_scope, aggregation_type, group_by, analysis_depth, metric)

    **결정 예시:**

    질문: "빌리프 평점 어때?"
    → capabilities: {
        "data_scope": "reviews",
        "aggregation_type": "simple",
        "group_by": "none",
        "analysis_depth": "overview",
        "metric": "rating"
    }

    질문: "빌리프 보습력 어때?"
    → capabilities: {
        "data_scope": "preprocessed_reviews",
        "aggregation_type": "simple",
        "group_by": "none",
        "analysis_depth": "attribute",
        "metric": "attribute_score"
    }

    질문: "빌리프와 마몽드 평점 비교"
    → capabilities: {
        "data_scope": "reviews",
        "aggregation_type": "comparison",
        "group_by": "brand",
        "analysis_depth": "overview",
        "metric": "rating"
    }

    **사용 시점:**
    - parse_entities 실행 후
    - generate_sql 실행 전

    Args:
        state: Agent 상태 (user_query, parsed_entities 포함)

    Returns:
        실행 완료 메시지 (capabilities는 State에 저장됨)
    """
    # State에서 데이터 읽기
    user_query = state["user_query"]
    parsed_entities = state.get("parsed_entities")

    if not parsed_entities:
        return "오류: 엔티티가 추출되지 않았습니다. parse_entities를 먼저 실행하세요."

    # CapabilityDetector 인스턴스 생성
    detector = CapabilityDetector()

    # 분석 전략 결정
    capabilities = detector._detect_capabilities(user_query, parsed_entities)

    # State에 저장
    state["capabilities"] = capabilities

    # 간단한 완료 메시지 반환
    data_scope = capabilities.get("data_scope", "unknown")
    agg_type = capabilities.get("aggregation_type", "unknown")

    return f"분석 전략 결정 완료: {data_scope} 테이블, {agg_type} 방식"
