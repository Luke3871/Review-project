"""
Parser Node - STEP 1: 사용자 질문 파싱

사용자 질문에서 다음 정보를 추출:
- brands: 브랜드명 리스트
- products: 제품명 리스트
- channels: 채널명 리스트
- intent: 질문 의도 (attribute_analysis, sentiment_analysis 등)

LLM을 사용하여 자연어 질문을 구조화된 데이터로 변환합니다.
"""

import json
import re
from typing import Dict, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..state import AgentState
from ..config import PARSER_PROMPT_TEMPLATE, INTENT_TO_TOOLS, CHANNEL_MAPPING


class ParserNode:
    """사용자 질문을 파싱하는 노드"""

    def __init__(self, llm_model: str = "gpt-4o-mini", temperature: float = 0.0):
        """
        Args:
            llm_model: 사용할 LLM 모델
            temperature: LLM temperature (0.0 = 결정적, 1.0 = 창의적)
        """
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature
        )

    def __call__(self, state: AgentState) -> Dict:
        """
        Parser Node 실행

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트할 상태 dict
        """
        user_query = state.get("user_query", "")

        # 노드 시작 메시지
        messages = state.get("messages", [])
        messages.append({
            "node": "Parser",
            "status": "processing",
            "content": f"질문 분석 중: '{user_query}'"
        })

        try:
            # LLM으로 질문 파싱
            parsed_query = self._parse_query_with_llm(user_query)

            # 파싱 결과 검증
            self._validate_parsed_query(parsed_query)

            # 채널명 정규화 (한글 → 영문)
            parsed_query['channels'] = self._normalize_channels(parsed_query.get('channels', []))

            # 성공 메시지
            messages.append({
                "node": "Parser",
                "status": "success",
                "content": self._format_parse_result(parsed_query)
            })

            return {
                "parsed_query": parsed_query,
                "messages": messages
            }

        except Exception as e:
            # 에러 메시지
            messages.append({
                "node": "Parser",
                "status": "error",
                "content": f"질문 파싱 실패: {str(e)}"
            })

            # 기본값으로 fallback
            fallback_query = {
                "brands": [],
                "products": [],
                "channels": [],
                "intent": "full_review",
                "error": str(e)
            }

            return {
                "parsed_query": fallback_query,
                "messages": messages
            }

    def _parse_query_with_llm(self, user_query: str) -> Dict:
        """
        LLM으로 사용자 질문 파싱

        Args:
            user_query: 사용자 질문

        Returns:
            파싱된 결과 dict
        """
        # 프롬프트 생성
        prompt = PARSER_PROMPT_TEMPLATE.format(query=user_query)

        # LLM 호출
        response = self.llm.invoke([HumanMessage(content=prompt)])
        response_text = response.content.strip()

        # JSON 추출 (마크다운 코드 블록 제거)
        json_text = self._extract_json_from_response(response_text)

        # JSON 파싱
        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM 응답이 유효한 JSON이 아닙니다: {response_text}") from e

        return parsed

    def _extract_json_from_response(self, response_text: str) -> str:
        """
        LLM 응답에서 JSON 추출

        마크다운 코드 블록(```json ... ```)이 있으면 제거하고 JSON만 추출

        Args:
            response_text: LLM 응답 텍스트

        Returns:
            JSON 문자열
        """
        # 마크다운 코드 블록 패턴
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, response_text, re.DOTALL)

        if match:
            return match.group(1)

        # 코드 블록 없으면 그대로 반환
        return response_text.strip()

    def _validate_parsed_query(self, parsed_query: Dict) -> None:
        """
        파싱된 결과 검증

        Args:
            parsed_query: 파싱된 결과

        Raises:
            ValueError: 필수 필드 누락 또는 유효하지 않은 값
        """
        # 필수 필드 확인
        required_fields = ["brands", "products", "channels", "intent"]
        for field in required_fields:
            if field not in parsed_query:
                raise ValueError(f"필수 필드 누락: {field}")

        # 리스트 타입 확인
        for field in ["brands", "products", "channels"]:
            if not isinstance(parsed_query[field], list):
                raise ValueError(f"{field}는 리스트여야 합니다. 현재: {type(parsed_query[field])}")

        # intent 유효성 확인
        intent = parsed_query["intent"]
        valid_intents = list(INTENT_TO_TOOLS.keys())

        if intent not in valid_intents:
            raise ValueError(
                f"유효하지 않은 intent: {intent}\n"
                f"가능한 값: {', '.join(valid_intents)}"
            )

    def _format_parse_result(self, parsed_query: Dict) -> str:
        """
        파싱 결과를 보기 좋게 포맷팅

        Args:
            parsed_query: 파싱된 결과

        Returns:
            포맷팅된 문자열
        """
        parts = ["질문 파싱 완료:"]

        # 브랜드
        if parsed_query["brands"]:
            parts.append(f"  - 브랜드: {', '.join(parsed_query['brands'])}")
        else:
            parts.append("  - 브랜드: 전체")

        # 제품
        if parsed_query["products"]:
            parts.append(f"  - 제품: {', '.join(parsed_query['products'])}")
        else:
            parts.append("  - 제품: 전체")

        # 채널
        if parsed_query["channels"]:
            parts.append(f"  - 채널: {', '.join(parsed_query['channels'])}")
        else:
            parts.append("  - 채널: 전체")

        # 의도
        intent = parsed_query["intent"]
        intent_description = INTENT_TO_TOOLS.get(intent, {}).get("reason", intent)
        parts.append(f"  - 분석 유형: {intent_description}")

        return "\n".join(parts)

    def _normalize_channels(self, channels: List[str]) -> List[str]:
        """
        채널명을 DB 형식으로 정규화 (한글 → 영문)

        Args:
            channels: LLM이 추출한 채널명 리스트 (예: ["올리브영", "쿠팡"])

        Returns:
            정규화된 채널명 리스트 (예: ["OliveYoung", "Coupang"])
        """
        normalized = []
        for channel in channels:
            # CHANNEL_MAPPING에서 매핑 찾기
            mapped_channel = CHANNEL_MAPPING.get(channel, channel)
            normalized.append(mapped_channel)

        return normalized


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Parser Node 테스트 ===\n")

    parser = ParserNode()

    # 테스트 질문들
    test_queries = [
        "빌리프 모이스춰라이징밤 속성 분석해줘",
        "VT 시카크림이랑 라로슈포제 시카플라스트 비교해줘",
        "올리브영에서 기획전 반응 어때?",
        "보습에 대한 긍정/부정 반응 알려줘",
        "빌리프 제품 장점이 뭐야?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 질문: {query}")

        # 초기 상태
        state = {
            "user_query": query,
            "messages": []
        }

        # Parser Node 실행
        result = parser(state)

        # 결과 출력
        for msg in result["messages"]:
            print(f"\n[{msg['node']}] {msg['status']}:")
            print(msg["content"])

        print(f"\n파싱된 쿼리: {json.dumps(result['parsed_query'], ensure_ascii=False, indent=2)}")
        print("-" * 80)
