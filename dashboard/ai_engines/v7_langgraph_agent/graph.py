#//==============================================================================//#
"""
graph.py
LangGraph 구성 - ReAct Agent 그래프 정의

Agent 노드와 Tool 노드를 연결하여 실제 동작하는 그래프를 생성합니다.

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Callable, Optional

import sys
from pathlib import Path

# V7 imports
v7_dir = str(Path(__file__).parent)
sys.path.insert(0, v7_dir)
sys.path.insert(0, str(Path(v7_dir) / 'nodes'))
sys.path.insert(0, str(Path(v7_dir) / 'tools'))

from state import AgentState
from config import AGENT_CONFIG
from tools import ALL_TOOLS
from agent import create_agent_node, should_continue


def create_graph(ui_callback: Optional[Callable] = None):
    """
    LangGraph 그래프 생성

    **그래프 구조:**

    START → agent → should_continue → tools → agent → ...
                          ↓
                         END

    - agent: LLM이 다음 Tool 선택
    - should_continue: Tool 호출 있으면 tools로, 없으면 END
    - tools: 선택된 Tool 실행 (ToolNode)

    Args:
        ui_callback: UI 업데이트 콜백 (Streamlit용)

    Returns:
        컴파일된 LangGraph
    """
    # StateGraph 초기화
    workflow = StateGraph(AgentState)

    # 1. Agent 노드 추가
    agent_node = create_agent_node()
    workflow.add_node("agent", agent_node)

    # 2. Tool 노드 추가 (LangGraph의 ToolNode 사용)
    tool_node = ToolNode(ALL_TOOLS)
    workflow.add_node("tools", tool_node)

    # 3. 엣지 설정
    # START → agent
    workflow.set_entry_point("agent")

    # agent → should_continue (conditional edge)
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # Tool 호출 있으면 tools 노드로
            "end": END         # Tool 호출 없으면 종료
        }
    )

    # tools → agent (다시 Agent로 돌아가서 다음 Tool 선택)
    workflow.add_edge("tools", "agent")

    # 4. 그래프 컴파일
    graph = workflow.compile()

    return graph


def run_agent(user_query: str, ui_callback: Optional[Callable] = None) -> dict:
    """
    Agent 실행 (편의 함수)

    사용자 질문을 받아서 Agent를 실행하고 최종 결과를 반환합니다.

    **실행 흐름:**

    1. 초기 상태 생성 (user_query, ui_callback 포함)
    2. 그래프 생성
    3. 그래프 실행 (invoke)
    4. 최종 상태 반환

    Args:
        user_query: 사용자 질문
        ui_callback: UI 업데이트 콜백

    Returns:
        최종 상태 (AgentState)

    **사용 예시:**

    ```python
    # 기본 사용
    result = run_agent("빌리프 보습력 어때?")
    print(result["messages"][-1].content)

    # Streamlit UI callback 포함
    def streamlit_callback(data):
        if data["type"] == "thought":
            st.expander("💭 Thought").write(data["content"])

    result = run_agent("빌리프 평점 알려줘", ui_callback=streamlit_callback)
    ```
    """
    # 초기 상태
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "user_query": user_query,
        "ui_callback": ui_callback,
        "parsed_entities": None,
        "capabilities": None,
        "sql_queries": None,
        "query_results": None,
        "outputs": None,
        "current_step": 0,
        "max_steps": AGENT_CONFIG["max_iterations"],
        "final_response": None,
        "error": None
    }

    # 그래프 생성 및 실행
    graph = create_graph(ui_callback)
    final_state = graph.invoke(initial_state)

    return final_state


def stream_agent(user_query: str, ui_callback: Optional[Callable] = None):
    """
    Agent 스트리밍 실행

    Agent의 각 단계를 스트리밍으로 반환합니다.
    실시간 UI 업데이트가 필요한 경우 사용합니다.

    Args:
        user_query: 사용자 질문
        ui_callback: UI 업데이트 콜백

    Yields:
        각 단계의 상태

    **사용 예시:**

    ```python
    for state in stream_agent("빌리프 보습력 어때?"):
        print(f"Step {state['current_step']}: {state['messages'][-1]}")
    ```
    """
    # 초기 상태
    initial_state = {
        "messages": [{"role": "user", "content": user_query}],
        "user_query": user_query,
        "ui_callback": ui_callback,
        "parsed_entities": None,
        "capabilities": None,
        "sql_queries": None,
        "query_results": None,
        "outputs": None,
        "current_step": 0,
        "max_steps": AGENT_CONFIG["max_iterations"],
        "final_response": None,
        "error": None
    }

    # 그래프 생성
    graph = create_graph(ui_callback)

    # 스트리밍 실행
    for state in graph.stream(initial_state):
        yield state
