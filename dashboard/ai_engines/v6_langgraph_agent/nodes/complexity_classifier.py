#//==============================================================================//#
"""
complexity_classifier.py
질문 복잡도 판단 (simple/medium/complex) - 조건부 라우팅용

last_updated: 2025.11.02
"""
#//==============================================================================//#

import logging
from typing import Dict, Any

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..errors import handle_exception
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.complexity_classifier")


class ComplexityClassifier:
    """질문 복잡도 분류"""

    def classify(self, state: AgentState) -> AgentState:
        """
        질문 복잡도 판단

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태 (complexity 추가)
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 로깅
            logger.info("ComplexityClassifier 시작")
            logger.debug(f"capabilities: {state.get('capabilities')}")

            # 1. 단계 시작
            tracker.start_step(
                node_name="ComplexityClassifier",
                description="질문 복잡도 분석 중...",
                substeps=["복잡도 점수 계산", "경로 결정"]
            )

            # 2. 복잡도 점수 계산
            score = self._calculate_complexity_score(
                state["user_query"],
                state["parsed_entities"],
                state["capabilities"]
            )

            logger.debug(f"복잡도 점수: {score}")

            # 3. 복잡도 레벨 결정
            if score <= 2:
                complexity = "simple"
                estimated_time = 2.5
                path = "Fast Path (Selector → SQL)"
            elif score <= 5:
                complexity = "medium"
                estimated_time = 5.0
                path = "Medium Path (Selector → Decomposer → SQL)"
            else:
                complexity = "complex"
                estimated_time = 12.0
                path = "Full Path (Selector → Decomposer → SQL → Refiner)"

            tracker.update_substep(f"복잡도: {complexity} (점수: {score})")
            tracker.update_substep(f"처리 경로: {path}")

            logger.info(f"복잡도 결정: {complexity} (점수: {score}, 경로: {path})")

            tracker.complete_step(summary=f"{complexity} 질문 (예상 {estimated_time}초)")

            # State 업데이트
            state["complexity"] = {
                "level": complexity,
                "score": score,
                "estimated_time": estimated_time,
                "path": path
            }
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "complexity_classifier")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"복잡도 분류 성공: {complexity}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except Exception as e:
            logger.error(f"ComplexityClassifier 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"복잡도 분석 오류: {str(e)}",
                suggestion="기본 경로로 진행합니다"
            )

            # 오류 시 medium으로 기본 설정
            state["complexity"] = {
                "level": "medium",
                "score": 3,
                "estimated_time": 5.0,
                "path": "Default Path"
            }
            state["error"] = handle_exception("ComplexityClassifier", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _calculate_complexity_score(
        self,
        query: str,
        entities: Dict[str, Any],
        capabilities: Dict[str, Any]
    ) -> int:
        """
        복잡도 점수 계산

        Args:
            query: 사용자 질문
            entities: 추출된 엔티티
            capabilities: 분석 전략

        Returns:
            복잡도 점수 (0~10+)
        """
        score = 0

        # 1. 엔티티 개수 (많을수록 복잡)
        brand_count = len(entities.get("brands", []))
        if brand_count > 3:
            score += 3
        elif brand_count > 1:
            score += 2
        elif brand_count == 1:
            score += 0

        product_count = len(entities.get("products", []))
        if product_count > 2:
            score += 2
        elif product_count > 0:
            score += 1

        attribute_count = len(entities.get("attributes", []))
        if attribute_count > 3:
            score += 3
        elif attribute_count > 1:
            score += 2
        elif attribute_count == 1:
            score += 0

        # 2. 집계 타입 (복잡도)
        agg_type = capabilities.get("aggregation_type", "simple")
        if agg_type == "time_series":
            score += 2  # 트렌드는 GROUP BY 필요
        elif agg_type == "comparison":
            score += 1  # 비교는 중간
        elif agg_type == "distribution":
            score += 2
        elif agg_type == "keyword_frequency":
            score += 1

        # 3. 데이터 소스 (JOIN은 복잡)
        data_scope = capabilities.get("data_scope", "preprocessed_reviews")
        if data_scope == "join":
            score += 2

        # 4. 복합 요청 감지 (질문에 "그리고", "하고" 등)
        compound_keywords = ["그리고", "하고", "또", "같이", "함께", "추가로"]
        for keyword in compound_keywords:
            if keyword in query:
                score += 2
                break

        # 5. 기간 조건 (필터링 증가)
        if entities.get("period", {}).get("type") != "all":
            score += 1

        # 6. 채널 조건
        if entities.get("channels"):
            score += 1

        # 7. 분석 깊이
        analysis_depth = capabilities.get("analysis_depth", "overview")
        if analysis_depth in ["pros_cons", "sentiment"]:
            score += 1

        return score
