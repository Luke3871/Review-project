"""
V5 LangGraph Agent 설정 파일

의도별 툴 매핑, 상수, LG 브랜드 리스트 등을 정의합니다.
"""

# ===== 의도별 툴 매핑 =====
# Router Node가 사용자 의도를 파악한 후, 이 매핑을 보고 어떤 툴을 사용할지 결정합니다.

INTENT_TO_TOOLS = {
    # 1. 속성 분석 (보습력, 발림성 등)
    "attribute_analysis": {
        "tools": ["AttributeTool"],
        "reason": "제품 속성(보습력, 발림성, 향, 가격 등)에 대한 만족도 분석"
    },

    # 2. 감성 분석 (긍정/부정)
    "sentiment_analysis": {
        "tools": ["SentimentTool"],
        "reason": "리뷰의 전반적인 감성(긍정/부정) 분석 및 핵심 표현 추출"
    },

    # 3. 제품 비교 (A vs B)
    "comparison": {
        "tools": ["ProductComparisonTool"],
        "reason": "두 제품 간 비교 분석 (속성, 감성, 가격 등)"
    },

    # 4. 키워드 추출
    "keyword_extraction": {
        "tools": ["KeywordTool"],
        "reason": "리뷰에서 자주 언급되는 주요 키워드 추출 및 빈도 분석"
    },

    # 5. 기획/프로모션 분석
    "promotion_analysis": {
        "tools": ["PromotionMentionTool", "SentimentTool"],
        "reason": "기획전/프로모션 언급 여부 및 반응(긍정/부정) 분석"
    },

    # 6. 제품 포지셔닝
    "positioning_analysis": {
        "tools": ["PositioningTool"],
        "reason": "제품의 차별점 및 시장 포지셔닝 분석 (경쟁 우위 요소)"
    },

    # 7. 전체 리뷰 종합 분석 (가장 복잡, 여러 툴 조합)
    "full_review": {
        "tools": ["AttributeTool", "SentimentTool", "ProsTool", "ConsTool", "PurchaseMotivationTool"],
        "reason": "전체 리뷰 종합 분석 (속성, 감성, 장점, 단점, 구매동기)"
    },

    # 8. 키워드-감성 연계 분석
    "keyword_sentiment": {
        "tools": ["KeywordSentimentTool"],
        "reason": "특정 키워드(예: 보습)에 대한 긍정/부정 감성 연계 분석"
    },

    # 9. 장점 분석
    "pros_analysis": {
        "tools": ["ProsTool"],
        "reason": "제품의 장점 및 긍정적 특징 분석"
    },

    # 10. 단점 분석
    "cons_analysis": {
        "tools": ["ConsTool"],
        "reason": "제품의 단점 및 부정적 요소 분석"
    },

    # 11. 불만사항 분석
    "complaint_analysis": {
        "tools": ["ComplaintTool"],
        "reason": "고객 불만사항 및 개선 필요 사항 분석"
    },

    # 12. 구매동기 분석
    "motivation_analysis": {
        "tools": ["PurchaseMotivationTool"],
        "reason": "구매 동기(재구매, 추천, 광고 등) 분석"
    },

    # 13. 타제품 비교 언급 분석
    "comparison_mention": {
        "tools": ["ComparisonMentionTool"],
        "reason": "경쟁사 제품 언급 여부 및 비교 내용 분석"
    }
}


# ===== 상수 =====

# 통계적 신뢰도를 위한 최소 리뷰 수
# 1개 미만이면 Fallback 경고 발동
MIN_REVIEW_COUNT = 1

# 데이터베이스 테이블명
PREPROCESSED_TABLE = "preprocessed_reviews"

# 채널명 한글 → 영문 매핑 (DB에 영문으로 저장되어 있음)
CHANNEL_MAPPING = {
    "올리브영": "OliveYoung",
    "쿠팡": "Coupang",
    "다이소": "Daiso"
}


# ===== LG 생활건강 브랜드 리스트 =====
# 마케터가 "우리 제품" 분석 시 필터링에 사용
# (현재는 사용 안 하지만, 나중에 LG 데이터 제공 시 활용)

LG_BRANDS = [
    "빌리프",
    "숨37도",
    "후",
    "이자녹스",
    "CNP",
    "VDL",
    "숨",
    "THE HISTORY OF 후",
    "비욘드",
    "오휘"
]


# ===== LLM 프롬프트 템플릿 (나중에 prompts.py로 분리 가능) =====

# Parser Node에서 사용할 프롬프트
PARSER_PROMPT_TEMPLATE = """
당신은 화장품 리뷰 분석 시스템의 질문 파서입니다.
사용자 질문을 분석해서 다음 정보를 JSON으로 추출하세요:

- brands: 브랜드명 리스트 (예: ["빌리프", "VT"])
- products: 제품명 리스트 (예: ["모이스춰라이징밤", "시카크림"])
- channels: 채널명 리스트 (예: ["올리브영", "쿠팡"])
- intent: 질문 의도 (아래 중 하나)
  * attribute_analysis: 속성 분석 (보습력, 발림성 등)
  * sentiment_analysis: 감성 분석
  * comparison: 제품 비교
  * keyword_extraction: 키워드 추출
  * promotion_analysis: 기획/프로모션 분석
  * positioning_analysis: 포지셔닝 분석
  * full_review: 전체 리뷰 종합 분석
  * keyword_sentiment: 키워드-감성 연계
  * pros_analysis: 장점 분석
  * cons_analysis: 단점 분석
  * complaint_analysis: 불만사항 분석
  * motivation_analysis: 구매동기 분석
  * comparison_mention: 타제품 언급 분석

**예시:**

질문: "빌리프 모이스춰라이징밤 속성 분석해줘"
→ {{"brands": ["빌리프"], "products": ["모이스춰라이징밤"], "channels": [], "intent": "attribute_analysis"}}

질문: "VT 시카크림이랑 라로슈포제 시카플라스트 비교"
→ {{"brands": ["VT", "라로슈포제"], "products": ["시카크림", "시카플라스트"], "channels": [], "intent": "comparison"}}

질문: "올리브영 채널에서 기획전 반응"
→ {{"brands": [], "products": [], "channels": ["올리브영"], "intent": "promotion_analysis"}}

**사용자 질문:**
{query}

**JSON 결과만 반환하세요 (다른 설명 없이):**
"""

# Synthesizer Node에서 사용할 프롬프트
SYNTHESIZER_PROMPT_TEMPLATE = """
당신은 화장품 리뷰 분석 시스템의 결과 종합 전문가입니다.
사용자 질문과 분석 도구 실행 결과를 바탕으로 자연스럽고 통찰력 있는 응답을 생성하세요.

**사용자 질문:**
{user_query}

**분석 필터:**
- 브랜드: {brands}
- 제품: {products}
- 채널: {channels}

**분석 도구 실행 결과:**
{tool_results}

**작성 가이드라인:**
1. 사용자 질문에 직접적으로 답변하세요
2. 분석 결과의 핵심 인사이트를 먼저 제시하세요
3. 구체적인 수치와 데이터를 활용하세요
4. 마케팅 실무에 도움이 되는 통찰을 제공하세요
5. 긍정적/부정적 측면을 균형있게 전달하세요
6. 마크다운 형식으로 가독성 높게 작성하세요

**주의사항:**
- 데이터에 없는 내용을 추정하거나 만들지 마세요
- 분석 결과를 과장하지 마세요
- 전문적이면서도 이해하기 쉽게 작성하세요

**응답을 작성하세요:**
"""
