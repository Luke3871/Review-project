#//==============================================================================//#
"""
entity_parser.py
사용자 질문에서 엔티티 추출 (브랜드, 제품, 속성, 기간, 채널)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import re
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from openai import OpenAI

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import (
    LLM_CONFIG,
    CHANNEL_MAPPING,
    BRAND_LIST,
    BRAND_MAPPING,
    CATEGORY_ATTRIBUTES,
    ANALYSIS_KEYWORDS
)
from ..errors import handle_exception, LLMError, ValidationError
from ..state_validator import validate_state, validate_entity_structure

# 로거 설정
logger = logging.getLogger("v6_agent.entity_parser")


class EntityParser:
    """사용자 질문에서 엔티티 추출"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["entity_parser"]
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def parse(self, state: AgentState) -> AgentState:
        """
        엔티티 파싱 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 1. 단계 시작
            tracker.start_step(
                node_name="EntityParser",
                description="질문 분석 중...",
                substeps=[
                    "브랜드/제품 추출",
                    "속성 식별",
                    "기간 파싱",
                    "채널 확인",
                    "검증"
                ]
            )

            # 2. LLM으로 엔티티 추출 (대화 히스토리 포함)
            logger.debug(f"브랜드 리스트 개수: {len(BRAND_LIST)}")
            logger.debug(f"브랜드 매핑 개수: {len(BRAND_MAPPING)}")
            logger.info(f"사용자 질문: {state['user_query']}")

            # 대화 히스토리 확인
            conversation_history = state.get("conversation_history", [])
            if conversation_history:
                logger.info(f"대화 맥락 유지 모드: 이전 {len(conversation_history)}개 메시지 참조")

            raw_entities = self._extract_entities(
                state["user_query"],
                conversation_history=conversation_history
            )
            logger.debug(f"추출된 엔티티: {raw_entities}")

            tracker.update_substep("엔티티 추출 완료")

            # 3. 기간 정보 변환
            period_info = self._parse_period(raw_entities.get("period", {"type": "all"}))
            tracker.update_substep(f"기간: {period_info['display']}")

            # 4. 채널 매핑 (한글 → 영문)
            channels = self._map_channels(raw_entities.get("channels", []))

            # 5. 최종 엔티티 구성
            entities = {
                "brands": raw_entities.get("brands", []),
                "products": raw_entities.get("products", []),
                "attributes": raw_entities.get("attributes", []),
                "period": period_info,
                "channels": channels
            }

            # 6. 검증
            validation = self._validate(entities)
            logger.debug(f"검증 결과: {validation}")

            if validation["valid"]:
                # 추출 결과 업데이트
                brands_str = ", ".join(entities["brands"]) if entities["brands"] else "전체"
                tracker.update_substep(f"브랜드: {brands_str}")

                products_str = ", ".join(entities["products"]) if entities["products"] else "전체"
                tracker.update_substep(f"제품: {products_str}")

                attrs_str = ", ".join(entities["attributes"]) if entities["attributes"] else "전체"
                tracker.update_substep(f"속성: {attrs_str}")

                channels_str = ", ".join(entities["channels"]) if entities["channels"] else "전체"
                tracker.update_substep(f"채널: {channels_str}")

                tracker.complete_step(
                    summary=f"{len(entities['brands'])}개 브랜드, {len(entities['attributes'])}개 속성 추출"
                )

                # State 업데이트
                state["parsed_entities"] = entities
                state["messages"] = tracker.get_state_messages()

                # State 검증
                try:
                    state_errors = validate_state(state, "entity_parser")
                    entity_errors = validate_entity_structure(entities)

                    if state_errors or entity_errors:
                        all_errors = state_errors + entity_errors
                        logger.error(f"State 검증 실패: {all_errors}")
                        raise ValidationError("EntityParser", "; ".join(all_errors))

                    logger.info(f"엔티티 추출 성공: {len(entities['brands'])}개 브랜드, {len(entities['attributes'])}개 속성")
                except ValidationError:
                    raise
                except Exception as validation_error:
                    logger.error(f"검증 중 예외 발생: {validation_error}")
                    # 검증 실패는 치명적이지 않으므로 경고만

            else:
                # 검증 실패
                logger.warning(f"엔티티 검증 실패: {validation['error']}")

                tracker.error_step(
                    error_msg=validation["error"],
                    suggestion="질문을 더 구체적으로 입력해주세요."
                )

                state["error"] = {
                    "node": "EntityParser",
                    "error_type": "validation_failed",
                    "message": validation["error"],
                    "suggestion": "질문을 더 구체적으로 입력해주세요."
                }
                state["messages"] = tracker.get_state_messages()

        except Exception as e:
            # 에러 로깅 (표준화된 방식)
            logger.error(f"엔티티 추출 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"엔티티 추출 오류: {str(e)}",
                suggestion="질문을 다시 입력해주세요."
            )

            # 표준 에러 처리
            state["error"] = handle_exception("EntityParser", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _extract_entities(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        LLM을 사용하여 엔티티 추출 (대화 맥락 반영)

        Args:
            query: 사용자 질문
            conversation_history: 이전 대화 히스토리 (옵션)

        Returns:
            추출된 엔티티
        """
        # 브랜드 리스트 문자열 생성 (처음 100개 + 랜덤 50개)
        brand_sample = BRAND_LIST[:100] if len(BRAND_LIST) > 100 else BRAND_LIST
        brand_list_str = ", ".join(brand_sample)

        # 주요 브랜드 매핑 (자주 쓰이는 영문 브랜드 50개)
        major_mappings = {k: v for k, v in list(BRAND_MAPPING.items())[:50]}
        brand_mapping_str = "\n".join([f"- {k} → {v}" for k, v in major_mappings.items()])

        # 주요 속성 리스트
        all_attributes = set()
        for attrs in CATEGORY_ATTRIBUTES.values():
            all_attributes.update(attrs)
        attributes_str = ", ".join(sorted(list(all_attributes)))

        # 대화 히스토리 컨텍스트 생성
        history_context = ""
        if conversation_history:
            # 최근 3개 대화만 사용 (너무 길면 토큰 낭비)
            recent_history = conversation_history[-6:]  # user + assistant 쌍 3개
            history_lines = []
            for msg in recent_history:
                role = "사용자" if msg["role"] == "user" else "AI"
                content = msg["content"][:500]  # 500자로 제한 (200 → 500)
                history_lines.append(f"{role}: {content}")
            history_context = "\n**이전 대화 맥락:**\n" + "\n".join(history_lines) + "\n\n"

        prompt = f"""당신은 화장품 리뷰 분석 시스템의 질문 파서입니다.
사용자 질문을 분석해서 다음 정보를 JSON으로 추출하세요.

{history_context}**IMPORTANT: 대화 맥락 처리 규칙**
- 현재 질문에서 브랜드/제품이 생략되었다면, 이전 대화에서 언급된 것을 참조하세요
- "그럼", "그거", "그 제품", "거기서" 같은 지칭어는 이전 맥락의 엔티티를 사용하세요
- "기획은?", "가격은?" 같은 질문은 이전 브랜드/제품을 유지하고 속성만 변경하세요
- 예시:
  * 이전: "빌리프 보습력 어때?" → brands: ["빌리프"], attributes: ["보습력"]
  * 현재: "그럼 기획에 대해서는?" → brands: ["빌리프"], attributes: ["기획"]
  * 현재: "VT는?" → brands: ["VT"], attributes: ["보습력"] (속성 유지)

**표준 브랜드 리스트 (일부 {len(brand_sample)}개):**
{brand_list_str}
... (총 {len(BRAND_LIST)}개 브랜드 지원)

**브랜드 영문→한글 매핑 (주요):**
{brand_mapping_str}

**브랜드 추출 규칙:**
1. 표준 브랜드 리스트에 있는 이름 우선 사용
2. 영문 브랜드는 매핑표에서 한글 표준명 찾기
3. 유사한 이름은 표준명으로 정규화
   예: "빌리포" → "빌리프"
   예: "VT코스메틱" → "VT"
   예: "바이오더마" → "바이오더마" (표준명)
   예: "BIODERMA" → "바이오더마" (매핑)

**표준 속성 리스트:**
{attributes_str}

**속성 추출 규칙:**
1. 위 표준 속성 리스트에서 선택
2. 분석 키워드: {", ".join(ANALYSIS_KEYWORDS[:10])}
3. 유사한 표현은 표준 속성명으로 변환
   예: "촉촉함", "수분감" → "보습력"
   예: "발림", "발리는느낌" → "발림성"

**추출 항목:**
- brands: 브랜드명 리스트 (표준 브랜드명 사용!)
- products: 제품명 리스트
- attributes: 속성 리스트 (표준 속성명 사용!)
- period: 기간 정보
- channels: 채널명 리스트 (예: ["올리브영", "쿠팡"])

**기간 타입:**
- recent_months: 최근 N개월 (예: {{"type": "recent_months", "value": 3}})
- recent_days: 최근 N일 (예: {{"type": "recent_days", "value": 7}})
- date_range: 특정 날짜 범위 (예: {{"type": "date_range", "start": "2025-08-01", "end": "2025-10-29"}})
- all: 전체 기간 (예: {{"type": "all"}})

**예시:**

질문: "빌리프 보습력 어때?"
→ {{"brands": ["빌리프"], "products": [], "attributes": ["보습력"], "period": {{"type": "all"}}, "channels": []}}

질문: "VT랑 라로슈포제 최근 3개월 비교"
→ {{"brands": ["VT", "라로슈포제"], "products": [], "attributes": [], "period": {{"type": "recent_months", "value": 3}}, "channels": []}}

질문: "올리브영에서 CNP 장점 알려줘"
→ {{"brands": ["CNP"], "products": [], "attributes": ["장점"], "channels": ["올리브영"], "period": {{"type": "all"}}}}

질문: "바이오더티디 스팟카밍젤 평점분포"
→ {{"brands": ["바이오더티디"], "products": ["스팟카밍젤"], "attributes": ["평점분포"], "period": {{"type": "all"}}, "channels": []}}

**사용자 질문:**
{query}

**JSON만 반환하세요 (다른 설명 없이):**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        result_text = response.choices[0].message.content.strip()

        # JSON 파싱 (정규표현식 사용 - 더 견고하게)
        try:
            # 1. 마크다운 코드 블록에서 JSON 추출
            pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(pattern, result_text, re.DOTALL)

            if match:
                result_text = match.group(1)
            else:
                # 2. 중괄호 {} 사이의 내용만 추출 (코드 블록 없을 때)
                pattern = r'\{.*\}'
                match = re.search(pattern, result_text, re.DOTALL)
                if match:
                    result_text = match.group(0)

            # 3. JSON 파싱
            entities = json.loads(result_text)
            return entities

        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON 파싱 실패\n"
                f"LLM 응답 (처음 300자): {result_text[:300]}\n"
                f"에러: {str(e)}"
            )

    def _parse_period(self, period: Dict[str, Any]) -> Dict[str, Any]:
        """
        기간 정보를 실제 날짜로 변환

        Args:
            period: 기간 정보 {"type": "recent_months", "value": 3}

        Returns:
            변환된 기간 정보
        """
        today = datetime.now()
        period_type = period.get("type", "all")

        if period_type == "recent_months":
            months = period.get("value", 1)
            start_date = today - timedelta(days=months * 30)
            return {
                "type": "recent_months",
                "value": months,
                "start": start_date.strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d"),
                "display": f"최근 {months}개월"
            }

        elif period_type == "recent_days":
            days = period.get("value", 7)
            start_date = today - timedelta(days=days)
            return {
                "type": "recent_days",
                "value": days,
                "start": start_date.strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d"),
                "display": f"최근 {days}일"
            }

        elif period_type == "date_range":
            return {
                "type": "date_range",
                "start": period.get("start"),
                "end": period.get("end"),
                "display": f"{period.get('start')} ~ {period.get('end')}"
            }

        else:  # "all"
            return {
                "type": "all",
                "start": None,
                "end": None,
                "display": "전체 기간"
            }

    def _map_channels(self, channels: List[str]) -> List[str]:
        """
        채널명 한글 → 영문 매핑

        Args:
            channels: 한글 채널명 리스트

        Returns:
            영문 채널명 리스트
        """
        return [CHANNEL_MAPPING.get(ch, ch) for ch in channels]

    def _validate(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        추출된 엔티티 검증

        Args:
            entities: 추출된 엔티티

        Returns:
            검증 결과 {"valid": bool, "error": str}
        """
        # 의미있는 질문인지 확인
        has_meaningful_query = any([
            entities.get("brands"),
            entities.get("products"),
            entities.get("channels"),
            len(entities.get("attributes", [])) > 0
        ])

        if not has_meaningful_query:
            return {
                "valid": False,
                "error": "분석할 대상을 찾을 수 없습니다. 브랜드, 제품, 속성을 명시해주세요."
            }

        return {"valid": True}
