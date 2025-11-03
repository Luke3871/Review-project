#//==============================================================================//#
"""
question_decomposer.py
복잡한 질문을 sub-questions로 분해

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import logging
from typing import Dict, Any, List
from openai import OpenAI

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import LLM_CONFIG
from ..errors import handle_exception, LLMError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.question_decomposer")


class QuestionDecomposer:
    """질문 분해"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["capability_detector"]  # 0.0
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def decompose(self, state: AgentState) -> AgentState:
        """
        질문 분해 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 1. 복잡도 체크
            complexity = state.get("complexity", {}).get("level", "medium")
            logger.info(f"QuestionDecomposer 시작 (복잡도: {complexity})")

            # Simple 질문은 분해 안 함
            if complexity == "simple":
                logger.info("단순 질문으로 분해 스킵")
                tracker.start_step(
                    node_name="QuestionDecomposer",
                    description="질문 분해 (단순 질문 - 스킵)",
                )
                tracker.complete_step(summary="단순 질문으로 분해 불필요")

                state["sub_questions"] = [{
                    "sub_question": state["user_query"],
                    "purpose": "단일 질문",
                    "dependency": None
                }]
                state["messages"] = tracker.get_state_messages()
                return state

            # 2. 단계 시작
            tracker.start_step(
                node_name="QuestionDecomposer",
                description="질문 분해 중...",
                substeps=[
                    "복잡한 질문 분석",
                    "하위 질문 생성",
                    "의존성 파악"
                ]
            )

            # 3. LLM으로 질문 분해
            logger.debug("질문 분해 시작")
            sub_questions = self._decompose_question(
                state["user_query"],
                state["parsed_entities"],
                complexity
            )

            logger.info(f"{len(sub_questions)}개 하위 질문 생성")
            tracker.update_substep(f"{len(sub_questions)}개 하위 질문 생성")

            # 4. 각 sub-question 표시
            for i, sq in enumerate(sub_questions, 1):
                dep_str = f" (depends on Q{sq['dependency'][0]})" if sq.get('dependency') else ""
                logger.debug(f"Q{i}: {sq['sub_question']}{dep_str}")
                tracker.update_substep(f"Q{i}: {sq['sub_question']}{dep_str}")

            tracker.complete_step(summary=f"{len(sub_questions)}개 하위 질문 생성 완료")

            # State 업데이트
            state["sub_questions"] = sub_questions
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "question_decomposer")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"질문 분해 성공: {len(sub_questions)}개")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except json.JSONDecodeError as e:
            # JSON 파싱 실패
            logger.error(f"질문 분해 실패 - JSON 파싱 오류: {e}", exc_info=True)

            tracker.error_step(
                error_msg="질문 분해 형식 오류 (LLM 응답 파싱 실패)",
                suggestion="원본 질문으로 진행합니다"
            )

            # 오류 시 원본 질문 그대로 사용
            state["sub_questions"] = [{
                "sub_question": state["user_query"],
                "purpose": "원본 질문",
                "dependency": None
            }]
            state["error"] = LLMError("QuestionDecomposer", f"JSON 파싱 실패: {str(e)}", original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except Exception as e:
            logger.error(f"QuestionDecomposer 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"질문 분해 오류: {str(e)}",
                suggestion="원본 질문으로 진행합니다"
            )

            # 오류 시 원본 질문 그대로 사용
            state["sub_questions"] = [{
                "sub_question": state["user_query"],
                "purpose": "원본 질문",
                "dependency": None
            }]
            state["error"] = handle_exception("QuestionDecomposer", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _decompose_question(
        self,
        query: str,
        entities: Dict[str, Any],
        complexity: str
    ) -> List[Dict[str, Any]]:
        """
        LLM을 사용하여 질문 분해

        Args:
            query: 사용자 질문
            entities: 추출된 엔티티
            complexity: 복잡도 레벨

        Returns:
            하위 질문 리스트
        """
        prompt = f"""당신은 복잡한 질문을 분해하는 전문가입니다.
사용자 질문을 분석하여 필요한 하위 질문(sub-questions)으로 분해하세요.

**규칙:**
1. 비교 질문: 각 대상별로 분리 (예: "A랑 B 비교" → "A 분석" + "B 분석")
2. 복합 요청: "그리고", "하고" 기준으로 분리
3. 시계열 + 비교: 각각 분리
4. 의존성: 이전 질문 결과가 필요한 경우 dependency에 질문 번호 명시 (1-based)

**출력 형식:**
[
    {{
        "sub_question": "구체적인 하위 질문",
        "purpose": "이 질문의 목적 (한 줄)",
        "dependency": null 또는 [이전 질문 번호]
    }}
]

**예시:**

예시 1:
질문: "빌리프 보습력 어때?"
→ [
    {{"sub_question": "빌리프 보습력 어때?", "purpose": "단일 속성 분석", "dependency": null}}
]

예시 2:
질문: "빌리프랑 VT 비교"
→ [
    {{"sub_question": "빌리프 전반적 평가", "purpose": "브랜드 A 분석", "dependency": null}},
    {{"sub_question": "VT 전반적 평가", "purpose": "브랜드 B 분석", "dependency": null}}
]

예시 3:
질문: "빌리프 보습력 분석하고 트렌드도 보여줘"
→ [
    {{"sub_question": "빌리프 보습력 평가", "purpose": "속성 분석", "dependency": null}},
    {{"sub_question": "빌리프 보습력 최근 트렌드", "purpose": "시계열 분석", "dependency": [1]}}
]

예시 4:
질문: "빌리프, VT, CNP 보습력 비교하고 각각 트렌드"
→ [
    {{"sub_question": "빌리프 보습력 평가", "purpose": "브랜드 A 속성 분석", "dependency": null}},
    {{"sub_question": "VT 보습력 평가", "purpose": "브랜드 B 속성 분석", "dependency": null}},
    {{"sub_question": "CNP 보습력 평가", "purpose": "브랜드 C 속성 분석", "dependency": null}},
    {{"sub_question": "빌리프 보습력 트렌드", "purpose": "브랜드 A 시계열", "dependency": [1]}},
    {{"sub_question": "VT 보습력 트렌드", "purpose": "브랜드 B 시계열", "dependency": [2]}},
    {{"sub_question": "CNP 보습력 트렌드", "purpose": "브랜드 C 시계열", "dependency": [3]}}
]

**사용자 질문:**
{query}

**추출된 엔티티:**
{json.dumps(entities, ensure_ascii=False, indent=2)}

**복잡도:** {complexity}

**JSON 배열만 반환하세요 (다른 설명 없이):**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        result_text = response.choices[0].message.content.strip()

        # JSON 파싱
        try:
            # 코드 블록 제거
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            sub_questions = json.loads(result_text)
            return sub_questions

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {result_text[:100]}... (error: {str(e)})")
