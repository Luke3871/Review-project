#//==============================================================================//#
"""
capability_detector.py
사용자 질문의 분석 전략 결정 (data_scope, aggregation_type 등)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import logging
from typing import Dict, Any
from openai import OpenAI

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import LLM_CONFIG
from ..errors import handle_exception, LLMError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.capability_detector")


class CapabilityDetector:
    """분석 전략 결정"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["capability_detector"]
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def detect(self, state: AgentState) -> AgentState:
        """
        분석 전략 결정 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 로깅
            logger.info("CapabilityDetector 시작")
            logger.debug(f"입력 엔티티: {state.get('parsed_entities')}")

            # 1. 단계 시작
            tracker.start_step(
                node_name="CapabilityDetector",
                description="데이터 전략 수립 중...",
                substeps=[
                    "데이터 소스 선택",
                    "집계 방식 결정",
                    "분석 깊이 판단"
                ]
            )

            # 2. LLM으로 capability 감지
            capabilities = self._detect_capabilities(
                state["user_query"],
                state["parsed_entities"]
            )

            logger.debug(f"감지 결과: {capabilities}")

            # 3. 결과 업데이트
            data_scope_display = {
                "preprocessed_reviews": "preprocessed_reviews (구조화된 분석)",
                "reviews": "reviews (원문 및 메타정보)",
                "join": "reviews + preprocessed_reviews (통합)"
            }
            tracker.update_substep(
                f"데이터 소스: {data_scope_display.get(capabilities['data_scope'], capabilities['data_scope'])}"
            )

            agg_type_display = {
                "time_series": "시계열 트렌드",
                "comparison": "대상 비교",
                "distribution": "분포 분석",
                "keyword_frequency": "키워드 빈도",
                "simple": "단순 조회"
            }
            tracker.update_substep(
                f"집계 방식: {agg_type_display.get(capabilities['aggregation_type'], capabilities['aggregation_type'])}"
            )

            analysis_display = {
                "overview": "전반적 요약",
                "attribute": "속성별 분석",
                "sentiment": "감정 분석",
                "keyword": "키워드 분석",
                "pros_cons": "장단점 분석"
            }
            tracker.update_substep(
                f"분석 깊이: {analysis_display.get(capabilities['analysis_depth'], capabilities['analysis_depth'])}"
            )

            tracker.complete_step(summary="데이터 전략 수립 완료")

            # State 업데이트
            state["capabilities"] = capabilities
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "capability_detector")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"전략 수립 성공: data_scope={capabilities.get('data_scope')}, aggregation={capabilities.get('aggregation_type')}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except json.JSONDecodeError as e:
            # JSON 파싱 실패
            logger.error(f"전략 감지 실패 - JSON 파싱 오류: {e}", exc_info=True)

            tracker.error_step(
                error_msg="전략 감지 형식 오류 (LLM 응답 파싱 실패)",
                suggestion="질문을 다시 확인해주세요"
            )

            state["error"] = LLMError("CapabilityDetector", f"JSON 파싱 실패: {str(e)}", original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except Exception as e:
            # 일반 예외
            logger.error(f"CapabilityDetector 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"전략 수립 오류: {str(e)}",
                suggestion="질문을 다시 확인해주세요"
            )

            state["error"] = handle_exception("CapabilityDetector", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _detect_capabilities(self, query: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM을 사용하여 분석 전략 결정

        Args:
            query: 사용자 질문
            entities: 추출된 엔티티

        Returns:
            분석 전략
        """
        prompt = f"""당신은 데이터 분석 전략을 결정하는 시스템입니다.
사용자 질문과 추출된 엔티티를 바탕으로 최적의 분석 방법을 JSON으로 반환하세요:

**판단 항목:**

1. data_scope: 사용할 데이터 소스 (매우 중요!)

   **"reviews" 테이블 (314,285건)을 사용해야 하는 경우:**
   - 평점 조회 (평균 평점, 평점 분포, 평점 트렌드 등)
   - 리뷰 수 집계
   - 날짜별 트렌드 분석
   - 원문 리뷰 샘플
   - 키워드: "평점", "평균", "분포", "트렌드", "리뷰수", "개수", "몇 개"

   **"preprocessed_reviews" 테이블 (5,000건)을 사용해야 하는 경우:**
   - 속성별 분석 (보습력, 발림성, 향, 지속력 등)
   - 장점/단점 분석
   - 감정 요약 (긍정/부정)
   - 키워드 추출
   - 주의: rating 칼럼 없음! 평점 조회 불가

   **"join" (두 테이블 조인)을 사용해야 하는 경우:**
   - 평점 + 텍스트 분석 둘 다 필요
   - 예: "평점 높은 제품의 장점 분석"

2. aggregation_type: 집계 방식
   - "time_series": 시간별 트렌드 (월별, 일별 변화)
   - "comparison": 여러 대상 비교 (브랜드, 제품 간 비교)
   - "distribution": 분포 분석 (평점 분포, 카테고리 분포)
   - "keyword_frequency": 키워드 빈도 분석
   - "simple": 단순 조회 (특정 정보만 가져오기)

3. group_by: 그룹화 기준
   - "brand": 브랜드별
   - "product": 제품별
   - "channel": 채널별
   - "period": 기간별 (시계열)
   - "none": 그룹화 없음

4. analysis_depth: 분석 깊이
   - "overview": 전반적 요약 (평점, 리뷰 수 등) → reviews 테이블
   - "attribute": 속성별 분석 (보습력, 발림성 등) → preprocessed_reviews 테이블
   - "sentiment": 감정 분석 (긍정/부정) → preprocessed_reviews 테이블
   - "keyword": 키워드 분석 → preprocessed_reviews 테이블
   - "pros_cons": 장단점 분석 → preprocessed_reviews 테이블

5. metric: 측정 지표
   - "rating": 평점 → 반드시 reviews 또는 join 사용!
   - "count": 개수
   - "percentage": 비율

**예시:**

질문: "빌리프 보습력 어때?"
엔티티: {{"brands": ["빌리프"], "attributes": ["보습력"]}}
→ {{"data_scope": "preprocessed_reviews", "aggregation_type": "simple", "group_by": "none", "analysis_depth": "attribute", "metric": "count"}}

질문: "빌리프 평점 어때?"
엔티티: {{"brands": ["빌리프"], "attributes": ["평점"]}}
→ {{"data_scope": "reviews", "aggregation_type": "simple", "group_by": "none", "analysis_depth": "overview", "metric": "rating"}}
(이유: "평점" 키워드 → reviews 테이블 사용)

질문: "빌리프 평점 분포"
엔티티: {{"brands": ["빌리프"], "attributes": ["평점분포"]}}
→ {{"data_scope": "reviews", "aggregation_type": "distribution", "group_by": "none", "analysis_depth": "overview", "metric": "rating"}}
(이유: "평점분포" → reviews 테이블 사용)

질문: "VT랑 라로슈포제 평점 비교"
엔티티: {{"brands": ["VT", "라로슈포제"]}}
→ {{"data_scope": "reviews", "aggregation_type": "comparison", "group_by": "brand", "analysis_depth": "overview", "metric": "rating"}}
(이유: "평점 비교" → reviews 테이블 사용)

질문: "최근 3개월 CNP 평점 트렌드"
엔티티: {{"brands": ["CNP"], "period": {{"type": "recent_months", "value": 3}}}}
→ {{"data_scope": "reviews", "aggregation_type": "time_series", "group_by": "period", "analysis_depth": "overview", "metric": "rating"}}
(이유: "평점 트렌드" → reviews 테이블 사용)

질문: "빌리프 샘플 리뷰 보여줘"
엔티티: {{"brands": ["빌리프"]}}
→ {{"data_scope": "reviews", "aggregation_type": "simple", "group_by": "none", "analysis_depth": "overview", "metric": "count"}}

질문: "빌리프 장점이랑 실제 리뷰 같이 보여줘"
엔티티: {{"brands": ["빌리프"], "attributes": ["장점"]}}
→ {{"data_scope": "join", "aggregation_type": "simple", "group_by": "none", "analysis_depth": "pros_cons", "metric": "count"}}

**사용자 질문:**
{query}

**추출된 엔티티:**
{json.dumps(entities, ensure_ascii=False, indent=2)}

**JSON만 반환하세요 (다른 설명 없이):**"""

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

            capabilities = json.loads(result_text)
            return capabilities

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 실패: {result_text[:100]}... (error: {str(e)})")
