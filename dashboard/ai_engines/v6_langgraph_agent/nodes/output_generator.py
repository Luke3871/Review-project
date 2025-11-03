#//==============================================================================//#
"""
output_generator.py
텍스트/표/차트 출력 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import logging
from typing import Dict, Any, List
from openai import OpenAI
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os
import psycopg2
from psycopg2.extras import RealDictCursor

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import LLM_CONFIG, DB_CONFIG
from ..errors import handle_exception, LLMError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.output_generator")


class OutputGenerator:
    """출력 생성"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["output_generator"]  # 0.3
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def generate(self, state: AgentState) -> AgentState:
        """
        출력 생성 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            logger.info("OutputGenerator 시작")

            # 1. 단계 시작
            response_plan = state.get("response_plan", {})
            components = response_plan.get("components", [])

            logger.debug(f"response_plan: {response_plan}")
            logger.info(f"components 개수: {len(components)}")

            tracker.start_step(
                node_name="OutputGenerator",
                description="출력 생성 중...",
                substeps=[c["type"] for c in components if c.get("required", True)]
            )

            # 2. 각 구성요소 생성
            outputs = {}

            # 텍스트 요약
            if any(c["type"] == "summary_text" for c in components):
                logger.info("텍스트 요약 생성 시작")
                try:
                    summary = self._generate_summary_text(state)
                    outputs["summary_text"] = summary
                    logger.info(f"텍스트 요약 생성 완료 ({len(summary)} chars)")
                    tracker.update_substep("텍스트 요약 생성 완료")
                except Exception as e:
                    logger.error(f"텍스트 요약 생성 실패: {e}", exc_info=True)
                    raise

            # 비교 테이블
            if any(c["type"] == "comparison_table" for c in components):
                table = self._generate_comparison_table(state)
                outputs["comparison_table"] = table
                tracker.update_substep("비교표 생성 완료")

            # 데이터 테이블
            if any(c["type"] == "data_table" for c in components):
                data_table = self._generate_data_table(state)
                outputs["data_table"] = data_table
                tracker.update_substep("데이터 테이블 생성 완료")

            # 시각화
            viz_components = [c for c in components if c["type"] in ["line_chart", "bar_chart", "wordcloud"]]
            logger.debug(f"viz_components 개수: {len(viz_components)}")

            if viz_components:
                visualizations = self._create_visualizations(state, viz_components)
                outputs["visualizations"] = visualizations
                logger.info(f"생성된 시각화 개수: {len(visualizations)}")
                tracker.update_substep(f"{len(visualizations)}개 시각화 생성 완료")
            else:
                outputs["visualizations"] = []
                logger.debug("시각화 컴포넌트 없음")

            # 시각화 옵션 제안 (suggest 전략)
            viz_options_component = next((c for c in components if c["type"] == "visualization_options"), None)
            if viz_options_component:
                outputs["visualization_suggestions"] = viz_options_component.get("options", [])
                logger.info(f"시각화 제안: {len(outputs['visualization_suggestions'])}개")
                tracker.update_substep(f"{len(outputs['visualization_suggestions'])}개 시각화 옵션 제안")
            else:
                outputs["visualization_suggestions"] = []

            tracker.complete_step(summary=f"{len(outputs)}개 출력 구성요소 생성")

            logger.info(f"최종 outputs keys: {list(outputs.keys())}")

            # State 업데이트
            state["outputs"] = outputs
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "output_generator")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"출력 생성 성공: {len(outputs)}개 구성요소")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except Exception as e:
            logger.error(f"OutputGenerator 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"출력 생성 오류: {str(e)}",
                suggestion="기본 출력으로 진행합니다"
            )

            # 오류 시 기본 출력
            state["outputs"] = {
                "summary_text": "출력 생성 중 오류가 발생했습니다."
            }
            state["error"] = handle_exception("OutputGenerator", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _generate_summary_text(self, state: AgentState) -> str:
        """
        LLM으로 텍스트 요약 생성

        Args:
            state: 현재 상태

        Returns:
            요약 텍스트
        """
        query = state["user_query"]
        entities = state.get("parsed_entities", {})
        query_results = state.get("query_results", {}).get("results", [])

        # 쿼리 결과를 텍스트로 변환
        results_summary = []
        for i, result in enumerate(query_results, 1):
            if result["success"]:
                # datetime 객체를 문자열로 변환
                sample_data = result['data'][:3]
                safe_sample = []
                for row in sample_data:
                    safe_row = {}
                    for k, v in row.items():
                        # datetime/date 객체는 isoformat()으로 변환
                        if hasattr(v, 'isoformat'):
                            safe_row[k] = v.isoformat()
                        else:
                            safe_row[k] = v
                    safe_sample.append(safe_row)

                results_summary.append(
                    f"Q{i}: {result['sub_question']}\n"
                    f"결과: {result['row_count']}건\n"
                    f"데이터 샘플: {json.dumps(safe_sample, ensure_ascii=False, indent=2)}\n"
                )
            else:
                results_summary.append(
                    f"Q{i}: {result['sub_question']}\n"
                    f"오류: {result['error']}\n"
                )

        results_text = "\n".join(results_summary)

        # 리뷰 샘플 자동 조회
        review_samples = self._fetch_review_samples(state, limit=5)
        review_samples_text = ""
        if review_samples:
            logger.info(f"리뷰 샘플 {len(review_samples)}개 추가")
            review_samples_text = "\n\n**추가 리뷰 샘플 (최신순 5개):**\n"
            for i, sample in enumerate(review_samples, 1):
                review_samples_text += f"\n리뷰 {i}:\n"
                review_samples_text += f"- 평점: {sample.get('rating', 'N/A')}\n"
                review_samples_text += f"- 감정: {sample.get('sentiment', 'N/A')}\n"
                review_samples_text += f"- 날짜: {sample.get('review_date', 'N/A')}\n"
                review_samples_text += f"- 내용: {sample.get('review_clean', '')}\n"

        prompt = f"""당신은 LG생활건강 마케팅팀을 위한 데이터 분석가입니다.
