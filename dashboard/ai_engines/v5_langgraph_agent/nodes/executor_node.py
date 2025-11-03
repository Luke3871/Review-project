"""
Executor Node - STEP 4: 툴 실행 및 결과 수집

선택된 툴들을 실행하고 결과를 수집합니다.

실행 전략:
1. 각 툴을 순차적으로 실행 (현재는 POC라서 순차, V6에서 병렬 고려)
2. 툴 실행 시 에러 핸들링 (한 툴이 실패해도 다른 툴은 계속 실행)
3. 각 툴의 실행 결과를 tool_results에 저장
4. 실행 성공/실패 상태를 messages에 기록
"""

from typing import Dict, List
import traceback

from ..state import AgentState
from ..tools.registry import get_tool


class ExecutorNode:
    """선택된 툴들을 실행하는 노드"""

    def __init__(self):
        """초기화"""
        pass

    def __call__(self, state: AgentState) -> Dict:
        """
        Executor Node 실행

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트할 상태 dict
        """
        selected_tools = state.get("selected_tools", [])
        parsed_query = state.get("parsed_query", {})

        brands = parsed_query.get("brands", [])
        products = parsed_query.get("products", [])
        channels = parsed_query.get("channels", [])

        # 노드 시작 메시지
        messages = state.get("messages", [])
        messages.append({
            "node": "Executor",
            "status": "processing",
            "content": f"{len(selected_tools)}개 툴 실행 중..."
        })

        # 툴 실행 결과 저장
        tool_results = {}
        success_count = 0
        error_count = 0

        # 각 툴 실행
        for tool_name in selected_tools:
            try:
                # 툴 실행
                result = self._execute_tool(
                    tool_name,
                    brands,
                    products,
                    channels
                )

                # 성공
                tool_results[tool_name] = {
                    "status": "success",
                    "data": result
                }
                success_count += 1

                # 툴별 성공 메시지
                messages.append({
                    "node": "Executor",
                    "status": "info",
                    "content": f"✓ {tool_name} 실행 완료"
                })

            except Exception as e:
                # 실패
                tool_results[tool_name] = {
                    "status": "error",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                error_count += 1

                # 툴별 에러 메시지
                messages.append({
                    "node": "Executor",
                    "status": "warning",
                    "content": f"✗ {tool_name} 실행 실패: {str(e)}"
                })

        # 전체 실행 결과 메시지
        if error_count == 0:
            # 모두 성공
            messages.append({
                "node": "Executor",
                "status": "success",
                "content": f"모든 툴 실행 완료: {success_count}/{len(selected_tools)} 성공"
            })
        elif success_count == 0:
            # 모두 실패
            messages.append({
                "node": "Executor",
                "status": "error",
                "content": f"모든 툴 실행 실패: {error_count}/{len(selected_tools)} 실패"
            })
        else:
            # 일부 성공
            messages.append({
                "node": "Executor",
                "status": "warning",
                "content": f"일부 툴 실행 완료: {success_count}개 성공, {error_count}개 실패"
            })

        return {
            "tool_results": tool_results,
            "messages": messages
        }

    def _execute_tool(
        self,
        tool_name: str,
        brands: List[str],
        products: List[str],
        channels: List[str]
    ) -> Dict:
        """
        단일 툴 실행

        Args:
            tool_name: 툴 이름
            brands: 브랜드 리스트
            products: 제품 리스트
            channels: 채널 리스트

        Returns:
            툴 실행 결과

        Raises:
            Exception: 툴 실행 중 에러 발생
        """
        # 툴 인스턴스 가져오기
        tool = get_tool(tool_name)

        # 툴 실행 (빈 리스트는 None으로 변환)
        result = tool.run(
            brands=brands if brands else None,
            products=products if products else None,
            channels=channels if channels else None
        )

        return result


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Executor Node 테스트 ===\n")

    executor = ExecutorNode()

    # 테스트 케이스
    test_cases = [
        {
            "name": "단일 툴 실행 (AttributeTool)",
            "selected_tools": ["AttributeTool"],
            "parsed_query": {
                "brands": ["빌리프"],
                "products": [],
                "channels": [],
                "intent": "attribute_analysis"
            }
        },
        {
            "name": "다중 툴 실행 (전체 리뷰 분석)",
            "selected_tools": ["AttributeTool", "SentimentTool", "KeywordTool"],
            "parsed_query": {
                "brands": ["빌리프"],
                "products": [],
                "channels": [],
                "intent": "full_review"
            }
        },
        {
            "name": "제품 비교",
            "selected_tools": ["ProductComparisonTool"],
            "parsed_query": {
                "brands": ["VT", "라로슈포제"],
                "products": ["시카크림", "시카플라스트"],
                "channels": [],
                "intent": "comparison"
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {test_case['name']}")
        print("=" * 80)

        # 초기 상태
        state = {
            "selected_tools": test_case["selected_tools"],
            "parsed_query": test_case["parsed_query"],
            "messages": []
        }

        # Executor Node 실행
        result = executor(state)

        # 결과 출력
        for msg in result["messages"]:
            print(f"\n[{msg['node']}] {msg['status']}:")
            print(msg["content"])

        print(f"\n실행된 툴: {len(result['tool_results'])}개")
        for tool_name, tool_result in result["tool_results"].items():
            print(f"  - {tool_name}: {tool_result['status']}")
            if tool_result['status'] == 'success':
                # 간단히 데이터 키만 출력
                print(f"    데이터 키: {list(tool_result['data'].keys())}")
