#//==============================================================================//#
"""
response_agent.py
LLM 기반 답변 생성

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
import pandas as pd

#//==============================================================================//#
# Response Agent
#//==============================================================================//#

class ResponseAgent:
    """
    분석 결과를 자연어로 변환
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, results: Dict, user_query: str) -> str:
        """
        분석 결과를 답변으로 변환
        """
        
        # 에러 처리
        if results.get('error') == 'not_answerable':
            plan = results.get('plan', {})
            reason = plan.get('steps', [{}])[0].get('reason', '데이터 부족')
            suggestion = plan.get('suggestion', '')
            
            response = f"""## 답변 불가

죄송합니다. 현재 데이터로는 이 질문에 답변할 수 없습니다.

**이유**: {reason}
"""
            if suggestion:
                response += f"\n{suggestion}\n"
            
            return response
        
        if results.get('error'):
            return f"분석 중 오류가 발생했습니다: {results['error']}"
        
        # 데이터 검증
        has_data = self._validate_data(results)
        if not has_data:
            return """## 데이터 없음

검색 결과가 없습니다. 다음을 확인해주세요:
- 브랜드명/제품명이 정확한가요?
- 해당 조건에 맞는 리뷰가 있나요?
"""
        
        system_prompt = """당신은 데이터 분석 전문가입니다.

원칙:
1. 제공된 데이터에만 기반
2. 추측 금지
3. 실제 리뷰 인용
4. 수치로 뒷받침

답변 구조:
1. 핵심 요약 (3-5문장)
2. 구체적 데이터 분석
3. 인사이트
"""
        
        user_prompt = f"""
질문: "{user_query}"

# 분석 데이터

{self._format_data(results)}

# 답변 작성

위 데이터만 사용하여 답변하세요. 마크다운 형식으로 작성하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"답변 생성 오류: {e}"
    
    def _validate_data(self, results: Dict) -> bool:
        """
        데이터 존재 여부 확인
        """
        
        if results.get('reviews') is not None:
            if isinstance(results['reviews'], pd.DataFrame):
                if not results['reviews'].empty:
                    return True
        
        if results.get('stats'):
            if isinstance(results['stats'], dict):
                if results['stats'].get('총_리뷰수', 0) > 0:
                    return True
        
        return False
    
    def _format_data(self, results: Dict) -> str:
        """
        데이터 포맷팅
        """
        
        lines = []
        
        # 리뷰 데이터
        if results.get('reviews') is not None and not results['reviews'].empty:
            reviews_df = results['reviews']
            lines.append(f"## 검색된 리뷰 ({len(reviews_df)}개)\n")
            
            for idx, row in reviews_df.head(10).iterrows():
                lines.append(f"### 리뷰 {idx+1}")
                lines.append(f"- 제품: {row['product_name']}")
                lines.append(f"- 브랜드: {row['brand']} | 채널: {row['channel']}")
                lines.append(f"- 평점: {row['rating']}점")
                if 'similarity' in row:
                    lines.append(f"- 유사도: {row['similarity']:.3f}")
                lines.append(f"- 내용: {row['review_text'][:200]}...")
                lines.append("")
        
        # 통계 데이터
        if results.get('stats'):
            stats = results['stats']
            lines.append("## 통계 정보\n")
            
            for key, value in stats.items():
                if isinstance(value, dict):
                    lines.append(f"### {key}")
                    for k, v in value.items():
                        lines.append(f"- {k}: {v}")
                else:
                    lines.append(f"- {key}: {value}")
            lines.append("")
        
        return "\n".join(lines) if lines else "데이터 없음"