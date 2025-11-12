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
                # 전체 데이터 전달 (LLM이 정확한 분석을 위해 필요)
                all_data = result['data']
                safe_data = []
                for row in all_data:
                    safe_row = {}
                    for k, v in row.items():
                        # datetime/date 객체는 isoformat()으로 변환
                        if hasattr(v, 'isoformat'):
                            safe_row[k] = v.isoformat()
                        else:
                            safe_row[k] = v
                    safe_data.append(safe_row)

                results_summary.append(
                    f"Q{i}: {result['sub_question']}\n"
                    f"결과: {result['row_count']}건\n"
                    f"전체 데이터:\n{json.dumps(safe_data, ensure_ascii=False, indent=2)}\n"
                )
            else:
                results_summary.append(
                    f"Q{i}: {result['sub_question']}\n"
                    f"오류: {result['error']}\n"
                )

        results_text = "\n".join(results_summary)

        # 리뷰 샘플 자동 조회
        review_samples = self._fetch_review_samples(state, limit=5)

        # review_samples_text 조건부 생성
        if review_samples:
            logger.info(f"리뷰 샘플 {len(review_samples)}개 추가")
            review_samples_text = "\n\n**추가 리뷰 샘플 (최신순 5개):**\n"
            for i, sample in enumerate(review_samples, 1):
                review_samples_text += f"\n리뷰 {i}:\n"
                review_samples_text += f"- 평점: {sample.get('rating', 'N/A')}\n"
                review_samples_text += f"- 감정: {sample.get('sentiment', 'N/A')}\n"
                review_samples_text += f"- 날짜: {sample.get('review_date', 'N/A')}\n"
                review_samples_text += f"- 내용: {sample.get('review_clean', '')}\n"
        else:
            review_samples_text = ""  # 빈 문자열

        # prompt는 무조건 정의 (review_samples 여부와 무관)
        prompt = f"""당신은 LG생활건강 마케팅팀을 위한 리뷰 데이터 분석 전문가입니다.
올리브영, 쿠팡, 다이소 리뷰에서 샘플링해서 전치리한 5000개의 리뷰 데이터를 분석한 결과를 바탕으로 사용자 질문에 답변합니다.

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

## 답변 작성 가이드

### 1. 핵심 발견 사항 (가장 중요)
**리뷰 텍스트의 구체적 인사이트를 발굴하세요:**
모든 답변에 대해서 그렇게 답변하게된 해당 리뷰의 원본을 같이 제시하세요

✅ **좋은 예시:**
- "토너패드 카테고리에서 '각질제거' 키워드가 '보습'보다 3배 더 많이 언급됩니다 (각질 1,247건 vs 보습 412건). 특히 '코 각질', '턱 각질' 등 부위별 언급이 두드러지며, '화장솜 대용'이라는 사용법 키워드도 상위 10위권에 등장합니다."
- "마몽드 로즈워터 톤업 크림은 '톤업' 관련 키워드가 789건으로 1위이나, '백탁' 부정 키워드도 234건으로 함께 나타납니다. 리뷰 원문을 보면 '피부톤이 밝은 사람은 괜찮지만 어두운 편이면 백탁현상'이라는 조건부 평가가 반복됩니다."

❌ **피해야 할 표현:**
- "전반적으로 긍정적입니다" → 너무 추상적
- "평점이 4.5로 높습니다" → 평점만으로는 의미 없음
- "리뷰가 많아서 인기있습니다" → 숫자만 나열

**분석할 요소들:**
- **키워드 패턴**: 어떤 키워드가 몇 건 나왔는지 + 함께 나오는 연관 키워드
- **속성 점수**: 각 속성(보습력, 발림성 등)의 평균 점수와 분포
- **긍정/부정 이유**: 왜 좋다/나쁘다고 했는지 구체적 표현 추출
- **구매 동기**: "~ 때문에 샀다"는 표현들
- **사용 맥락**: 어떤 상황에서, 누가, 어떻게 사용하는지
- **개선 요청**: "~했으면 좋겠다"는 니즈

### 2. 구체적 수치 제시
**SQL 결과에 있는 수치만 사용 (추정 절대 금지):**

✅ **제공할 수치:**
- 리뷰 건수: "총 2,456건 분석"
- 비율: "긍정 리뷰 82.3% (2,023건), 부정 리뷰 17.7% (433건)"
- 평균: "보습력 평균 4.2/5.0"
- 순위: "키워드 출현 빈도 상위 5개: 촉촉함(892건), 가성비(654건)..."
- 비교: "A 브랜드는 234건, B 브랜드는 189건으로 A가 24% 더 많음"

❌ **금지사항:**
- "약 ~정도", "~쯤", "거의 ~" 등 추정 표현
- SQL 결과에 없는 수치 언급
- 비율 계산 오류 (총합이 100% 초과/미달)

### 3. 리뷰 샘플 인용
**제공된 리뷰 중 질문 의도에 가장 부합하는 것을 선택:**

**인용 형식:**
```
**리뷰 1** (평점: 5.0, 감정: 긍정, 날짜: 2024-10-15)
> "원문 그대로 인용..."

**리뷰 2** (평점: 4.0, 감정: 긍정, 날짜: 2024-10-12)
> "원문 그대로 인용..."
```

**선택 기준:**
- 속성 질문 → 해당 속성 키워드가 명확한 리뷰
- 비교 질문 → 각 대상별로 특징이 드러나는 리뷰 (각 5개씩, 총 10개)
- 장단점 질문 → 긍정 리뷰 3개 + 부정 리뷰 2개
- 최신순/평점순 등 정렬 기준 명시

**리뷰 개수:**
- 기본: 5개
- 비교 질문: 각 대상별 5개씩 (총 10개)
- 간단한 질문: 3개
- 복잡한 분석: 7-10개

### 4. 실무 시사점 
**데이터에 기반한 실행 가능한 제안:**

✅ **좋은 시사점:**
- "'각질제거' 키워드가 강점이므로, 상세페이지 상단에 '각질케어' 문구 배치 추천"
- "'백탁' 부정 키워드가 234건이므로, 제품 설명에 '피부톤별 발림 팁' 추가 필요"
- "구매동기 1위가 '선물용'(567건)이므로, 기프트 세트 기획 고려"

❌ **근거 없는 제안:**
- "마케팅을 강화하세요" → 너무 일반적
- "제품을 개선하세요" → 구체성 없음

---

## 답변 스타일별 예시

### 패턴 1: 간단한 질문 (평점, 리뷰수 등)
**질문:** "빌리프 평점 어때?"

**답변 구조:**
```
빌리프는 총 3,456건의 리뷰에서 평균 4.3점을 기록했습니다. 
긍정 리뷰가 85.2%(2,945건)로 높은 편이며, 특히 '수분크림' 카테고리에서 
'보습력'(1,234건)과 '흡수력'(892건) 키워드가 상위권입니다.

**대표 리뷰 3개:**
[리뷰 샘플]
```
**길이:** 2-3문단

---

### 패턴 2: 속성 분석
**질문:** "토너패드 보습력 어때?"

**답변 구조:**
```
## 보습력 전체 분석
토너패드 카테고리 리뷰 5,678건 중 '보습' 관련 키워드는 2,134건(37.6%)에서 
언급되었습니다. 보습력 속성 평균 점수는 4.1/5.0입니다.

### 긍정 평가 (1,823건, 85.4%)
- 핵심 키워드: '촉촉함', '수분', '건조하지않음'
- 연관 표현: '아침까지 촉촉', '겨울에도 OK', '수분 장벽'
[긍정 리뷰 3개]

### 부정 평가 (311건, 14.6%)
- 핵심 키워드: '건조함', '수분부족', '덧바름'
- 연관 표현: '시간 지나면 당김', '크림 필수'
[부정 리뷰 2개]

### 실무 시사점
'아침까지 촉촉' 표현이 89건으로 야간 보습 효과가 핵심 만족 포인트입니다.
```
**길이:** 4-6문단

---

### 패턴 3: 비교 질문
**질문:** "마몽드랑 미모 토너패드 비교해줘"

**답변 구조:**
```
## 전체 비교 요약
| 항목 | 마몽드 | 미모 |
|------|--------|------|
| 리뷰 수 | 2,345건 | 1,876건 |
| 평균 평점 | 4.4 | 4.2 |
| 보습력 평균 | 4.3 | 4.0 |
| 주요 키워드 | 각질제거(892건) | 진정(654건) |

## 마몽드 장점
[구체적 키워드 분석 + 수치]
**대표 리뷰 5개:**
[리뷰 샘플]

## 미모 장점
[구체적 키워드 분석 + 수치]
**대표 리뷰 5개:**
[리뷰 샘플]

## 선택 가이드
- 각질 고민 → 마몽드 (각질제거 키워드 2.1배 많음)
- 민감성 피부 → 미모 (진정 키워드 1.8배 많음)
```
**길이:** 6-8문단

---

### 패턴 4: 트렌드 질문
**질문:** "토너패드 트렌드 변화 보여줘"

**답변 구조:**
```
## 2024년 분기별 키워드 변화

### Q1 (1-3월)
- 주요 키워드: 각질제거(892건), 보습(654건)
- 특징: 겨울 건조함 대응 수요

### Q2 (4-6월)
- 주요 키워드: 진정(1,023건), 쿨링(567건)
- 특징: '쿨링' 키워드 전 분기 대비 340% 증가

[분기별 대표 리뷰 각 2개]

### 시사점
계절별 키워드 전환이 명확하므로, 시즌별 마케팅 메시지 조정 필요
```
**길이:** 5-7문단

---

### 패턴 5: 제품 리뷰 종합 분석
**질문:** "빌리프 아쿠아밤 리뷰 분석해줘"

**답변 구조:**
```
## 전체 개요
빌리프 아쿠아밤은 총 2,345건의 리뷰에서 평균 4.3점을 기록했습니다.
- 긍정 리뷰: 1,987건 (84.7%)
- 부정 리뷰: 358건 (15.3%)
- 분석 기간: 2024.01.01 - 2024.10.31

## 주요 키워드 분석
### 상위 10개 키워드
아래의 숫자는 예시입니다. 그대로 사용하면 안됩니다. 데이터에 기반해서 수치를 다시 적으세요
1. 보습력 (892건, 38.0%)
2. 흡수력 (654건, 27.9%)
3. 촉촉함 (567건, 24.2%)
4. 가성비 (445건, 19.0%)
5. 끈적임 (234건, 10.0%) - 부정
[6-10위 계속]

### 키워드 조합 패턴
- "보습력 + 지속력": 234건 → "밤까지 촉촉"
- "흡수력 + 빠름": 189건 → "금방 흡수됨"
- "끈적임 + 여름": 123건 → "여름엔 무거움"

## 속성별 평가
| 속성 | 평균 점수 | 긍정 | 부정 | 주요 언급 |
|------|-----------|------|------|-----------|
| 보습력 | 4.5/5.0 | 892건 | 67건 | "24시간 보습" |
| 흡수력 | 4.2/5.0 | 654건 | 123건 | "빠른 흡수" vs "끈적임" |
| 발림성 | 4.3/5.0 | 567건 | 89건 | "부드러움" |
| 향 | 3.8/5.0 | 345건 | 234건 | "무향 선호" 많음 |

## 긍정 리뷰 심층 분석 (1,987건)
### 핵심 장점
1. **보습력** (892건, 44.9%)
   - "밤에 발라도 아침까지 촉촉" (234건)
   - "겨울 건조함 해결" (189건)
   - "수분크림 안 발라도 됨" (156건)

2. **흡수력** (654건, 32.9%)
   - "바르자마자 쏙 흡수" (267건)
   - "번들거림 없음" (198건)

3. **가성비** (445건, 22.4%)
   - "용량 대비 저렴" (234건)
   - "오래 씀" (156건)

**대표 긍정 리뷰 5개:**
**리뷰 1** (평점: 5.0, 감정: 긍정, 날짜: 2024-10-25)
> "건성인데 이거 바르면 진짜 24시간 촉촉해요. 아침에 일어나도 피부가 당기지 않고 보들보들합니다. 흡수도 빨라서 끈적임 없이 바로 자도 되고 가격도 착해서 매일 듬뿍 바르고 있어요."

**리뷰 2** (평점: 5.0, 감정: 긍정, 날짜: 2024-10-20)
> "여러 수분크림 써봤는데 이게 제일 좋아요. 제형이 묽어서 발림성 좋고 흡수도 빨라요. 무엇보다 아침까지 보습력이 유지돼서 겨울에 딱입니다."

[리뷰 3-5 계속...]

## 부정 리뷰 심층 분석 (358건)
### 핵심 단점
1. **끈적임** (123건, 34.4%)
   - "여름엔 무거움" (67건)
   - "베개에 묻음" (34건)
   - 주로 지성/복합성 피부 언급

2. **향** (89건, 24.9%)
   - "인공 향" (45건)
   - "무향 원함" (34건)

3. **가격** (67건, 18.7%)
   - "용량 대비 비쌈" (34건)
   - "세일 기다림" (23건)

**대표 부정 리뷰 3개:**
**리뷰 1** (평점: 2.0, 감정: 부정, 날짜: 2024-09-15)
> "보습력은 좋은데 여름에 쓰기엔 너무 무거워요. 지성 피부라 그런지 끈적이는 느낌이 불편하고 베개에도 묻어나더라고요. 겨울용으로는 괜찮을 것 같아요."

[리뷰 2-3 계속...]

## 구매 동기 분석 (상위 5개)
1. 건조함 해결 (567건, 24.2%) - "피부 당김", "각질"
2. 리뷰 보고 (445건, 19.0%) - "평점 높아서", "후기 좋아서"
3. 재구매 (389건, 16.6%) - "또 샀어요", "벌써 3통째"
4. 선물 (234건, 10.0%) - "선물용", "어머니께"
5. 할인 (189건, 8.1%) - "세일해서", "1+1"

## 사용 패턴
- **시간대**: 밤 (67.8%), 아침 (32.2%)
- **계절**: 겨울 (45.6%), 가을 (28.9%), 봄 (15.5%), 여름 (10.0%)
- **피부 타입**: 건성 (56.7%), 복합성 (28.9%), 지성 (14.4%)
- **연령대**: 20대 (45.6%), 30대 (34.5%), 40대+ (19.9%)

## 경쟁 제품 비교 (리뷰 내 언급)
| 비교 대상 | 언급 횟수 | 주요 비교 내용 |
|-----------|-----------|----------------|
| 라로슈포제 시카플라스트 밤 | 234건 | "시카보다 가볍고 흡수 빠름" |
| 닥터자르트 시카페어 크림 | 189건 | "자르트보다 저렴하고 용량 많음" |
| 토리든 다이브인 수딩 크림 | 156건 | "토리든보다 보습력 강함" |

## 시간대별 트렌드
### 2024년 분기별 변화
- **Q1 (1-3월)**: 리뷰 678건, 평균 4.2점
  - 키워드: 건조, 겨울, 각질
- **Q2 (4-6월)**: 리뷰 489건, 평균 4.3점
  - 키워드: 환절기, 보습
- **Q3 (7-9월)**: 리뷰 534건, 평균 4.1점
  - 키워드: 무겁다, 끈적임 (여름 비수기)
- **Q4 (10월)**: 리뷰 644건, 평균 4.5점
  - 키워드: 재구매, 겨울준비 (수요 증가)

## 개선 요청 및 니즈 (상위 5개)
1. 무향 버전 출시 (89건) - "향 없었으면"
2. 대용량 출시 (67건) - "펌프형 큰 거"
3. 여름용 경량 버전 (56건) - "가벼운 제형"
4. 세트 구성 (45건) - "토너랑 세트"
5. 리필 제품 (34건) - "친환경 리필"

## 실무 시사점

### 마케팅 전략
1. **메인 메시지**: "24시간 지속 보습력" 강조 (234건 언급)
   - 상세페이지 상단에 "아침까지 촉촉" 카피 배치
   - Before/After 타임랩스 콘텐츠 제작

2. **타겟팅**: 건성 피부 × 20-30대 × 겨울 시즌 집중
   - Q4-Q1 프로모션 강화 (리뷰 활동 22% 증가 확인)

3. **경쟁 우위**: 
   - vs 라로슈포제: "가볍고 빠른 흡수" 차별화
   - vs 닥터자르트: "가성비" 강조 (용량/가격)

### 제품 개발
1. **라인 확장 안**:
   - 무향 버전 (부정 리뷰 89건)
   - 라이트 버전 (여름용, 지성 피부용)
   - 대용량 펌프형 (니즈 67건)

2. **개선 포인트**:
   - 제형 경량화 연구 (끈적임 123건)
   - 향 재조정 또는 무향 옵션

### 유통/프로모션
1. **세일 타이밍**: Q3 (여름 비수기) 할인 효과적
2. **번들 구성**: 토너/세럼과 세트 (니즈 45건)
3. **선물용 패키지**: 10% 구매 동기 (234건)

### 콘텐츠 전략
1. **피부 타입별 사용법 가이드**
   - 건성: 듬뿍 / 지성: 얇게 (피부타입별 불만 해소)
2. **계절별 활용 팁**
   - 여름: 냉장 보관 후 사용
   - 겨울: 멀티 밤으로 활용
3. **UGC 캠페인**: 
   - "#24시간챌린지" - 지속력 증명
   - 재구매 인증 이벤트 (재구매 16.6%)
```
---
### 패턴 3: 비교 질문 - 키워드 중심 분석
**질문:** "피지오겔 DMT랑 라로슈포제 시카플라스트 비교해줘"

**답변 구조:**
```
## 비교 개요

피지오겔 DMT 로션과 라로슈포제 시카플라스트 밤의 키워드 패턴을 분석했습니다.

| 항목 | 피지오겔 DMT | 라로슈포제 시카플라스트 |
|------|-------------|------------------------|
| 분석 리뷰 수 | 50건 | 45건 |
| 분석 기간 | 2024.01-10 | 2024.01-10 |
| 총 키워드 수 | 180개 | 165개 |

---

## 1. 핵심 키워드 비교

### 피지오겔 DMT - 상위 15개 키워드
| 순위 | 키워드 | 출현 빈도 | 비율 | 특징 |
|------|--------|-----------|------|------|
| 1 | 보습력 | 38건 | 76.0% | 압도적 1위 |
| 2 | 재구매 | 25건 | 50.0% | 높은 재구매율 |
| 3 | 무향 | 22건 | 44.0% | 특징 |
| 4 | 건성피부 | 20건 | 40.0% | 타겟 |
| 5 | 무자극 | 18건 | 36.0% | 특징 |
| 6 | 흡수력 | 15건 | 30.0% | |
| 7 | 촉촉함 | 14건 | 28.0% | |
| 8 | 가성비 | 12건 | 24.0% | |
| 9 | 겨울 | 11건 | 22.0% | 계절 |


### 라로슈포제 시카플라스트 - 상위 15개 키워드
| 순위 | 키워드 | 출현 빈도 | 비율 | 특징 |
|------|--------|-----------|------|------|
| 1 | 진정 | 35건 | 77.8% | 압도적 1위 |
| 2 | 민감성 | 28건 | 62.2% | 타겟 |
| 3 | 트러블완화 | 22건 | 48.9% | 효과 |
| 4 | 재구매 | 18건 | 40.0% | |
| 5 | 끈적임 | 16건 | 35.6% | 부정 |
| 6 | 수분 | 14건 | 31.1% | |
| 7 | 밤타입 | 12건 | 26.7% | 제형 |
| 8 | 트러블 | 11건 | 24.4% | |
| 9 | 비쌈 | 10건 | 22.2% | 부정 |
| 10 | 붉음증 | 9건 | 20.0% | 고민 |


---

## 필수 준수사항

### ✅ 반드시 할 것
1. SQL 결과에 있는 데이터만 사용
2. 모든 주장에 구체적 수치 근거 제시
3. 리뷰 원문은 제공된 것만 정확히 인용
4. 키워드 언급 시 출현 빈도 함께 기재
5. 비교 시 명확한 수치 차이 명시

### ❌ 절대 금지
1. 데이터 없는 내용 추정/상상
2. "약", "정도", "쯤" 등 모호한 표현
3. 이모지 사용
4. 과장된 마케팅 문구
5. SQL 결과에 없는 리뷰 창작

---
⚠️ **최종 확인사항 - 답변 제출 전 반드시 체크:**

당신의 답변이 다음 기준을 모두 충족하는지 확인하세요:
□ 전체 길이가 1,000자 이상인가?
□ 예시의 데이터(키워드, 수치)를 사용했는가?
□ 리뷰 샘플을 답변마다 인용했는가? 
□ 모든 숫자에 출처가 명확한가?
**만약 위 항목 중 하나라도 No라면, 답변을 더 길고 상세하게 다시 작성하세요.**
"간단히 요약"하지 마세요. 마케팅 팀은 상세한 인사이트를 원합니다.
이제 답변을 작성하세요:
"""

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
            width=700,
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
            width=700,
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

        # 한글 폰트 경로 찾기 (크로스 플랫폼 지원)
        import platform

        font_path = None
        system = platform.system()

        if system == 'Windows':
            font_candidates = [
                'C:/Windows/Fonts/malgun.ttf',
                'C:/Windows/Fonts/malgunbd.ttf',
                'C:/Windows/Fonts/NanumGothic.ttf',
            ]
        elif system == 'Darwin':  # macOS
            font_candidates = [
                '/System/Library/Fonts/AppleGothic.ttf',
                '/Library/Fonts/AppleGothic.ttf',
                '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
            ]
        else:  # Linux
            font_candidates = [
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
                '/usr/share/fonts/nanum/NanumGothic.ttf',
            ]

        for font in font_candidates:
            if os.path.exists(font):
                font_path = font
                break

        # 원형 마스크
        x, y = np.ogrid[:600, :600]
        mask = (x - 300) ** 2 + (y - 300) ** 2 > 280 ** 2
        mask = 255 * mask.astype(int)

        # 워드클라우드 생성
        wordcloud = WordCloud(
            font_path=font_path,
            width=600,
            height=600,
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
        fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
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
