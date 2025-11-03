#//==============================================================================//#
"""
entity_parser.py
사용자 질문에서 엔티티 추출 (브랜드, 제품, 속성, 기간, 채널)

last_updated: 2025.10.29
"""
#//==============================================================================//#

import json
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
from openai import OpenAI
import sys
from pathlib import Path

# V7 root 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import AgentState
from config import (
    LLM_CONFIG,
    CHANNEL_MAPPING,
    BRAND_LIST,
    BRAND_MAPPING,
    CATEGORY_ATTRIBUTES
)


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
        # V7에서는 사용되지 않음 - Tool에서 _extract_entities() 직접 호출
        try:
            raw_entities = self._extract_entities(state["user_query"])
            state["parsed_entities"] = raw_entities
        except Exception as e:
            state["error"] = {
                "node": "EntityParser",
                "error_type": "extraction_failed",
                "message": str(e)
            }
        return state

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """
        LLM을 사용하여 엔티티 추출

        Args:
            query: 사용자 질문

        Returns:
            추출된 엔티티
        """
        # 브랜드 리스트 전체 사용 (V7: Tool 단위라 전체 사용 가능)
        brand_list_str = ", ".join(BRAND_LIST)

        # 브랜드 매핑 전체 사용
        brand_mapping_str = "\n".join([f"- {k} → {v}" for k, v in BRAND_MAPPING.items()])

        # 주요 속성 리스트
        all_attributes = set()
        for attrs in CATEGORY_ATTRIBUTES.values():
            all_attributes.update(attrs)
        attributes_str = ", ".join(sorted(list(all_attributes)))

        prompt = f"""당신은 화장품 리뷰 분석 시스템의 질문 파서입니다.
사용자 질문을 분석해서 다음 정보를 JSON으로 추출하세요:

**표준 브랜드 리스트 (전체 {len(BRAND_LIST)}개):**
{brand_list_str}

**브랜드 영문→한글 매핑 (전체 {len(BRAND_MAPPING)}개):**
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
        # 의미있는 질문인지 확인 (너무 빈약한 질문만 걸러냄)
        has_meaningful_query = any([
            entities.get("brands"),
            entities.get("products"),
            entities.get("channels"),
            len(entities.get("attributes", [])) > 0  # 속성만 있어도 OK
        ])

        # 속성에 분석 관련 키워드 있으면 통과
        has_analysis_intent = False
        for attr in entities.get("attributes", []):
            if any(keyword in attr for keyword in ANALYSIS_KEYWORDS):
                has_analysis_intent = True
                break

        if not has_meaningful_query and not has_analysis_intent:
            return {
                "valid": False,
                "error": "분석할 대상을 찾을 수 없습니다. 브랜드, 제품, 속성 중 하나를 명시해주세요."
            }

        return {"valid": True}
