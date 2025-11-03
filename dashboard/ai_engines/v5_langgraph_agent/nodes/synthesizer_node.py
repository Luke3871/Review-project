"""
Synthesizer Node - STEP 5: 최종 응답 생성

툴 실행 결과들을 종합하여 사용자에게 제공할 최종 응답을 생성합니다.

응답 생성 전략:
1. Fallback 모드인 경우: 데이터 부족 안내 + 가능한 범위에서 결과 제공
2. 정상 모드인 경우: LLM으로 자연스러운 응답 생성
3. 툴 실행 결과를 데이터 기반으로 통찰 제공
4. 마크다운 형식으로 가독성 높은 응답
"""

import json
from typing import Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..state import AgentState
from ..config import SYNTHESIZER_PROMPT_TEMPLATE


class SynthesizerNode:
    """최종 응답을 생성하는 노드"""

    def __init__(self, llm_model: str = "gpt-4o", temperature: float = 0.3):
        """
        Args:
            llm_model: 사용할 LLM 모델 (응답 생성은 좀 더 강력한 모델 사용)
            temperature: LLM temperature (0.3 = 약간의 창의성)
        """
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature
        )

    def __call__(self, state: AgentState) -> Dict:
        """
        Synthesizer Node 실행

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트할 상태 dict
        """
        user_query = state.get("user_query", "")
        parsed_query = state.get("parsed_query", {})
        is_fallback = state.get("is_fallback", False)
        fallback_reason = state.get("fallback_reason", "")
        tool_results = state.get("tool_results", {})
        needs_clarification = state.get("needs_clarification", False)
        suggestions = state.get("suggestions", None)

        # 노드 시작 메시지
        messages = state.get("messages", [])
        messages.append({
            "node": "Synthesizer",
            "status": "processing",
            "content": "최종 응답 생성 중..."
        })

        try:
            # 재질문이 필요한 경우
            if needs_clarification:
                final_response = self._generate_clarification_response(
                    user_query,
                    parsed_query,
                    suggestions
                )
            elif is_fallback:
                # Fallback 모드: 간단한 응답
                final_response = self._generate_fallback_response(
                    user_query,
                    fallback_reason,
                    tool_results
                )
            else:
                # 정상 모드: LLM으로 응답 생성
                final_response = self._generate_normal_response(
                    user_query,
                    parsed_query,
                    tool_results
                )

            # 성공 메시지
            messages.append({
                "node": "Synthesizer",
                "status": "success",
                "content": "최종 응답 생성 완료"
            })

            return {
                "final_response": final_response,
                "messages": messages
            }

        except Exception as e:
            # 에러 발생 시 기본 응답
            error_msg = f"응답 생성 실패: {str(e)}"
            messages.append({
                "node": "Synthesizer",
                "status": "error",
                "content": error_msg
            })

            fallback_response = self._generate_error_response(user_query, str(e), tool_results)

            return {
                "final_response": fallback_response,
                "messages": messages
            }

    def _generate_normal_response(
        self,
        user_query: str,
        parsed_query: Dict,
        tool_results: Dict
    ) -> str:
        """
        정상 모드 응답 생성 (LLM 사용)

        Args:
            user_query: 사용자 질문
            parsed_query: 파싱된 쿼리
            tool_results: 툴 실행 결과

        Returns:
            최종 응답 문자열
        """
        # 필터 정보 추출
        brands = parsed_query.get("brands", [])
        products = parsed_query.get("products", [])
        channels = parsed_query.get("channels", [])

        # 툴 결과 포맷팅 (성공한 것만)
        formatted_results = self._format_tool_results(tool_results)

        # 프롬프트 생성
        prompt = SYNTHESIZER_PROMPT_TEMPLATE.format(
            user_query=user_query,
            brands=", ".join(brands) if brands else "전체",
            products=", ".join(products) if products else "전체",
            channels=", ".join(channels) if channels else "전체",
            tool_results=formatted_results
        )

        # LLM 호출
        response = self.llm.invoke([HumanMessage(content=prompt)])
        final_response = response.content.strip()

        return final_response

    def _generate_clarification_response(
        self,
        user_query: str,
        parsed_query: Dict,
        suggestions: list
    ) -> str:
        """
        재질문 응답 생성 (드롭다운 선택)

        Args:
            user_query: 사용자 질문
            parsed_query: 파싱된 쿼리
            suggestions: 제안할 제품 리스트 (사용 안 함)

        Returns:
            재질문 응답 문자열
        """
        products = parsed_query.get("products", [])
        brands = parsed_query.get("brands", [])
        channels = parsed_query.get("channels", [])

        parts = [
            f"# 데이터를 찾을 수 없습니다\n"
        ]

        # 입력한 필터 표시
        if brands or products or channels:
            parts.append("**입력하신 조건:**")
            if channels:
                parts.append(f"  - 채널: {', '.join(channels)}")
            if brands:
                parts.append(f"  - 브랜드: {', '.join(brands)}")
            if products:
                parts.append(f"  - 제품: {', '.join(products)}")
            parts.append("")

        parts.append("\n---\n")
        parts.append("\n## 아래 드롭다운에서 채널, 브랜드, 제품을 선택해주세요\n")
        parts.append("\n*정확한 데이터를 찾기 위해 드롭다운 메뉴에서 선택하실 수 있습니다.*")

        return "\n".join(parts)

    def _generate_fallback_response(
        self,
        user_query: str,
        fallback_reason: str,
        tool_results: Dict
    ) -> str:
        """
        Fallback 모드 응답 생성 (간단한 템플릿)

        Args:
            user_query: 사용자 질문
            fallback_reason: Fallback 이유
            tool_results: 툴 실행 결과

        Returns:
            Fallback 응답 문자열
        """
        parts = [
            f"# 분석 결과 (데이터 부족)\n",
            fallback_reason,
            "\n---\n",
            "\n## 분석 가능한 범위에서 결과를 제공합니다\n"
        ]

        # 성공한 툴 결과가 있으면 포함
        success_results = {
            tool_name: result
            for tool_name, result in tool_results.items()
            if result.get("status") == "success"
        }

        if success_results:
            for tool_name, result in success_results.items():
                parts.append(f"\n### {tool_name} 결과")

                # summary가 있으면 표시
                data = result.get("data", {})
                if "summary" in data:
                    parts.append(data["summary"])
                else:
                    # summary 없으면 주요 정보만 표시
                    parts.append(self._format_data_summary(data))
        else:
            parts.append("\n⚠️ 분석 가능한 데이터가 없습니다.")

        return "\n".join(parts)

    def _generate_error_response(
        self,
        user_query: str,
        error_message: str,
        tool_results: Dict
    ) -> str:
        """
        에러 응답 생성

        Args:
            user_query: 사용자 질문
            error_message: 에러 메시지
            tool_results: 툴 실행 결과

        Returns:
            에러 응답 문자열
        """
        parts = [
            f"# 응답 생성 중 오류 발생\n",
            f"**질문:** {user_query}\n",
            f"**오류:** {error_message}\n",
            "\n---\n"
        ]

        # 성공한 툴 결과가 있으면 raw 데이터라도 표시
        success_results = {
            tool_name: result
            for tool_name, result in tool_results.items()
            if result.get("status") == "success"
        }

        if success_results:
            parts.append("\n## 수집된 데이터 (Raw)\n")
            for tool_name, result in success_results.items():
                data = result.get("data", {})
                parts.append(f"\n### {tool_name}")
                parts.append(f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```")
        else:
            parts.append("\n분석된 데이터가 없습니다.")

        return "\n".join(parts)

    def _format_tool_results(self, tool_results: Dict) -> str:
        """
        툴 실행 결과를 LLM에게 전달할 형식으로 포맷팅

        Args:
            tool_results: 툴 실행 결과

        Returns:
            포맷팅된 문자열
        """
        parts = []

        for tool_name, result in tool_results.items():
            status = result.get("status")

            if status == "success":
                data = result.get("data", {})
                parts.append(f"\n### {tool_name} (성공)")
                parts.append(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                error = result.get("error", "알 수 없는 오류")
                parts.append(f"\n### {tool_name} (실패)")
                parts.append(f"오류: {error}")

        return "\n".join(parts) if parts else "실행된 툴 결과가 없습니다."

    def _format_data_summary(self, data: Dict) -> str:
        """
        데이터의 주요 정보를 간단히 포맷팅

        Args:
            data: 툴 데이터

        Returns:
            포맷팅된 문자열
        """
        parts = []

        # count 정보
        if "count" in data:
            parts.append(f"- 분석 리뷰 수: {data['count']}개")

        # 주요 키들만 간단히 표시
        important_keys = [
            "긍정_비율", "부정_비율",
            "주요_키워드", "대표_장점", "주요_단점",
            "포지셔닝_요약"
        ]

        for key in important_keys:
            if key in data:
                value = data[key]
                if isinstance(value, list):
                    if value:  # 비어있지 않으면
                        parts.append(f"- {key}: {', '.join(str(v) for v in value[:3])}")
                else:
                    parts.append(f"- {key}: {value}")

        return "\n".join(parts) if parts else "데이터 없음"


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Synthesizer Node 테스트 ===\n")

    synthesizer = SynthesizerNode()

    # 테스트 케이스: 정상 모드
    print("테스트 1: 정상 모드 (AttributeTool 결과)")
    print("=" * 80)

    state = {
        "user_query": "빌리프 브랜드 속성 분석해줘",
        "parsed_query": {
            "brands": ["빌리프"],
            "products": [],
            "channels": [],
            "intent": "attribute_analysis"
        },
        "is_fallback": False,
        "fallback_reason": "",
        "tool_results": {
            "AttributeTool": {
                "status": "success",
                "data": {
                    "count": 150,
                    "summary": "빌리프 제품은 보습력(85.2%)과 발림성(78.3%)에서 높은 만족도를 보입니다."
                }
            }
        },
        "messages": []
    }

    result = synthesizer(state)

    for msg in result["messages"]:
        print(f"\n[{msg['node']}] {msg['status']}:")
        print(msg["content"])

    print(f"\n최종 응답:\n{result['final_response']}")
