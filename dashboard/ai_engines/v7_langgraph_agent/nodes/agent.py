#//==============================================================================//#
"""
agent.py
ReAct Agent 노드 - LLM이 Tool을 동적으로 선택하고 실행

LangGraph의 ReAct 패턴을 사용하여 Agent가 사용자 질문을 분석하고
필요한 Tool을 순차적으로 호출하여 최종 답변을 생성합니다.

last_updated: 2025.11.02
"""
#//==============================================================================//#

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

import sys
from pathlib import Path

# V7 imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from state import AgentState
from config import AGENT_CONFIG
from tools import ALL_TOOLS, RECOMMENDED_TOOL_FLOW


def create_agent_node():
    """
    ReAct Agent 노드 생성

    Returns:
        Agent 노드 함수
    """
    # LLM 초기화 (GPT-4o for reasoning)
    llm = ChatOpenAI(
        model=AGENT_CONFIG["model"],
        temperature=AGENT_CONFIG["temperature"],
        max_tokens=AGENT_CONFIG["max_tokens"]
    )

    # Tool binding
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        """
        Agent 노드 - LLM이 다음 행동 결정

        이 노드는 현재 상태를 분석하고 다음에 실행할 Tool을 선택합니다.

        **동작 방식:**

        1. 현재 대화 히스토리 확인
        2. System prompt로 Agent의 역할과 사용 가능한 Tool 안내
        3. LLM이 다음 Tool 선택 (tool_calls 생성)
        4. Tool 선택이 없으면 최종 답변 생성

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트된 상태 (messages에 AIMessage 추가)
        """
        # System prompt
        system_message = SystemMessage(content=f"""당신은 LG생활건강 마케팅팀을 위한 데이터 분석 Agent입니다.

사용자의 질문을 분석하고, 필요한 도구를 순차적으로 호출하여 최종 답변을 생성하세요.

**사용 가능한 도구:**

{RECOMMENDED_TOOL_FLOW}

**작업 흐름:**

1. 사용자 질문을 받으면 먼저 parse_entities 도구로 엔티티 추출
2. detect_capability 도구로 분석 전략 결정
3. generate_sql 도구로 SQL 쿼리 생성
4. execute_sql 도구로 쿼리 실행
5. generate_output 도구로 최종 리포트 생성

**중요 원칙:**

- 도구는 순서대로 호출하세요 (각 도구의 출력이 다음 도구의 입력)
- 한 번에 하나의 도구만 호출하세요 (parallel_tool_calls=False)
- 모든 도구 실행이 끝나면 generate_output의 결과를 사용자에게 전달
- 에러 발생 시 사용자에게 명확히 설명

**현재 상태:**
- 현재 단계: {state.get('current_step', 0)}/{state.get('max_steps', AGENT_CONFIG['max_iterations'])}
- 캐시된 데이터:
  * parsed_entities: {'있음' if state.get('parsed_entities') else '없음'}
  * capabilities: {'있음' if state.get('capabilities') else '없음'}
  * sql_queries: {'있음' if state.get('sql_queries') else '없음'}
  * query_results: {'있음' if state.get('query_results') else '없음'}
""")

        # 메시지 히스토리 준비
        messages = [system_message] + state["messages"]

        # LLM 호출
        response = llm_with_tools.invoke(messages)

        # 상태 업데이트
        state["messages"].append(response)
        state["current_step"] = state.get("current_step", 0) + 1

        # UI callback (Thought 표시)
        if AGENT_CONFIG["show_thoughts"] and state.get("ui_callback"):
            callback = state["ui_callback"]

            # Tool 호출이 있으면 표시
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_name = response.tool_calls[0]['name']
                callback({
                    "type": "thought",
                    "content": f"💭 다음 도구 선택: {tool_name}",
                    "step": state["current_step"]
                })
            else:
                # 최종 답변 생성 중
                callback({
                    "type": "thought",
                    "content": "💭 최종 답변 생성 중...",
                    "step": state["current_step"]
                })

        return state

    return agent_node


def should_continue(state: AgentState) -> str:
    """
    다음 노드 결정 (Router)

    Agent가 Tool을 호출했는지, 아니면 최종 답변을 생성했는지 판단합니다.

    Args:
        state: 현재 상태

    Returns:
        "tools": Tool 실행 노드로 이동
        "end": 종료 (최종 답변 생성 완료)
    """
    messages = state["messages"]
    last_message = messages[-1]

    # Tool 호출이 있으면 tools 노드로
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # 최대 반복 횟수 초과 체크
    if state.get("current_step", 0) >= state.get("max_steps", AGENT_CONFIG["max_iterations"]):
        # 강제 종료
        if state.get("ui_callback"):
            state["ui_callback"]({
                "type": "error",
                "content": f"⚠️ 최대 반복 횟수({AGENT_CONFIG['max_iterations']})에 도달했습니다."
            })
        return "end"

    # Tool 호출 없으면 종료
    return "end"
