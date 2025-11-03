#//==============================================================================//#
"""
state_validator.py
V6 LangGraph Agent State 검증

AgentState의 일관성과 정확성을 검증하여 에러 조기 감지

last_updated: 2025.11.02
"""
#//==============================================================================//#

from typing import List, Dict, Any, Set
from .state import AgentState


# AgentState의 모든 필드 (타입 체크용)
VALID_STATE_FIELDS: Set[str] = {
    # 기본 필드
    "user_query",
    "ui_callback",
    "conversation_history",  # 대화 맥락 유지

    # 워크플로우 필드
    "parsed_entities",
    "capabilities",
    "complexity",
    "sub_questions",
    "sql_queries",
    "query_results",
    "response_plan",
    "outputs",
    "final_response",

    # 메시지/에러
    "messages",
    "error",

    # Debug 모드 (Phase 2: UI 피드백 개선)
    "debug_mode",
    "debug_traces",
    "sql_metadata",

    # 이미지 생성 워크플로우
    "workflow_type",
    "source_product_image",
    "image_analysis",
    "design_keywords",
    "daiso_channel_summary",
    "design_prompt",
    "generated_images"
}


# 각 노드가 생성해야 하는 필수 필드
NODE_REQUIRED_OUTPUTS: Dict[str, List[str]] = {
    "entity_parser": ["parsed_entities"],
    "capability_detector": ["capabilities"],
    "complexity_classifier": ["complexity"],
    "question_decomposer": ["sub_questions"],
    "sql_generator": ["sql_queries"],
    "executor": ["query_results"],
    "sql_refiner": ["sql_queries"],  # 재생성
    "response_planner": ["response_plan"],
    "output_generator": ["outputs"],
    "synthesizer": ["final_response"],
    "image_prompt_generator": ["image_prompt"],
    "image_generator": ["generated_images"]
}


def validate_state(state: AgentState, node_name: str = None) -> List[str]:
    """
    AgentState 검증

    Args:
        state: 검증할 AgentState
        node_name: 노드 이름 (출력 필드 검증 시 필요)

    Returns:
        에러 메시지 리스트 (비어있으면 정상)

    Example:
        ```python
        errors = validate_state(state, "EntityParser")
        if errors:
            logger.error(f"State validation failed: {errors}")
            raise ValidationError("EntityParser", "; ".join(errors))
        ```
    """
    errors = []

    # 1. 필수 필드 존재 확인
    if "user_query" not in state or not state["user_query"]:
        errors.append("Missing required field: user_query")

    # 2. 잘못된 필드명 체크 (오타 감지)
    for field in state.keys():
        if field not in VALID_STATE_FIELDS:
            errors.append(f"Unknown field: {field} (possible typo?)")

    # 3. 타입 검증
    type_errors = _validate_types(state)
    errors.extend(type_errors)

    # 4. 노드별 출력 검증 (node_name이 있을 때만)
    if node_name and node_name in NODE_REQUIRED_OUTPUTS:
        output_errors = _validate_node_output(state, node_name)
        errors.extend(output_errors)

    return errors


