#//==============================================================================//#
"""
synthesizer.py
최종 답변 통합

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
logger = logging.getLogger("v6_agent.synthesizer")


class Synthesizer:
    """최종 답변 통합"""

    def synthesize(self, state: AgentState) -> AgentState:
        """
        최종 답변 통합 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 로깅
            logger.info("Synthesizer 시작")

            # 1. 단계 시작
            tracker.start_step(
                node_name="Synthesizer",
                description="최종 답변 통합 중...",
                substeps=[
                    "텍스트 조합",
                    "시각화 정리",
                    "메타데이터 추가"
                ]
            )

            # 2. 워크플로우 타입 확인 (generated_images 존재 여부로 판단)
            generated_images = state.get("generated_images", [])

            # outputs 가져오기
            outputs = state.get("outputs", {})
            response_plan = state.get("response_plan", {})

            logger.debug(f"generated_images: {len(generated_images)}개")
            logger.debug(f"outputs keys: {list(outputs.keys())}")

            # 3. 이미지 생성 워크플로우 vs SQL 워크플로우
            if generated_images:
                # 이미지 생성 워크플로우
                logger.info(f"이미지 생성 워크플로우: {len(generated_images)}개 이미지")
                final_text = self._create_image_generation_response(state)

                tracker.update_substep(f"{len(generated_images)}개 이미지 생성 완료")
                tracker.complete_step(summary="이미지 생성 완료")

                state["final_response"] = {
                    "text": final_text,
                    "generated_images": generated_images,
                    "visualizations": [],
                    "tables": {},
                    "metadata": self._create_metadata(state),
                    "visualization_strategy": "none"
                }

            else:
                # SQL 워크플로우 (기존 로직)
                logger.info("SQL 워크플로우: 텍스트 답변 통합")
                final_text = self._combine_text_response(outputs)
                tracker.update_substep("텍스트 답변 조합 완료")

                # 4. 시각화 정리
                visualizations = outputs.get("visualizations", [])
                tracker.update_substep(f"{len(visualizations)}개 시각화 포함")

                # 5. 메타데이터 추가
                metadata = self._create_metadata(state)
                tracker.update_substep("메타데이터 생성 완료")

                tracker.complete_step(summary="최종 답변 통합 완료")

                # State 업데이트
                state["final_response"] = {
                    "text": final_text,
                    "visualizations": visualizations,
                    "visualization_suggestions": outputs.get("visualization_suggestions", []),
                    "tables": {
                        "comparison": outputs.get("comparison_table"),
                        "data": outputs.get("data_table")
                    },
                    "metadata": metadata,
                    "visualization_strategy": response_plan.get("visualization_strategy", "none")
                }

            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "synthesizer")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info("최종 답변 통합 성공")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except Exception as e:
            logger.error(f"Synthesizer 실패: {type(e).__name__} - {str(e)}", exc_info=True)
            tracker.error_step(
                error_msg=f"답변 통합 오류: {str(e)}",
                suggestion="부분 답변으로 제공합니다."
            )

            # 오류 시 기본 답변
            state["final_response"] = {
                "text": "답변 생성 중 오류가 발생했습니다.",
                "visualizations": [],
                "tables": {},
                "metadata": {},
                "visualization_strategy": "none"
            }
            state["error"] = handle_exception("Synthesizer", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _create_image_generation_response(self, state: AgentState) -> str:
        """
        이미지 생성 워크플로우 답변 생성

        Args:
            state: 현재 상태

        Returns:
            답변 텍스트
        """
        generated_images = state.get("generated_images", [])
        design_keywords = state.get("design_keywords", [])
        entities = state.get("parsed_entities", {})

        # 브랜드/제품 정보
        brands = entities.get("brands", [])
        products = entities.get("products", [])

        brand_text = " ".join(brands) if brands else "제품"
        product_text = " ".join(products) if products else ""

        # 답변 생성
        response_parts = [
            f"### 다이소 채널 최적화 디자인 시안",
            f"\n**원본 제품:** {brand_text} {product_text}",
            f"\n**타겟 채널:** 다이소 (5,000원 가격대 뷰티)",
        ]

        if design_keywords:
            keywords_text = ", ".join(design_keywords[:5])
            response_parts.append(f"\n**리뷰 키워드 반영:** {keywords_text}")

        response_parts.append(f"\n\n생성된 디자인 시안 **{len(generated_images)}개**를 아래에서 확인하세요.")
        response_parts.append("\n\n#### 주요 특징")
        response_parts.append("- 실제 리뷰 데이터에서 추출한 키워드 반영")
        response_parts.append("- 다이소 채널 특성: 귀여운 파스텔 톤, 10ml 미니 사이즈")
        response_parts.append("- 올리브영 프리미엄 제품의 브랜드 정체성 유지")

        return "\n".join(response_parts)

    def _combine_text_response(self, outputs: Dict[str, Any]) -> str:
        """
        텍스트 답변 조합

        Args:
            outputs: 출력 데이터

        Returns:
            조합된 텍스트
        """
        text_parts = []

        # 1. 요약 텍스트
        if "summary_text" in outputs:
            text_parts.append(outputs["summary_text"])

        # 2. 테이블 언급 (있으면)
        if outputs.get("comparison_table", {}).get("row_count", 0) > 0:
            text_parts.append("\n\n📊 **상세 비교 데이터는 아래 표를 참고하세요.**")

        # 3. 시각화 언급 (있으면)
        viz_count = len(outputs.get("visualizations", []))
        if viz_count > 0:
            text_parts.append(f"\n\n📈 **{viz_count}개의 시각화 차트를 아래에서 확인하세요.**")

        return "\n".join(text_parts)

    def _create_metadata(self, state: AgentState) -> Dict[str, Any]:
        """
        메타데이터 생성

        Args:
            state: 현재 상태

        Returns:
            메타데이터
        """
        # 전체 처리 시간 계산
        messages = state.get("messages", [])
        total_duration = sum(
            msg.get("duration", 0) for msg in messages if msg.get("duration")
        )

        # 쿼리 통계
        query_results = state.get("query_results", {})
        total_queries = query_results.get("total_queries", 0)
        successful_queries = query_results.get("data_characteristics", {}).get("successful_queries", 0)
        total_rows = query_results.get("data_characteristics", {}).get("total_rows", 0)

        # 복잡도 정보
        complexity = state.get("complexity", {})

        # SQL 메타데이터 (UI 표시용)
        sql_metadata = state.get("sql_metadata", [])

        return {
            "total_duration": round(total_duration, 2),
            "complexity": complexity.get("level", "unknown"),
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "total_data_rows": total_rows,
            "visualization_confidence": state.get("response_plan", {}).get("confidence", 0),
            "processing_steps": len(messages),
            "sql_queries": sql_metadata  # SQL 쿼리 메타데이터 추가
        }
