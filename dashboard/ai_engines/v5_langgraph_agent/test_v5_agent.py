"""
V5 Agent 통합 테스트 스크립트

전체 워크플로우가 정상 작동하는지 테스트합니다.
"""

import sys
import os

# 경로 추가 (ai_engines 디렉토리를 sys.path에 추가)
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_engines_dir = os.path.dirname(current_dir)
sys.path.insert(0, ai_engines_dir)

from v5_langgraph_agent import V5Agent


def test_simple_query():
    """간단한 질문 테스트"""
    print("=" * 80)
    print("테스트 1: 간단한 속성 분석 질문")
    print("=" * 80)

    agent = V5Agent()
    query = "빌리프 브랜드 속성 분석해줘"

    print(f"\n질문: {query}\n")
    print("-" * 80)
    print("워크플로우 실행 중...\n")

    # 스트리밍으로 실행하여 각 노드 출력 확인
    for state_update in agent.stream(query):
        node_name = list(state_update.keys())[0]
        node_state = state_update[node_name]

        messages = node_state.get("messages", [])
        if messages:
            latest_msg = messages[-1]
            status_icon = {
                "processing": "🔄",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌",
                "info": "ℹ️"
            }.get(latest_msg["status"], "•")

            print(f"{status_icon} [{latest_msg['node']}] {latest_msg['status'].upper()}")

            # content가 길면 줄바꿈 처리
            content = latest_msg["content"]
            if len(content) > 200:
                print(f"   {content[:200]}...")
            else:
                # 여러 줄인 경우 들여쓰기
                for line in content.split("\n"):
                    print(f"   {line}")
            print()

    print("=" * 80)
    print("최종 결과")
    print("=" * 80)

    final_state = agent.run(query)
    print(final_state["final_response"])
    print("\n")


def test_comparison_query():
    """제품 비교 질문 테스트"""
    print("=" * 80)
    print("테스트 2: 제품 비교 질문")
    print("=" * 80)

    agent = V5Agent()
    query = "빌리프와 VT 브랜드 비교해줘"

    print(f"\n질문: {query}\n")
    print("-" * 80)

    final_state = agent.run(query)

    # 노드별 메시지 출력
    print("\n[노드별 실행 결과]\n")
    for msg in final_state["messages"]:
        status_icon = {
            "processing": "🔄",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }.get(msg["status"], "•")

        print(f"{status_icon} [{msg['node']}] {msg['status'].upper()}")

    print("\n" + "=" * 80)
    print("최종 결과")
    print("=" * 80)
    print(final_state["final_response"])
    print("\n")


def test_fallback_mode():
    """Fallback 모드 테스트 (데이터 부족)"""
    print("=" * 80)
    print("테스트 3: Fallback 모드 (데이터 부족 케이스)")
    print("=" * 80)

    agent = V5Agent()
    query = "존재하지않는브랜드12345 제품 분석해줘"

    print(f"\n질문: {query}\n")
    print("-" * 80)

    final_state = agent.run(query)

    print(f"\nFallback 모드: {final_state['is_fallback']}")
    if final_state['is_fallback']:
        print(f"Fallback 이유:\n{final_state['fallback_reason']}")

    print("\n" + "=" * 80)
    print("최종 결과")
    print("=" * 80)
    print(final_state["final_response"])
    print("\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "V5 LangGraph Agent 통합 테스트" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n")

    try:
        # 테스트 1: 간단한 질문
        test_simple_query()

        # 테스트 2: 제품 비교
        test_comparison_query()

        # 테스트 3: Fallback 모드
        test_fallback_mode()

        print("=" * 80)
        print("✅ 모든 테스트 완료!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
