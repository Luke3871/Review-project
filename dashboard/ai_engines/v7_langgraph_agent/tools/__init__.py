#//==============================================================================//#
"""
__init__.py
Tool Registry - V7 Agent가 사용할 모든 Tool 등록

LangGraph ReAct 패턴에서 Agent가 동적으로 선택할 수 있는 도구들을 정의합니다.

last_updated: 2025.11.02
"""
#//==============================================================================//#

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from entity_parser_tool import parse_entities
from capability_detector_tool import detect_capability
from sql_generator_tool import generate_sql
from executor_tool import execute_sql
from output_generator_tool import generate_output
from visualization_tool import generate_visualization


# Tool Registry: Agent가 사용할 수 있는 모든 도구
ALL_TOOLS = [
    parse_entities,
    detect_capability,
    generate_sql,
    execute_sql,
    generate_output,
    generate_visualization  # 선택적 Tool (사용자가 요청 시)
]


# Tool 설명 (디버깅/로깅용)
TOOL_DESCRIPTIONS = {
    "parse_entities": "사용자 질문에서 엔티티 추출 (브랜드, 제품, 속성, 기간, 채널)",
    "detect_capability": "분석 전략 결정 (data_scope, aggregation_type 등)",
    "generate_sql": "SQL 쿼리 생성",
    "execute_sql": "SQL 쿼리 실행",
    "generate_output": "최종 텍스트 리포트 생성",
    "generate_visualization": "데이터 시각화 차트 이미지 생성 (사용자 요청 시)"
}


# Tool 실행 순서 가이드 (Agent가 참고하도록)
RECOMMENDED_TOOL_FLOW = """
**권장 실행 순서:**

1. parse_entities
   → 사용자 질문 분석 및 엔티티 추출

2. detect_capability
   → 분석 전략 결정 (어느 테이블 사용할지, 어떻게 집계할지)

3. generate_sql
   → SQL 쿼리 생성 (1개 또는 2개)

4. execute_sql
   → SQL 실행 및 결과 반환

5. generate_visualization (선택적)
   → 사용자가 "그래프", "차트", "시각화" 요청 시에만 실행
   → 시계열/비교 데이터를 차트 이미지로 생성

6. generate_output
   → 최종 텍스트 리포트 생성

**주의사항:**
- 각 Tool의 출력은 다음 Tool의 입력으로 사용됨
- generate_sql은 detect_capability의 data_scope에 따라 1개 또는 2개 SQL 생성
- execute_sql은 모든 SQL을 실행하고 통합 결과 반환
- generate_visualization은 사용자가 명시적으로 요청했을 때만 실행 (선택적)
- generate_output은 사용자 의도에 맞게 적절한 수준의 리포트 생성
"""


def get_tool_by_name(tool_name: str):
    """
    Tool 이름으로 Tool 객체 가져오기

    Args:
        tool_name: Tool 이름

    Returns:
        Tool 객체 또는 None
    """
    tool_map = {tool.name: tool for tool in ALL_TOOLS}
    return tool_map.get(tool_name)


def list_available_tools():
    """
    사용 가능한 모든 Tool 목록 반환

    Returns:
        Tool 이름 리스트
    """
    return [tool.name for tool in ALL_TOOLS]


__all__ = [
    "ALL_TOOLS",
    "TOOL_DESCRIPTIONS",
    "RECOMMENDED_TOOL_FLOW",
    "get_tool_by_name",
    "list_available_tools",
    "parse_entities",
    "detect_capability",
    "generate_sql",
    "execute_sql",
    "generate_output",
    "generate_visualization"
]
