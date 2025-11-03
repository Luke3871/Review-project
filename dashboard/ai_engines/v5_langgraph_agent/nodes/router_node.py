"""
Router Node - STEP 3: 툴 선택

파싱된 의도(intent)에 맞는 Tool들을 선택합니다.

선택 전략:
1. config.py의 INTENT_TO_TOOLS 매핑 사용
2. Fallback 모드인 경우에도 기본 툴 선택 (데이터 부족 경고와 함께 실행)
3. 선택 이유 명확히 기록
"""

from typing import Dict, List

from ..state import AgentState
from ..config import INTENT_TO_TOOLS


class RouterNode:
    """의도에 맞는 툴을 선택하는 노드"""

    def __init__(self):
        """초기화"""
        pass

    def __call__(self, state: AgentState) -> Dict:
        """
        Router Node 실행

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트할 상태 dict
        """
        parsed_query = state.get("parsed_query", {})
        intent = parsed_query.get("intent", "full_review")
        is_fallback = state.get("is_fallback", False)

        # 노드 시작 메시지
        messages = state.get("messages", [])
        messages.append({
            "node": "Router",
            "status": "processing",
            "content": f"의도 '{intent}'에 맞는 툴 선택 중..."
        })

        try:
            # 툴 선택
            selected_tools, selection_reason = self._select_tools(intent)

            # Fallback 모드 경고 추가
            if is_fallback:
                selection_reason += "\n\n⚠️ 주의: 데이터가 부족하지만 요청하신 분석을 진행합니다."

            # 성공 메시지
            messages.append({
                "node": "Router",
                "status": "success",
                "content": self._format_selection_result(selected_tools, selection_reason)
            })

            return {
                "selected_tools": selected_tools,
                "selection_reason": selection_reason,
                "messages": messages
            }

        except Exception as e:
            # 에러 발생 시 기본 툴 선택
            error_msg = f"툴 선택 실패: {str(e)}"
            messages.append({
                "node": "Router",
                "status": "error",
                "content": error_msg
            })

            # Fallback: SentimentTool만 사용
            fallback_tools = ["SentimentTool"]
            fallback_reason = f"{error_msg}\n기본 툴(SentimentTool)로 대체합니다."

            return {
                "selected_tools": fallback_tools,
                "selection_reason": fallback_reason,
                "messages": messages
            }

    def _select_tools(self, intent: str) -> tuple[List[str], str]:
        """
        의도에 맞는 툴 선택

        Args:
            intent: 의도 (예: "attribute_analysis")

        Returns:
            (툴 리스트, 선택 이유) 튜플

        Raises:
            ValueError: 유효하지 않은 의도
        """
        # INTENT_TO_TOOLS에서 매핑 확인
        if intent not in INTENT_TO_TOOLS:
            valid_intents = ", ".join(INTENT_TO_TOOLS.keys())
            raise ValueError(
                f"유효하지 않은 의도: {intent}\n"
                f"가능한 의도: {valid_intents}"
            )

        tool_config = INTENT_TO_TOOLS[intent]
        selected_tools = tool_config["tools"]
        selection_reason = tool_config["reason"]

        return selected_tools, selection_reason

    def _format_selection_result(
        self,
        selected_tools: List[str],
        selection_reason: str
    ) -> str:
        """
        툴 선택 결과 포맷팅

        Args:
            selected_tools: 선택된 툴 리스트
            selection_reason: 선택 이유

        Returns:
            포맷팅된 문자열
        """
        parts = [
            f"툴 선택 완료: {len(selected_tools)}개 툴",
            f"\n**선택된 툴:**"
        ]

        for i, tool_name in enumerate(selected_tools, 1):
            parts.append(f"  {i}. {tool_name}")

        parts.append(f"\n**선택 이유:**\n{selection_reason}")

        return "\n".join(parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Router Node 테스트 ===\n")

    router = RouterNode()

    # 테스트 케이스들
    test_cases = [
        {
            "name": "속성 분석",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": [],
                "channels": [],
                "intent": "attribute_analysis"
            },
            "is_fallback": False
        },
        {
            "name": "제품 비교",
            "parsed_query": {
                "brands": ["VT", "라로슈포제"],
                "products": ["시카크림", "시카플라스트"],
                "channels": [],
                "intent": "comparison"
            },
            "is_fallback": False
        },
        {
            "name": "전체 리뷰 분석",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": [],
                "channels": [],
                "intent": "full_review"
            },
            "is_fallback": False
        },
        {
            "name": "데이터 부족 (Fallback 모드)",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": ["존재하지않는제품"],
                "channels": [],
                "intent": "attribute_analysis"
            },
            "is_fallback": True
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {test_case['name']}")
        print("=" * 80)

        # 초기 상태
        state = {
            "parsed_query": test_case["parsed_query"],
            "is_fallback": test_case["is_fallback"],
            "messages": []
        }

        # Router Node 실행
        result = router(state)

        # 결과 출력
        for msg in result["messages"]:
            print(f"\n[{msg['node']}] {msg['status']}:")
            print(msg["content"])

        print(f"\n선택된 툴: {result['selected_tools']}")