아래 SQL 쿼리 결과를 분석하여 실무에 즉시 활용 가능한 인사이트 리포트를 작성하세요.

**사용자 질문:**
{query}

**추출된 정보:**
- 브랜드: {', '.join(entities.get('brands', [])) or '전체'}
- 제품: {', '.join(entities.get('products', [])) or '전체'}
- 속성: {', '.join(entities.get('attributes', [])) or '전체'}
- 기간: {entities.get('period', {}).get('display', '전체')}

**SQL 쿼리 결과:**
{results_text}
{review_samples_text}

---

**작성 가이드:**

위 SQL 결과 데이터를 철저히 분석하여 다음 구조로 리포트를 작성하세요.
**데이터에 없는 내용은 절대 작성하지 마세요.**

### 핵심 요약
- SQL 결과의 주요 수치를 2-3문장으로 요약
- 가장 중요한 발견사항

### 데이터 분석
- SQL 결과에서 발견한 패턴과 트렌드
- 구체적 수치 제시 (건수, 비율, 평균 등)
- preprocessed_reviews 데이터인 경우:
  * 제품특성 (제형, 발림성, 향, 지속력 등)
  * 감정요약 (긍정/부정 비율, 핵심표현)
  * 장점/단점 키워드
  * 구매동기, 경쟁사 비교 (데이터 있을 경우만)

### 리뷰 샘플 (IMPORTANT)
- **"추가 리뷰 샘플" 섹션이 제공된 경우 반드시 포함**
- 제공된 리뷰 중 **질문 의도에 맞는 대표 리뷰 3-5개** 선택:
  * 사용자 질문이 "장점", "만족", "효과" 관련 → 긍정 리뷰 위주
  * 사용자 질문이 "단점", "불만", "문제" 관련 → 부정 리뷰 위주
  * 사용자 질문이 "기획", "가격", "일반" 관련 → 다양한 평점 골고루
- 각 리뷰는 다음 형식으로 작성:
  ```
  **리뷰 1** (평점: 5, 감정: 긍정적, 날짜: 2025-10-15)
  > "리뷰 원문 내용을 그대로 인용..."
  ```
- 리뷰가 제공되지 않았으면 이 섹션 생략

### 마케팅 시사점
- SQL 결과 기반 실무 제안
- 캠페인 소구점 (실제 핵심 표현 활용)
- 개선 영역 (단점/불만 기반)
- 타겟 확장 기회

### 데이터 범위
- 분석 건수, 기간, 출처 간략히 명시

---

**중요 원칙:**
1. **SQL 결과에 있는 데이터만 사용** - 없는 내용 추정 금지
2. **구체적 수치 명시** - 모든 주장에 숫자 포함
3. **리뷰 원문은 SQL 결과에 있는 것만 인용**
4. **데이터 없는 섹션은 생략**
5. **이모지 사용 금지** - 깔끔한 마크다운만 사용
6. **간결하게** - 핵심만 전달

