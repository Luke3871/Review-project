#//==============================================================================//#
"""
state.py
V7 Agent 상태 정의 - 메시지 히스토리 기반

last_updated: 2025.11.02
"""
#//==============================================================================//#

from typing import TypedDict, Optional, List, Dict, Any, Callable, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """V7 Agent 상태 - ReAct 패턴"""

    # ============================================================================
    # 1. 핵심: 메시지 히스토리 (LangGraph 권장 방식)
    # ============================================================================
    messages: Annotated[List[BaseMessage], add_messages]
    """
    LangGraph의 add_messages를 사용하여 자동으로 메시지 추가/관리

    예시:
    [
        HumanMessage(content="빌리프 보습력 어때?"),
        AIMessage(content="Thought: 엔티티 추출 필요\nAction: parse_entities\n...", tool_calls=[...]),
        ToolMessage(content='{"brands": ["빌리프"], ...}', tool_call_id="call_123"),
        ...
    ]
    """

    # ============================================================================
    # 2. 사용자 입력
    # ============================================================================
    user_query: str
    ui_callback: Optional[Callable]
    """Streamlit UI 업데이트 콜백"""

    # ============================================================================
    # 3. Tool 실행 결과 캐시 (각 Tool이 업데이트)
    # ============================================================================
    parsed_entities: Optional[Dict[str, Any]]
    """
    엔티티 추출 결과

    예시:
    {
        "brands": ["빌리프", "VT"],
        "products": ["모이스춰라이징밤"],
        "attributes": ["보습력", "발림성"],
        "period": {"start": "2025-08-01", "end": "2025-10-29", "display": "최근 3개월"},
        "channels": ["OliveYoung"]
    }
    """

    capabilities: Optional[Dict[str, Any]]
    """
    분석 전략 결정 결과

    예시:
    {
        "data_scope": "preprocessed_reviews",  # reviews | preprocessed_reviews | join
        "aggregation_type": "comparison",       # time_series | comparison | distribution | keyword_frequency
        "group_by": "brand",                    # brand | product | channel | period
        "analysis_depth": "attribute",          # overview | attribute | sentiment | keyword | pros_cons
        "metric": "rating"                      # rating | count | percentage
    }
    """

    sql_queries: Optional[List[Dict[str, Any]]]
    """
    SQL 쿼리 생성 결과

    예시:
    [
        {
            "question_id": 1,
            "sub_question": "...",
            "sql": "SELECT ...",
            "estimated_rows": 150,
            "uses_index": True,
            "explanation": "..."
        }
    ]
    """

    query_results: Optional[Dict[str, Any]]
    """
    SQL 실행 결과

    예시:
    {
        "results": [...],
        "total_queries": 2,
        "total_duration": 1.05,
        "data_characteristics": {...}
    }
    """

    outputs: Optional[Dict[str, Any]]
    """
    텍스트/차트 생성 결과

    예시:
    {
        "text": "빌리프와 VT의 보습력 비교입니다...",
        "table": {...},
        "visualizations": [...]
    }
    """

    # ============================================================================
    # 4. Agent 제어 필드
    # ============================================================================
    current_step: int
    """현재 ReAct 루프 반복 횟수"""

    max_steps: int
    """최대 반복 제한 (무한루프 방지)"""

    # ============================================================================
    # 5. 최종 출력
    # ============================================================================
    final_response: Optional[str]
    """사용자에게 전달할 최종 답변"""

    # ============================================================================
    # 6. 에러 처리
    # ============================================================================
    error: Optional[Dict[str, Any]]
    """
    에러 정보

    예시:
    {
        "tool": "execute_sql",
        "error_type": "timeout",
        "message": "쿼리 실행 시간 초과",
        "suggestion": "더 구체적인 조건을 추가해보세요"
    }
    """

    # ============================================================================
    # 7. 이미지 생성 워크플로우 (선택적)
    # ============================================================================
    workflow_type: Optional[str]
    """워크플로우 타입: "sql" | "image_generation" """

    source_product_image: Optional[str]
    """올리브영 제품 이미지 경로"""

    design_keywords: Optional[List[str]]
    """올리브영 제품 리뷰 키워드"""

    design_prompt: Optional[str]
    """Gemini 이미지 생성 프롬프트"""

    generated_images: Optional[List[Dict[str, Any]]]
    """
    생성된 이미지 정보

    예시:
    [
        {
            "url": "https://...",
            "local_path": "dashboard/generated_images/daiso/vt_reedle_shot_20251101.png",
            "revised_prompt": "..."
        }
    ]
    """
