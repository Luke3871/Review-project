"""
V5 LangGraph Agent State 정의

AgentState는 LangGraph 워크플로우에서 사용하는 상태 관리 객체입니다.
질문이 들어와서 최종 답변이 나올 때까지의 모든 정보를 담습니다.
"""

from typing import TypedDict, List, Optional, Dict


class AgentState(TypedDict):
    """
    V5 Agent의 전체 상태를 관리하는 State

    LangGraph의 각 Node는 이 State를 읽고 업데이트합니다.
    """

    # ===== 입력 =====
    user_query: str  # 사용자 질문 원문

    # ===== STEP 1: Parser Node 결과 =====
    parsed_query: Optional[Dict]
    # 예시: {
    #   "brands": ["빌리프"],
    #   "products": ["모이스춰라이징밤"],
    #   "channels": ["올리브영"],
    #   "intent": "attribute_analysis"
    # }

    # ===== STEP 2: Validation Node 결과 =====
    data_validation: Optional[Dict]
    # 예시: {
    #   "count": 45,           # 찾은 리뷰 수
    #   "sufficient": True     # 10개 이상인지
    # }

    is_fallback: bool  # Fallback 발동 여부
    fallback_reason: str  # Fallback 이유 (UI에 경고 표시용)

    # ===== 재질문 관련 =====
    needs_clarification: bool  # 재질문 필요 여부
    suggestions: Optional[List[Dict]]  # 제안할 제품 리스트
    # 예시: [
    #   {"product_name": "빌리프 모이스춰라이징밤 30ml", "review_count": 120, ...},
    #   ...
    # ]
    clarification_type: str  # "product" | "brand" | "channel" | "none"

    # 드롭다운 선택용 후보 리스트
    available_channels: Optional[List[str]]  # 사용 가능한 채널 리스트
    available_brands: Optional[List[str]]  # 사용 가능한 브랜드 리스트
    available_products: Optional[List[str]]  # 사용 가능한 제품 리스트

    # ===== STEP 3: Router Node 결과 =====
    selected_tools: Optional[List[str]]  # 선택된 툴 리스트
    # 예시: ["AttributeTool"] 또는 ["ProsTool", "ConsTool", "SentimentTool"]

    selection_reason: str  # 툴 선택 이유 (설명 가능한 AI)

    # ===== STEP 4: Executor Node 결과 =====
    tool_results: Optional[Dict]
    # 예시: {
    #   "AttributeTool": {"count": 45, "data": {...}},
    #   "SentimentTool": {"count": 45, "data": {...}}
    # }

    # ===== STEP 5: Synthesizer Node 결과 =====
    final_response: str  # 최종 응답 (마크다운 형식)

    # ===== UI 표시용 메시지들 (노드별 출력) =====
    messages: List[Dict]
    # 예시: [
    #   {"step": 1, "title": "질문 파싱 완료", "details": {...}},
    #   {"step": 2, "title": "데이터 확인 완료", "details": {...}},
    #   ...
    # ]
