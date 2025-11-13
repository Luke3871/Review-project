#//==============================================================================//#
"""
state.py
V6 에이전트 상태 정의

last_updated: 2025.10.29
"""
#//==============================================================================//#

from typing import TypedDict, Optional, List, Dict, Any, Callable

class AgentState(TypedDict):
    """V6 에이전트 상태"""

    # 1. 입력
    user_query: str
    ui_callback: Optional[Callable]  # Streamlit UI 업데이트 콜백
    conversation_history: Optional[List[Dict[str, str]]]  # 대화 히스토리 (맥락 유지)
    # [
    #     {"role": "user", "content": "빌리프 보습력 어때?"},
    #     {"role": "assistant", "content": "빌리프 제품의 보습력은..."},
    #     {"role": "user", "content": "그럼 기획에 대해서는?"}  # 이전 맥락 참조
    # ]

    # 2. EntityParser 출력
    parsed_entities: Optional[Dict[str, Any]]
    # {
    #     "brands": ["빌리프", "VT"],
    #     "products": ["모이스춰라이징밤"],
    #     "attributes": ["보습력", "발림성"],
    #     "period": {"start": "2025-08-01", "end": "2025-10-29", "display": "최근 3개월"},
    #     "channels": ["OliveYoung"]
    # }

    # 3. CapabilityDetector 출력
    capabilities: Optional[Dict[str, Any]]
    # {
    #     "data_scope": "preprocessed_reviews",  # reviews | preprocessed_reviews
    #     "aggregation_type": "comparison",       # time_series | comparison | distribution | keyword_frequency
    #     "group_by": "brand",                    # brand | product | channel | period
    #     "analysis_depth": "attribute",          # overview | attribute | sentiment | keyword | pros_cons
    #     "metric": "rating"                      # rating | count | percentage
    # }

    # 3-1. ComplexityClassifier 출력
    complexity: Optional[Dict[str, Any]]
    # {
    #     "level": "simple",  # simple | medium | complex
    #     "score": 1,
    #     "reasoning": "...",
    #     "routing_path": "direct"  # direct | decompose | refine
    # }

    # 3-2. QuestionDecomposer 출력 (복잡한 질문만)
    sub_questions: Optional[List[Dict[str, Any]]]
    # [
    #     {
    #         "sub_question": "...",
    #         "purpose": "...",
    #         "dependency": None or [1, 2]
    #     }
    # ]

    # 4. SQLGenerator 출력
    sql_queries: Optional[List[Dict[str, Any]]]
    # [
    #     {
    #         "question_id": 1,
    #         "sub_question": "...",
    #         "sql": "SELECT ...",
    #         "estimated_rows": 150,
    #         "uses_index": True,
    #         "explanation": "..."
    #     }
    # ]

    # 5. Executor 출력
    query_results: Optional[Dict[str, Any]]
    # {
    #     "results": [...],  # 쿼리 결과 리스트
    #     "total_queries": 2,
    #     "total_duration": 1.05,
    #     "data_characteristics": {
    #         "successful_queries": 2,
    #         "total_rows": 150,
    #         "time_series": True,
    #         "multi_entity": True,
    #         "has_distribution": False,
    #         "keyword_count": 25
    #     }
    # }

    # 6. ResponsePlanner 출력
    response_plan: Optional[Dict[str, Any]]
    # {
    #     "primary_format": "visualization",  # text | table | visualization
    #     "components": [
    #         {"type": "summary_text", "priority": 1},
    #         {"type": "comparison_table", "priority": 2},
    #         {"type": "bar_chart", "priority": 3}
    #     ],
    #     "visualization_strategy": "auto",  # auto | suggest | none
    #     "confidence": 0.92
    # }

    # 7. OutputGenerator 출력
    outputs: Optional[Dict[str, Any]]
    # {
    #     "text": "빌리프와 VT의 보습력 비교입니다...",
    #     "table": {...},  # DataFrame or dict
    #     "visualizations": [
    #         {"type": "bar_chart", "data": {...}, "config": {...}}
    #     ],
    #     "suggestions": ["다른 속성도 비교하시겠어요?"]
    # }

    # 8. 최종 출력
    final_response: Optional[str]

    # 9. 진행상황 메시지 (ProgressTracker가 기록)
    messages: List[Dict[str, Any]]
    # [
    #     {
    #         "node": "EntityParser",
    #         "status": "completed",
    #         "content": "질문 분석 완료",
    #         "substeps": [...],
    #         "duration": 0.5,
    #         "timestamp": "2025-10-29T10:30:15"
    #     }
    # ]

    # 10. 에러 처리
    error: Optional[Dict[str, Any]]
    # {
    #     "node": "SQLGenerator",
    #     "error_type": "timeout",
    #     "message": "쿼리 실행 시간 초과",
    #     "suggestion": "더 구체적인 조건을 추가해보세요"
    # }

    # 11. Debug 모드 (Phase 2: UI 피드백 개선)
    debug_mode: Optional[bool]  # Debug 모드 활성화 여부
    debug_traces: Optional[List[Dict[str, Any]]]  # Debug 추적 정보
    sql_metadata: Optional[List[Dict[str, Any]]]  # SQL 쿼리 메타데이터 (UI 표시용)

    # 12. 이미지 생성 워크플로우 (AI Visual Agent)
    workflow_type: Optional[str]  # "sql" | "image_generation"
    source_product_image: Optional[str]  # 올리브영 제품 이미지 경로
    design_keywords: Optional[List[str]]  # 올리브영 제품 리뷰 키워드
    daiso_channel_summary: Optional[str]  # Daiso 채널 특성 요약 (리뷰 기반)
    design_prompt: Optional[str]  # Gemini (Nano Banana) 프롬프트
    generated_images: Optional[List[Dict[str, Any]]]  # 생성된 이미지 정보
    # [
    #     {
    #         "url": "https://...",
    #         "local_path": "dashboard/generated_images/daiso/vt_reedle_shot_20251101.png",
    #         "revised_prompt": "..."
    #     }
    # ]
