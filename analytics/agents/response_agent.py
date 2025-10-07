#//==============================================================================//#
"""
response_agent.py
LLM 기반 답변 생성 (데이터 기반만 답변)

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
import pandas as pd

#//==============================================================================//#
# Response Agent
#//==============================================================================//#

class ResponseAgent:
    """
    분석 결과를 자연어 보고서로 변환 (데이터만 사용)
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
            
            response += """
## 답변 가능한 질문 예시

**브랜드/속성 평가**
- "토리든 보습 평가 어때?"
- "라운드랩 발림성은?"
- "VDL 지속력 괜찮아?"

**채널/제품 정보**
- "올리브영 토리든 평점은?"
- "쿠팡에서 네일라꾸 리뷰 많아?"

**비교 분석**
- "토리든 vs 라운드랩 보습 비교"
- "올리브영 vs 쿠팡 평점 차이"

**트렌드**
- "최근 토리든 평가 좋아지고 있어?"
- "올리브영 리뷰 수 늘고 있어?"
"""
            return response
        
        if results.get('error'):
            return f"분석 중 오류가 발생했습니다: {results['error']}"
        
        # 데이터 검증
        has_data = self._validate_data(results)
        if not has_data:
            return """## 데이터 없음

검색 결과가 없습니다. 다음을 확인해주세요:
- 브랜드명/제품명이 정확한가요?
- 해당 채널에 리뷰가 있나요?
- 다른 표현으로 다시 질문해보세요.
"""
        
        system_prompt = """당신은 데이터 분석 전문가입니다.

철저한 원칙:
1. 제공된 데이터에만 기반하여 답변
2. 데이터에 없는 정보는 절대 언급 금지
3. 추측, 가정, 일반론 금지
4. 불확실한 내용은 "확인 불가" 명시
5. 모든 주장에 구체적 근거 제시

답변 스타일:
- 실제 리뷰 인용 우선
- 수치로 뒷받침
- 명확하고 구체적으로"""
        
        user_prompt = f"""
질문: "{user_query}"

# 분석 데이터

{self._format_all_data(results)}

# 답변 작성 지침

## 필수 원칙
1. **위 데이터에만 기반**: 데이터에 없는 내용은 절대 쓰지 마세요
2. **실제 인용 우선**: 리뷰가 있으면 구체적으로 인용하세요
3. **수치 정확히**: 계산 없이 데이터에 있는 그대로만
4. **불확실하면 명시**: "현재 데이터로는 확인 어려움" 표현

## 답변 구조

### 1. 핵심 요약 (3-5문장)
- 질문에 대한 직접 답변
- 가장 중요한 수치 1-2개
- 긍정/부정 판단이 명확하면 제시

### 2. 데이터 분석

#### 실제 고객 리뷰 (검색된 리뷰가 있는 경우)
- 구체적으로 인용: "한 고객은 '...'라고 평가"
- 여러 리뷰의 공통 패턴
- 긍정/부정 구분

#### 정량 지표 (통계가 있는 경우)
- 긍정 비율, 리뷰 수, 평균 평점
- 비교 가능하면 상대적 위치

#### 키워드 (있는 경우)
- 자주 언급되는 특징

### 3. 인사이트
- 데이터가 시사하는 바
- 실무 활용 방안 (데이터 기반만)

## 중요: 금지 사항
- 데이터에 없는 수치 생성 금지
- "아마도", "~일 것 같다" 같은 추측 금지
- 일반적인 화장품 지식 언급 금지
- 리뷰에 없는 내용 추론 금지

## 길이
- 데이터 적으면: 간단히 (5-8문장)
- 데이터 많으면: 상세히 (15-20문장)

마크다운으로 구조화하세요.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # 낮춤
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"답변 생성 오류: {e}"
    
    def _validate_data(self, results: Dict) -> bool:
        """
        실제 데이터가 있는지 검증
        """
        
        # retrieved_reviews 확인
        if results.get('retrieved_reviews') is not None:
            if not results['retrieved_reviews'].empty:
                return True
        
        # data 확인
        if results.get('data') is not None:
            if isinstance(results['data'], pd.DataFrame):
                if not results['data'].empty:
                    return True
            elif isinstance(results['data'], dict):
                for df in results['data'].values():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        return True
        
        # analysis 확인
        if results.get('analysis'):
            analysis = results['analysis']
            if isinstance(analysis, dict):
                if analysis.get('brand_attributes') and len(analysis['brand_attributes']) > 0:
                    return True
        
        return False
    
    def _format_all_data(self, results: Dict) -> str:
        """
        모든 데이터를 LLM이 읽기 쉽게 포맷팅
        """
        
        lines = []
        
        # 1. RAG 검색 결과
        if results.get('retrieved_reviews') is not None and not results['retrieved_reviews'].empty:
            reviews_df = results['retrieved_reviews']
            lines.append(f"## 검색된 리뷰 ({len(reviews_df)}개)")
            lines.append("")
            
            # 상위 15개 리뷰 상세히
            for idx, row in reviews_df.head(15).iterrows():
                lines.append(f"### 리뷰 {idx+1}")
                lines.append(f"- 제품: {row['product_name']}")
                lines.append(f"- 브랜드: {row['brand']} | 채널: {row['channel']}")
                lines.append(f"- 평점: {row['rating']}점")
                lines.append(f"- 유사도: {row.get('similarity', 0):.3f}")
                lines.append(f"- 내용: {row['review_text']}")
                lines.append("")
        
        # 2. DB 조회 결과
        if results.get('data') is not None:
            data = results['data']
            
            if isinstance(data, dict):
                # 테이블별 결과
                for table_name, df in data.items():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        lines.append(f"## {table_name} 조회 결과 ({len(df)}건)")
                        lines.append("")
                        lines.append(df.head(10).to_string())
                        lines.append("")
            
            elif isinstance(data, pd.DataFrame) and not data.empty:
                lines.append(f"## 조회 결과 ({len(data)}건)")
                lines.append("")
                lines.append(data.head(10).to_string())
                lines.append("")
        
        # 3. 분석 결과
        if results.get('analysis'):
            analysis = results['analysis']
            
            if 'brand_attributes' in analysis:
                attrs = analysis['brand_attributes']
                lines.append(f"## 브랜드 속성 분석 ({len(attrs)}개)")
                lines.append("")
                
                for attr in attrs:
                    lines.append(f"### {attr['brand']} - {attr['attribute']}")
                    lines.append(f"- 분석 리뷰: {attr['sample_size']:,}개")
                    lines.append(f"- 긍정: {attr['positive_ratio']:.1%} ({attr['positive_count']:,}개)")
                    lines.append(f"- 부정: {attr['negative_ratio']:.1%} ({attr['negative_count']:,}개)")
                    lines.append(f"- 평균 평점: {attr['avg_rating']:.2f}점")
                    lines.append("")
        
        return "\n".join(lines) if lines else "데이터 없음"