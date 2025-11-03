#//==============================================================================//#
"""
planning_agent.py
LLM 기반 실행 계획 생성

last_updated : 2025.10.16
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
    LLM 기반 실행 계획 생성
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def create_plan(self, user_query: str) -> Dict:
        """
        사용자 질문을 분석하여 실행 계획 생성
        """
        
        system_prompt = """당신은 리뷰 분석 시스템의 실행 계획 수립자입니다.

# 사용 가능한 데이터

## reviews 테이블 (PostgreSQL + pgvector)
- 총 51만개 화장품 리뷰
- BGE-M3 임베딩 완료
- 필드:
  * product_name (제품명)
  * brand (브랜드)
  * channel (채널: OliveYoung, Coupang, Daiso)
  * category (카테고리: skincare, makeup 등)
  * rating (평점: 1-5)
  * review_date (리뷰 날짜)
  * review_text (리뷰 본문)
  * reviewer_skin_features (피부 타입: 복합성, 지성 등)
  * embedding (벡터)

# 사용 가능한 작업

## 1. retrieve_similar_reviews
의미 기반 벡터 검색
- query: 검색할 의미 ("보습력 좋은", "촉촉한")
- filters: {brand, channel, category, min_rating, date_from, date_to, skin_features}
- top_k: 가져올 개수 (기본 30)

## 2. filter_reviews  
조건 기반 필터링
- filters: {brand, channel, category, min_rating, date_from, date_to}

## 3. calculate_stats
통계 계산 (filter_reviews 후 실행)
- metric: 계산할 지표
- group_by: 그룹화 기준 (brand, channel, category)

# 답변 가능 판단

**가능한 질문:**
- "VT 보습 어때?" → retrieve_similar_reviews
- "올리브영 평점 높은 제품은?" → filter_reviews + calculate_stats
- "최근 3개월 토리든 평가?" → retrieve_similar_reviews (date_from 필터)
- "복합성 피부 추천 제품" → filter_reviews (skin_features)

**불가능한 질문:**
- 판매량, 매출, 인기도 (데이터 없음)
- 다른 사이트 정보
- 예측, 추론

# 출력 형식

답변 가능:
{
  "steps": [
    {"action": "retrieve_similar_reviews", "query": "...", "filters": {...}, "top_k": 30}
  ],
  "answerable": true,
  "reasoning": "..."
}

답변 불가:
{
  "steps": [{"action": "reject", "reason": "..."}],
  "answerable": false,
  "suggestion": "..."
}
"""
        
        user_prompt = f"""
사용자 질문: "{user_query}"

위 질문을 분석하여 실행 계획을 JSON으로 반환하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
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