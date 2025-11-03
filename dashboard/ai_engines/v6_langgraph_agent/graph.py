#//==============================================================================//#
"""
graph.py
LangGraph 워크플로우 정의

last_updated: 2025.10.29
"""
#//==============================================================================//#

from langgraph.graph import StateGraph, END
from typing import Dict, Any

from .state import AgentState
from .nodes.entity_parser import EntityParser
from .nodes.capability_detector import CapabilityDetector
from .nodes.complexity_classifier import ComplexityClassifier
from .nodes.question_decomposer import QuestionDecomposer
from .nodes.sql_generator import SQLGenerator
from .nodes.executor import Executor
from .nodes.sql_refiner import SQLRefiner
from .nodes.response_planner import ResponsePlanner
from .nodes.output_generator import OutputGenerator
from .nodes.synthesizer import Synthesizer
from .nodes.image_prompt_generator import ImagePromptGenerator
from .nodes.image_generator import ImageGenerator


def create_graph() -> StateGraph:
    """
    V6 LangGraph 워크플로우 생성

    Returns:
        StateGraph: 실행 가능한 그래프
    """
    # 1. 노드 인스턴스 생성
    entity_parser = EntityParser()
    capability_detector = CapabilityDetector()
    complexity_classifier = ComplexityClassifier()
    question_decomposer = QuestionDecomposer()
    sql_generator = SQLGenerator()
    executor = Executor()
    sql_refiner = SQLRefiner()
    response_planner = ResponsePlanner()
    output_generator = OutputGenerator()
    synthesizer = Synthesizer()
    image_prompt_generator = ImagePromptGenerator()
    image_generator = ImageGenerator()

    # 2. StateGraph 생성
    workflow = StateGraph(AgentState)

    # 3. 노드 추가
    workflow.add_node("entity_parser", entity_parser.parse)
    workflow.add_node("capability_detector", capability_detector.detect)
    workflow.add_node("complexity_classifier", complexity_classifier.classify)
    workflow.add_node("question_decomposer", question_decomposer.decompose)
    workflow.add_node("sql_generator", sql_generator.generate)
    workflow.add_node("executor", executor.execute)
    workflow.add_node("sql_refiner", sql_refiner.refine)
    workflow.add_node("response_planner", response_planner.plan)
    workflow.add_node("output_generator", output_generator.generate)
    workflow.add_node("synthesizer", synthesizer.synthesize)
    # 이미지 생성 워크플로우
    workflow.add_node("image_prompt_generator", image_prompt_generator.generate)
    workflow.add_node("image_generator", image_generator.generate)

    # 4. 엣지 정의
    # 시작 → EntityParser
    workflow.set_entry_point("entity_parser")

    # EntityParser → 워크플로우 라우팅 (이미지 생성 vs SQL)
    workflow.add_conditional_edges(
        "entity_parser",
        route_workflow_type,
        {
            "image_generation": "image_prompt_generator",
            "sql": "capability_detector",
            "error": END
        }
    )

    # CapabilityDetector → ComplexityClassifier
    workflow.add_edge("capability_detector", "complexity_classifier")

    # ComplexityClassifier → QuestionDecomposer (복잡도에 따라)
    workflow.add_conditional_edges(
        "complexity_classifier",
        route_by_complexity,
        {
            "decompose": "question_decomposer",
            "sql_generator": "sql_generator"
        }
    )

    # QuestionDecomposer → SQLGenerator
    workflow.add_edge("question_decomposer", "sql_generator")

    # SQLGenerator → Executor
    workflow.add_edge("sql_generator", "executor")

    # Executor → SQLRefiner (복잡도에 따라)
    workflow.add_conditional_edges(
        "executor",
        route_to_refiner,
        {
            "refine": "sql_refiner",
            "response_planner": "response_planner"
        }
    )

    # SQLRefiner → ResponsePlanner
    workflow.add_edge("sql_refiner", "response_planner")

    # ResponsePlanner → OutputGenerator
    workflow.add_edge("response_planner", "output_generator")

    # OutputGenerator → Synthesizer
    workflow.add_edge("output_generator", "synthesizer")

    # Synthesizer → END
    workflow.add_edge("synthesizer", END)

    # 이미지 생성 워크플로우
    # ImagePromptGenerator → ImageGenerator
    workflow.add_edge("image_prompt_generator", "image_generator")

    # ImageGenerator → Synthesizer
    workflow.add_edge("image_generator", "synthesizer")

    # 5. 컴파일
    return workflow.compile()


def route_workflow_type(state: AgentState) -> str:
    """
    워크플로우 타입 라우팅 (이미지 생성 vs SQL)

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    # 에러 체크
    if state.get("error"):
        return "error"

    # 사용자 쿼리에서 이미지 생성 키워드 감지
    query = state.get("user_query", "").lower()
    image_keywords = ["디자인", "시안", "이미지", "패키지", "생성", "만들어", "다이소", "버전"]

    if any(kw in query for kw in image_keywords):
        state["workflow_type"] = "image_generation"
        return "image_generation"
    else:
        state["workflow_type"] = "sql"
        return "sql"


def route_by_complexity(state: AgentState) -> str:
    """
    복잡도에 따라 라우팅

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    complexity = state.get("complexity", {}).get("level", "medium")

    # Simple 질문은 decompose 스킵
    if complexity == "simple":
        return "sql_generator"
    else:
        return "decompose"


def route_to_refiner(state: AgentState) -> str:
    """
    실패한 쿼리 있으면 Refiner로, 없으면 ResponsePlanner로

    Args:
        state: 현재 상태

    Returns:
        다음 노드 이름
    """
    complexity = state.get("complexity", {}).get("level", "medium")
    query_results = state.get("query_results", {}).get("results", [])

    # Complex 질문이고 실패한 쿼리가 있으면 Refiner 실행
    failed_queries = [r for r in query_results if not r.get("success", True)]

    if complexity == "complex" and failed_queries:
        return "refine"
    else:
        return "response_planner"
