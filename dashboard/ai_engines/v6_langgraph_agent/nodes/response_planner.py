#//==============================================================================//#
"""
response_planner.py
시각화 전략 결정 (auto/suggest/none)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import logging
from typing import Dict, Any, List

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import VISUALIZATION_CONFIG
from ..errors import handle_exception
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.response_planner")


class ResponsePlanner:
    """응답 형식 계획"""

    def __init__(self):
        self.viz_config = VISUALIZATION_CONFIG

    def plan(self, state: AgentState) -> AgentState:
        """
        응답 계획 수립

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 로깅
            logger.info("ResponsePlanner 시작")

            # 1. 단계 시작
            tracker.start_step(
                node_name="ResponsePlanner",
                description="응답 형식 계획 중...",
                substeps=[
                    "데이터 특성 분석",
                    "시각화 필요성 판단",
                    "출력 구성 결정"
                ]
            )

            # 2. 데이터 특성 가져오기
            query_results = state.get("query_results", {})
            data_chars = query_results.get("data_characteristics", {})
            logger.debug(f"data_characteristics: {data_chars}")
            capabilities = state.get("capabilities", {})

            # 3. 시각화 confidence 계산
            viz_confidence = self._calculate_viz_confidence(data_chars, capabilities)
            tracker.update_substep(f"시각화 신뢰도: {viz_confidence:.2f}")

            # 4. 전략 결정
            auto_threshold = self.viz_config["auto_threshold"]
            suggest_threshold = self.viz_config["suggest_threshold"]

            if viz_confidence >= auto_threshold:
                strategy = "auto"
                message = "자동 시각화 생성"
            elif viz_confidence >= suggest_threshold:
                strategy = "suggest"
                message = "시각화 옵션 제안"
            else:
                strategy = "none"
                message = "텍스트 답변만"

            tracker.update_substep(f"전략: {message}")

            # 5. 출력 구성 결정
            components = self._plan_components(
                strategy,
                viz_confidence,
                data_chars,
                capabilities
            )

            logger.debug(f"strategy: {strategy}")
            logger.debug(f"viz_confidence: {viz_confidence}")
            logger.debug(f"components: {components}")

            tracker.update_substep(f"{len(components)}개 출력 구성요소 결정")

            tracker.complete_step(summary=f"{strategy} 전략 ({viz_confidence:.2f})")

            # State 업데이트
            state["response_plan"] = {
                "visualization_strategy": strategy,
                "confidence": viz_confidence,
                "components": components,
                "thresholds": {
                    "auto": auto_threshold,
                    "suggest": suggest_threshold
                }
            }
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "response_planner")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"응답 계획 성공: {strategy} 전략, {len(components)}개 구성요소")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except Exception as e:
            logger.error(f"ResponsePlanner 실패: {type(e).__name__} - {str(e)}", exc_info=True)
            tracker.error_step(
                error_msg=f"응답 계획 오류: {str(e)}",
                suggestion="기본 텍스트 답변으로 진행합니다."
            )

            # 오류 시 기본 전략
            state["response_plan"] = {
                "visualization_strategy": "none",
                "confidence": 0.0,
                "components": [{"type": "text", "priority": 1}]
            }
            state["error"] = handle_exception("ResponsePlanner", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _calculate_viz_confidence(
        self,
        data_chars: Dict[str, Any],
        capabilities: Dict[str, Any]
    ) -> float:
        """
        시각화 필요성 confidence 계산

        Args:
            data_chars: 데이터 특성
            capabilities: 분석 전략

        Returns:
            confidence 점수 (0.0~1.0)
        """
        confidence = 0.0
        rules = self.viz_config["confidence_rules"]

        # Rule 1: 시계열 데이터 (매우 높음)
        if data_chars.get("time_series") and data_chars.get("total_rows", 0) >= rules["time_series"]["min_points"]:
            confidence += rules["time_series"]["weight"]

        # Rule 2: 여러 엔티티 비교 (높음)
        if data_chars.get("multi_entity"):
            entity_count = data_chars.get("total_rows", 0)
            min_e = rules["multi_comparison"]["min_entities"]
            max_e = rules["multi_comparison"]["max_entities"]
            if min_e <= entity_count <= max_e:
                confidence += rules["multi_comparison"]["weight"]

        # Rule 3: 분포 데이터 (높음)
        if data_chars.get("has_distribution") and data_chars.get("total_rows", 0) >= rules["distribution"]["min_categories"]:
            confidence += rules["distribution"]["weight"]

        # Rule 4: 키워드 다양성 (중간)
        keyword_count = data_chars.get("keyword_count", 0)
        if keyword_count >= rules["keyword_cloud"]["min_keywords"]:
            confidence += rules["keyword_cloud"]["weight"]

        # Rule 5: 대량 데이터 (낮음)
        if data_chars.get("total_rows", 0) > rules["large_dataset"]["min_rows"]:
            confidence += rules["large_dataset"]["weight"]

        return min(confidence, 1.0)

    def _plan_components(
        self,
        strategy: str,
        confidence: float,
        data_chars: Dict[str, Any],
        capabilities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        출력 구성요소 결정

        Args:
            strategy: 시각화 전략
            confidence: confidence 점수
            data_chars: 데이터 특성
            capabilities: 분석 전략

        Returns:
            구성요소 리스트
        """
        components = []

        # 1. 텍스트 요약 (항상 포함)
        components.append({
            "type": "summary_text",
            "priority": 1,
            "required": True
        })

        # 2. 시각화 전략에 따라 추가
        if strategy == "auto":
            # 자동 시각화 생성
            if data_chars.get("time_series"):
                components.append({
                    "type": "line_chart",
                    "priority": 2,
                    "required": True,
                    "config": {"title": "시계열 트렌드"}
                })

            if data_chars.get("multi_entity"):
                components.append({
                    "type": "comparison_table",
                    "priority": 3,
                    "required": True
                })
                components.append({
                    "type": "bar_chart",
                    "priority": 4,
                    "required": True,
                    "config": {"title": "비교 분석"}
                })

            if data_chars.get("keyword_count", 0) >= 20:
                components.append({
                    "type": "wordcloud",
                    "priority": 5,
                    "required": True
                })

        elif strategy == "suggest":
            # 시각화 옵션 제안
            suggestions = []

            if data_chars.get("time_series"):
                suggestions.append("line_chart")

            if data_chars.get("multi_entity"):
                suggestions.append("bar_chart")

            if data_chars.get("keyword_count", 0) >= 15:
                suggestions.append("wordcloud")

            if suggestions:
                components.append({
                    "type": "visualization_options",
                    "priority": 2,
                    "required": False,
                    "options": suggestions
                })

        # 3. 데이터 테이블 (선택적)
        if data_chars.get("total_rows", 0) <= 50:
            components.append({
                "type": "data_table",
                "priority": 6,
                "required": False
            })

        return components
