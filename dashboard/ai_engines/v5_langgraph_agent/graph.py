"""
LangGraph Workflow - V5 Agent Graph

5개 노드를 LangGraph로 연결하여 전체 워크플로우를 구성합니다.

워크플로우:
START → Parser → Validation → Router → Executor → Synthesizer → END

각 노드는 순차적으로 실행되며, AgentState를 업데이트합니다.
"""

from typing import Dict
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    ParserNode,
    ValidationNode,
    RouterNode,
    ExecutorNode,
    SynthesizerNode
)


class V5Agent:
    """
    V5 LangGraph Agent

    14개 Tool과 5개 Node로 구성된 리뷰 분석 에이전트
    """

    def __init__(
        self,
        parser_llm: str = "gpt-4o-mini",
        synthesizer_llm: str = "gpt-4o"
    ):
        """
        Args:
            parser_llm: Parser Node에서 사용할 LLM 모델
            synthesizer_llm: Synthesizer Node에서 사용할 LLM 모델
        """
        # 노드 인스턴스 생성
        self.parser = ParserNode(llm_model=parser_llm)
        self.validation = ValidationNode()
        self.router = RouterNode()
        self.executor = ExecutorNode()
        self.synthesizer = SynthesizerNode(llm_model=synthesizer_llm)

        # LangGraph 구성
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        LangGraph 워크플로우 구성

        Returns:
            컴파일된 StateGraph
        """
        # StateGraph 생성
        workflow = StateGraph(AgentState)

        # 노드 추가
        workflow.add_node("parser", self.parser)
        workflow.add_node("validation", self.validation)
        workflow.add_node("router", self.router)
        workflow.add_node("executor", self.executor)
        workflow.add_node("synthesizer", self.synthesizer)

        # 엣지 연결 (순차 실행)
        workflow.set_entry_point("parser")
        workflow.add_edge("parser", "validation")
        workflow.add_edge("validation", "router")
        workflow.add_edge("router", "executor")
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("synthesizer", END)

        # 컴파일
        return workflow.compile()

    def run(self, user_query: str) -> Dict:
        """
        사용자 질문에 대한 분석 실행

        Args:
            user_query: 사용자 질문

        Returns:
            최종 AgentState (final_response, messages 포함)
        """
        # 초기 상태
        initial_state = {
            "user_query": user_query,
            "parsed_query": None,
            "data_validation": None,
            "is_fallback": False,
            "fallback_reason": "",
            "selected_tools": None,
            "selection_reason": "",
            "tool_results": None,
            "final_response": "",
            "messages": []
        }

        # 그래프 실행
        final_state = self.graph.invoke(initial_state)

        return final_state

    def stream(self, user_query: str):
        """
        사용자 질문에 대한 분석을 스트리밍으로 실행

        Args:
            user_query: 사용자 질문

        Yields:
            각 노드의 출력 상태
        """
        # 초기 상태
        initial_state = {
            "user_query": user_query,
            "parsed_query": None,
            "data_validation": None,
            "is_fallback": False,
            "fallback_reason": "",
            "selected_tools": None,
            "selection_reason": "",
            "tool_results": None,
            "final_response": "",
            "messages": []
        }

        # 그래프 스트리밍 실행
        for state_update in self.graph.stream(initial_state):
            yield state_update


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== V5 Agent Graph 테스트 ===\n")

    # Agent 인스턴스 생성
    agent = V5Agent()

    # 테스트 질문들
    test_queries = [
        "빌리프 브랜드 속성 분석해줘",
        "VT 시카크림이랑 라로슈포제 시카플라스트 비교해줘",
        "올리브영에서 기획전 반응 어때?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {query}")
        print("=" * 80)

        # 스트리밍으로 실행 (노드별 출력 확인)
        print("\n[워크플로우 진행 상황]\n")

        for state_update in agent.stream(query):
            # 현재 노드명 추출
            node_name = list(state_update.keys())[0]
            node_state = state_update[node_name]

            # messages 확인
            messages = node_state.get("messages", [])
            if messages:
                latest_msg = messages[-1]
                print(f"[{latest_msg['node']}] {latest_msg['status']}: {latest_msg['content'][:100]}...")

        print("\n[최종 결과]\n")

        # 전체 실행 (최종 상태 확인)
        final_state = agent.run(query)

        print(f"최종 응답:\n{final_state['final_response'][:500]}...")
        print(f"\n처리된 메시지 수: {len(final_state['messages'])}")