**SQL 결과를 철저히 분석하여 데이터 기반 리포트를 작성하세요:**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        result_text = response.choices[0].message.content.strip()

        # Debug 추적
        self._add_debug_trace(
            state=state,
            step="generate_summary_text",
            prompt=prompt,
            llm_response=result_text
        )

        return result_text

    def _generate_comparison_table(self, state: AgentState) -> Dict[str, Any]:
        """
        비교 테이블 생성

        Args:
            state: 현재 상태

        Returns:
            테이블 데이터
        """
        query_results = state.get("query_results", {}).get("results", [])

        # 성공한 쿼리 결과만 필터링
        successful_results = [r for r in query_results if r["success"] and r["row_count"] > 0]

        if not successful_results:
            return {"data": [], "columns": []}

        # 첫 번째 결과의 컬럼을 기준으로 테이블 생성
        all_data = []
        for result in successful_results:
            all_data.extend(result["data"])

        if not all_data:
            return {"data": [], "columns": []}

        # DataFrame으로 변환
        df = pd.DataFrame(all_data)

        return {
            "data": df.to_dict("records"),
            "columns": list(df.columns),
            "row_count": len(df),
            "dataframe": df
        }

    def _generate_data_table(self, state: AgentState) -> Dict[str, Any]:
        """
        데이터 테이블 생성 (전체 결과)

        Args:
            state: 현재 상태

        Returns:
            테이블 데이터
        """
        return self._generate_comparison_table(state)

    def _create_visualizations(
        self,
        state: AgentState,
        viz_components: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        시각화 생성

        Args:
            state: 현재 상태
            viz_components: 시각화 구성요소 리스트

        Returns:
            시각화 객체 리스트
        """
        query_results = state.get("query_results", {}).get("results", [])
        visualizations = []

        for component in viz_components:
            viz_type = component["type"]
            config = component.get("config", {})

            # 관련 데이터 찾기
            relevant_data = []
            for result in query_results:
                if result["success"] and result["row_count"] > 0:
                    relevant_data.extend(result["data"])

            if not relevant_data:
                continue

            df = pd.DataFrame(relevant_data)

            # 시각화 타입별 생성
            try:
                if viz_type == "line_chart":
                    fig = self._create_line_chart(df, config)
                    if fig:
                        visualizations.append({
                            "type": "line_chart",
                            "figure": fig,
                            "title": config.get("title", "트렌드 차트")
                        })

                elif viz_type == "bar_chart":
                    fig = self._create_bar_chart(df, config)
                    if fig:
                        visualizations.append({
                            "type": "bar_chart",
                            "figure": fig,
                            "title": config.get("title", "비교 차트")
                        })

                elif viz_type == "wordcloud":
                    fig = self._create_wordcloud(df, config)
                    if fig:
                        visualizations.append({
                            "type": "wordcloud",
                            "figure": fig,
                            "title": "키워드 워드클라우드"
                        })

            except Exception as e:
                logger.warning(f"시각화 생성 오류 ({viz_type}): {str(e)}")
                continue

        return visualizations

    def _create_line_chart(self, df: pd.DataFrame, config: Dict) -> go.Figure:
        """라인 차트 생성"""
        if df.empty:
            return None

        x_col = self._detect_time_column(df)
        y_col = self._detect_metric_column(df)

        if x_col not in df.columns or y_col not in df.columns:
            return None

        fig = px.line(
            df,
            x=x_col,
            y=y_col,
            title=config.get("title", "트렌드 차트"),
            labels={x_col: "기간", y_col: "값"}
        )

        fig.update_traces(mode='lines+markers')
        fig.update_layout(
            height=400,
            showlegend=False,
            hovermode='x unified'
        )

        return fig

    def _create_bar_chart(self, df: pd.DataFrame, config: Dict) -> go.Figure:
        """막대 차트 생성"""
        if df.empty:
            return None

        x_col = self._detect_category_column(df)
        y_col = self._detect_metric_column(df)

        if x_col not in df.columns or y_col not in df.columns:
            return None

        fig = px.bar(
            df,
            x=x_col,
            y=y_col,
            title=config.get("title", "비교 차트"),
            labels={x_col: "카테고리", y_col: "값"}
        )

        fig.update_layout(
            height=400,
            showlegend=False
        )

        return fig

    def _create_wordcloud(self, df: pd.DataFrame, config: Dict) -> plt.Figure:
        """워드클라우드 생성"""
        if df.empty:
            return None

        text_col = self._detect_text_column(df)
        freq_col = self._detect_metric_column(df)

        if text_col not in df.columns:
            return None

        # 빈도 딕셔너리 생성
        if freq_col in df.columns:
            word_freq = dict(zip(df[text_col], df[freq_col]))
        else:
            word_freq = dict(zip(df[text_col], [1] * len(df)))

        # 한글 폰트 경로 찾기
        font_path = None
        font_candidates = [
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/malgunbd.ttf',
            'C:/Windows/Fonts/NanumGothic.ttf',
        ]

        for font in font_candidates:
            if os.path.exists(font):
                font_path = font
                break

        # 원형 마스크
        x, y = np.ogrid[:800, :800]
        mask = (x - 400) ** 2 + (y - 400) ** 2 > 380 ** 2
        mask = 255 * mask.astype(int)

        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path=font_path,
            width=800,
            height=800,
            background_color='white',
            colormap='Set2',
            relative_scaling=0.7,
            min_font_size=12,
            max_font_size=100,
            mask=mask,
            max_words=30,
            random_state=42
        ).generate_from_frequencies(word_freq)

        # Figure 생성
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
        fig.patch.set_facecolor('#f8f9fa')
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')

        if font_path:
            font_prop = fm.FontProperties(fname=font_path, size=14, weight='bold')
            ax.set_title(config.get("title", "키워드 워드클라우드"), fontproperties=font_prop, pad=20)
        else:
            ax.set_title(config.get("title", "키워드 워드클라우드"), fontsize=14, pad=20, weight='bold')

        plt.tight_layout()
        return fig

    def _detect_time_column(self, df: pd.DataFrame) -> str:
        """시간 컬럼 감지"""
        for col in ["month", "date", "period", "year", "review_date"]:
            if col in df.columns:
                return col
        return df.columns[0] if len(df.columns) > 0 else "date"

    def _detect_metric_column(self, df: pd.DataFrame) -> str:
        """지표 컬럼 감지"""
        for col in ["count", "avg_rating", "review_count", "percentage"]:
            if col in df.columns:
                return col
        return df.columns[-1] if len(df.columns) > 0 else "count"

    def _detect_category_column(self, df: pd.DataFrame) -> str:
        """카테고리 컬럼 감지"""
        for col in ["brand", "product_name", "channel", "category"]:
            if col in df.columns:
                return col
        return df.columns[0] if len(df.columns) > 0 else "category"

    def _detect_text_column(self, df: pd.DataFrame) -> str:
        """텍스트 컬럼 감지"""
        for col in ["keyword", "advantage", "disadvantage", "text", "키워드", "장점", "단점"]:
            if col in df.columns:
                return col
        return df.columns[0] if len(df.columns) > 0 else "text"

    def _fetch_review_samples(self, state: AgentState, limit: int = 5) -> List[Dict[str, Any]]:
        """
        브랜드/제품 기반으로 리뷰 샘플 자동 조회

        Args:
            state: AgentState (parsed_entities 포함)
            limit: 조회할 리뷰 개수 (기본 5개)

        Returns:
            리뷰 샘플 리스트 (review_clean, rating, review_date, sentiment 포함)
        """
        try:
            entities = state.get("parsed_entities", {})
            brands = entities.get("brands", [])
            products = entities.get("products", [])

            # 브랜드나 제품 정보가 없으면 빈 리스트 반환
            if not brands and not products:
                logger.debug("브랜드/제품 정보 없음, 리뷰 샘플 조회 스킵")
                return []

            # SQL 쿼리 구성
            where_clauses = []
            if brands:
                where_clauses.append(f"brand = '{brands[0]}'")
            if products:
                where_clauses.append(f"product_name LIKE '%{products[0]}%'")

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            sql = f"""
            SELECT
                review_clean,
                rating,
                review_date,
                analysis->'감정요약'->>'전반적평가' as sentiment,
                brand,
                product_name
            FROM preprocessed_reviews
            WHERE {where_sql}
              AND review_clean IS NOT NULL
            ORDER BY CAST(review_date AS DATE) DESC
            LIMIT {limit}
            """

            logger.debug(f"리뷰 샘플 조회 SQL: {sql[:200]}...")

            # DB 연결 및 실행
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(sql)
            rows = cur.fetchall()

            # dict로 변환
            samples = [dict(row) for row in rows]

            cur.close()
            conn.close()

            logger.info(f"리뷰 샘플 조회 완료: {len(samples)}개")
            return samples

        except Exception as e:
            logger.error(f"리뷰 샘플 조회 실패: {e}", exc_info=True)
            return []

    def _add_debug_trace(
        self,
        state: Dict[str, Any],
        step: str,
        prompt: str,
        llm_response: str,
        parsed_result: Any = None
    ):
        """
        Debug 모드일 때 LLM 추적 정보 저장

        Args:
            state: AgentState
            step: 단계 이름
            prompt: LLM 프롬프트
            llm_response: LLM 원본 응답
            parsed_result: 파싱된 결과 (옵션)
        """
        if state.get("debug_mode", False):
            state.setdefault("debug_traces", []).append({
                "node": "OutputGenerator",
                "step": step,
                "prompt": prompt[:1000] if len(prompt) > 1000 else prompt,  # 처음 1000자
                "llm_response": llm_response[:1000] if len(llm_response) > 1000 else llm_response,
                "parsed_result": parsed_result
            })
