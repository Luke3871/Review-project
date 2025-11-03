#//==============================================================================//#
"""
entity_parser_tool.py
엔티티 추출 Tool

사용자 질문에서 브랜드, 제품, 속성, 기간, 채널 추출

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.entity_parser import EntityParser
from state import AgentState


@tool
def parse_entities(state) -> str:
    """
    사용자 질문에서 엔티티 추출 (브랜드, 제품, 속성, 기간, 채널)

    이 도구는 자연어 질문을 분석하여 다음 정보를 추출하고 State에 저장합니다:
    - 브랜드: 화장품 브랜드명 (예: 빌리프, VT, 라로슈포제)
    - 제품: 구체적인 제품명 (예: 모이스춰라이징밤)
    - 속성: 분석할 제품 특성 (예: 보습력, 발림성, 향)
    - 기간: 분석 기간 (예: 최근 3개월, 2024년 1월)
    - 채널: 리뷰 채널 (예: 올리브영, 쿠팡, 다이소)

    **State 읽기:**
    - user_query: 사용자의 원래 질문

    **State 쓰기:**
    - parsed_entities: 추출된 엔티티 정보

    **추출 예시:**

    질문: "빌리프와 VT의 최근 3개월 보습력 비교"
    → parsed_entities: {
        "brands": ["빌리프", "VT"],
        "products": [],
        "attributes": ["보습력"],
        "period": {"type": "recent_months", "value": 3, "display": "최근 3개월"},
        "channels": []
    }

    질문: "마몽드 평점 어때?"
    → parsed_entities: {
        "brands": ["마몽드"],
        "products": [],
        "attributes": ["평점"],
        "period": {},
        "channels": []
    }

    **사용 시점:**
    - 항상 첫 번째로 실행
    - 다른 모든 도구는 이 결과(parsed_entities)를 사용

    Args:
        state: Agent 상태 (user_query 포함)

    Returns:
        실행 완료 메시지 (엔티티는 State에 저장됨)
    """
    # State에서 user_query 읽기
    user_query = state["user_query"]

    # EntityParser 인스턴스 생성
    parser = EntityParser()

    # 엔티티 추출
    entities = parser._extract_entities(user_query)

    # State에 저장
    state["parsed_entities"] = entities

    # 간단한 완료 메시지 반환
    brands_str = ", ".join(entities.get("brands", [])) or "전체"
    attrs_str = ", ".join(entities.get("attributes", [])) or "전체"
    period_str = entities.get("period", {}).get("display", "전체 기간")

    return f"엔티티 추출 완료: 브랜드({brands_str}), 속성({attrs_str}), 기간({period_str})"