def _validate_types(state: AgentState) -> List[str]:
    """
    State 필드 타입 검증

    주요 필드들의 타입이 올바른지 확인
    """
    errors = []

    # parsed_entities: Dict
    if "parsed_entities" in state and state["parsed_entities"] is not None:
        if not isinstance(state["parsed_entities"], dict):
            errors.append(f"parsed_entities must be Dict, got {type(state['parsed_entities'])}")

    # capabilities: Dict
    if "capabilities" in state and state["capabilities"] is not None:
        if not isinstance(state["capabilities"], dict):
            errors.append(f"capabilities must be Dict, got {type(state['capabilities'])}")

    # complexity: Dict
    if "complexity" in state and state["complexity"] is not None:
        if not isinstance(state["complexity"], dict):
            errors.append(f"complexity must be Dict, got {type(state['complexity'])}")

    # sub_questions: List[Dict]
    if "sub_questions" in state and state["sub_questions"] is not None:
        if not isinstance(state["sub_questions"], list):
            errors.append(f"sub_questions must be List[Dict], got {type(state['sub_questions'])}")

    # sql_queries: List[Dict]
    if "sql_queries" in state and state["sql_queries"] is not None:
        if not isinstance(state["sql_queries"], list):
            errors.append(f"sql_queries must be List[Dict], got {type(state['sql_queries'])}")
        elif state["sql_queries"] and not isinstance(state["sql_queries"][0], dict):
            errors.append(f"sql_queries items must be Dict, got {type(state['sql_queries'][0])}")

    # query_results: Dict
    if "query_results" in state and state["query_results"] is not None:
        if not isinstance(state["query_results"], dict):
            errors.append(f"query_results must be Dict, got {type(state['query_results'])}")

    # response_plan: Dict
    if "response_plan" in state and state["response_plan"] is not None:
        if not isinstance(state["response_plan"], dict):
            errors.append(f"response_plan must be Dict, got {type(state['response_plan'])}")

    # outputs: Dict
    if "outputs" in state and state["outputs"] is not None:
        if not isinstance(state["outputs"], dict):
            errors.append(f"outputs must be Dict, got {type(state['outputs'])}")

    # final_response: str
    if "final_response" in state and state["final_response"] is not None:
        if not isinstance(state["final_response"], str):
            errors.append(f"final_response must be str, got {type(state['final_response'])}")

    # messages: List[Dict]
    if "messages" in state and state["messages"] is not None:
        if not isinstance(state["messages"], list):
            errors.append(f"messages must be List[Dict], got {type(state['messages'])}")

    # error: Dict
    if "error" in state and state["error"] is not None:
        if not isinstance(state["error"], dict):
            errors.append(f"error must be Dict, got {type(state['error'])}")

    return errors


def _validate_node_output(state: AgentState, node_name: str) -> List[str]:
    """
    노드별 출력 필드 검증

    각 노드가 생성해야 하는 필드가 State에 올바르게 저장되었는지 확인
    """
    errors = []

    required_fields = NODE_REQUIRED_OUTPUTS.get(node_name, [])

    for field in required_fields:
        if field not in state:
            errors.append(f"{node_name} must output {field}, but field is missing")
        elif state[field] is None:
            errors.append(f"{node_name} must output {field}, but value is None")

    return errors


def validate_entity_structure(parsed_entities: Dict[str, Any]) -> List[str]:
    """
    parsed_entities 구조 상세 검증

    EntityParser 출력이 올바른 형식인지 확인
    """
    errors = []

    if not parsed_entities:
        return ["parsed_entities is empty"]

    # 필수 키 존재 확인
    required_keys = ["brands", "products", "attributes", "period", "channels"]
    for key in required_keys:
        if key not in parsed_entities:
            errors.append(f"parsed_entities missing key: {key}")

    # brands, products, attributes, channels는 리스트여야 함
    for key in ["brands", "products", "attributes", "channels"]:
        if key in parsed_entities and not isinstance(parsed_entities[key], list):
            errors.append(f"parsed_entities['{key}'] must be List, got {type(parsed_entities[key])}")

    # period는 딕셔너리여야 함
    if "period" in parsed_entities and not isinstance(parsed_entities["period"], dict):
        errors.append(f"parsed_entities['period'] must be Dict, got {type(parsed_entities['period'])}")

    return errors


def validate_sql_query_structure(sql_query: Dict[str, Any]) -> List[str]:
    """
    sql_queries 각 항목의 구조 검증

    SQLGenerator 출력 형식 확인
    """
    errors = []

    if not sql_query:
        return ["sql_query is empty"]

    # 필수 키
    required_keys = ["sql"]
    for key in required_keys:
        if key not in sql_query:
            errors.append(f"sql_query missing required key: {key}")

    # sql은 문자열이어야 함
    if "sql" in sql_query and not isinstance(sql_query["sql"], str):
        errors.append(f"sql_query['sql'] must be str, got {type(sql_query['sql'])}")

    # sql이 비어있으면 안 됨
    if "sql" in sql_query and not sql_query["sql"].strip():
        errors.append("sql_query['sql'] is empty string")

    return errors


# 편의 함수
def assert_state_valid(state: AgentState, node_name: str = None):
    """
    State 검증 후 에러 발생 시 예외 발생

    Args:
        state: 검증할 AgentState
        node_name: 노드 이름

    Raises:
        ValueError: State 검증 실패 시

    Example:
        ```python
        # 노드 끝에서 호출
        state["parsed_entities"] = entities
        assert_state_valid(state, "EntityParser")
        return state
        ```
    """
    errors = validate_state(state, node_name)
    if errors:
        raise ValueError(f"State validation failed: {'; '.join(errors)}")
