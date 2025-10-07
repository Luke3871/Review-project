#//==============================================================================//#
"""
planning_agent.py
LLM 기반 실행 계획 생성 (할루시네이션 방지)

last_updated : 2025.10.02
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from typing import Dict
from openai import OpenAI
import json

#//==============================================================================//#
# Planning Agent
#//==============================================================================//#

class PlanningAgent:
    """
    LLM 기반 실행 계획 생성 - 데이터 기반 답변 강제
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def create_plan(self, user_query: str) -> Dict:
        """
        사용자 질문을 분석하여 실행 계획 생성
        """
        
        system_prompt = """당신은 리뷰 분석 시스템의 실행 계획 수립자입니다.

절대 원칙:
1. 데이터에 없는 정보는 답변 불가능으로 판단
2. 추측이나 일반론으로 답변하지 말 것
3. 사용 가능한 데이터로 답변 불가능하면 명확히 거부
4. 모든 답변은 검색/조회된 실제 데이터에만 기반"""
        
        user_prompt = f"""
사용자 질문: "{user_query}"

# 사용 가능한 데이터 소스

## 1. RAG - 원본 리뷰 검색 (벡터 임베딩)
**retrieve_similar_reviews(query, filters, top_k)**

데이터:
- 10,000개 리뷰의 임베딩 벡터
- 메타데이터: product_name, brand, channel, rating (1-5점), review_date, review_text

용도:
- 고객의 실제 표현, 구체적 의견
- "어떤 느낌이야?", "무슨 특징이야?" 같은 질적 질문
- 탐색적 질문 ("인기 제품", "주목받는")

제약:
- 검색 결과가 없으면 답변 불가
- 리뷰 내용에 없는 정보는 답변 불가

예시:
{{"action": "retrieve_similar_reviews", "query": "촉촉 수분 보습", "filters": {{"brand": "토리든"}}, "top_k": 30}}

## 2. 집계 통계 테이블 (배치 분석 결과)

### brand_attribute_stats
**query_db("brand_attribute_stats", filters)**

데이터:
- 브랜드별 x 속성별 평가 (보습, 발림성, 지속력, 자극, 향)
- positive_count, negative_count, positive_ratio, sample_size, avg_rating

용도:
- "토리든 보습 평가 어때?" 같은 정량 질문
- 긍정/부정 비율, 평균 평점

제약:
- 속성은 5가지만 (보습, 발림성, 지속력, 자극, 향)
- 해당 브랜드 x 속성 조합이 없으면 답변 불가

### product_stats
**query_db("product_stats", filters)**

데이터:
- 제품별 통계: total_reviews, avg_rating, median_rating, rating_1~5

용도:
- 제품 전체 평가, 평점 분포

### product_keywords
**query_db("product_keywords", filters)**

데이터:
- 제품별 TF-IDF 키워드 30개
- top_keywords 배열

용도:
- "이 제품 주요 특징은?" 같은 키워드 질문

### monthly_trends
**query_db("monthly_trends", filters)**

데이터:
- 브랜드/채널별 월별 review_count, avg_rating
- year_month 형식 (2024-01)

용도:
- "최근 평가 좋아지고 있어?" 같은 트렌드 질문

제약:
- 월별 집계만 가능 (주별 불가)

## 3. 실시간 분석
**load_reviews(filters) → analyze(module)**

데이터:
- reviews 원본 테이블 직접 조회 및 분석

용도:
- 배치에 없는 조건 ("최근 7일", "최근 3개월")
- 특정 기간 필터링 필요시

제약:
- 느림 (20-30초)
- 복잡한 분석은 배치 결과 사용 권장

# 답변 가능 여부 판단

다음은 답변 **불가능**:
- "판매량", "매출", "인기도" → 데이터 없음
- "트렌드 예측", "미래 전망" → 예측 불가
- 데이터에 없는 브랜드/제품 질문
- "왜 인기 있어?" 같은 인과 관계 추론

다음은 답변 **가능**:
- "토리든 보습 평가 어때?" → brand_attribute_stats + RAG
- "최근 리뷰 좋아지고 있어?" → monthly_trends + RAG
- "올리브영에서 고객들이 자주 언급하는 특징?" → RAG
- "토리든 키워드는?" → product_keywords

# 도구 조합 전략

질문에 따라 **여러 도구 조합**:

단순 질문:
- RAG만: 실제 리뷰 감성 파악

복합 질문:
- RAG + 통계: 리뷰 의견 + 정량 지표
- 통계 + 키워드: 수치 + 특징

비교 질문:
- 각 대상별로 동일 도구 실행 후 비교

# 출력 형식

## 답변 가능한 경우:
{{
  "steps": [
    {{"action": "retrieve_similar_reviews", "query": "...", "filters": {{...}}, "top_k": 30}},
    {{"action": "query_db", "table": "brand_attribute_stats", "filters": {{...}}}}
  ],
  "answerable": true,
  "reasoning": "RAG로 실제 고객 의견 수집, 통계로 정량 검증",
  "data_sources": ["reviews", "brand_attribute_stats"]
}}

## 답변 불가능한 경우:
{{
  "steps": [{{"action": "reject", "reason": "구체적인 이유"}}],
  "answerable": false,
  "reasoning": "요청 정보가 데이터에 없음",
  "suggestion": "대신 이렇게 질문하세요: [구체적 예시]"
}}

# 중요 원칙
1. 불확실하면 reject
2. RAG 결과가 0개 예상되면 reject
3. 데이터 조합으로도 답변 불가능하면 reject
4. 일반론이나 추측으로 답변하지 말 것

JSON만 반환하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # 낮춤
                response_format={"type": "json_object"}
            )
            
            plan = json.loads(response.choices[0].message.content)
            return plan
            
        except Exception as e:
            return {
                "steps": [{"action": "error", "message": str(e)}],
                "answerable": False,
                "reasoning": "계획 생성 오류"
            }