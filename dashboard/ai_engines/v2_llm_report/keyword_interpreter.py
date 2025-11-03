#//==============================================================================//#
"""
keyword_interpreter.py
V2-B 키워드 해석 분석

- 추출된 키워드를 GPT가 해석
- ui/review_analysis.py에서 이식

last_updated: 2025.10.26
"""
#//==============================================================================//#

import pandas as pd
from datetime import datetime

#//==============================================================================//#
# 키워드 해석 분석
#//==============================================================================//#

def generate_keyword_interpretation(product_df, keywords, channel, api_key):
    """키워드 분석 결과에 대한 AI 해석 생성

    Args:
        product_df (DataFrame): 제품 리뷰 데이터
        keywords (list): [(키워드, 점수), ...] 형태의 키워드 리스트
        channel (str): 채널명
        api_key (str): OpenAI API 키

    Returns:
        dict: 해석 결과
            - interpretation: GPT 생성 해석
            - keywords_summary: 키워드 요약
            - generated_at: 생성 시각
    """
    if not keywords or product_df.empty:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # 1. 키워드 요약
        top_keywords = keywords[:20]  # 상위 20개
        keyword_list = [f"{word}: {score:.3f}" for word, score in top_keywords]

        # 2. 기본 통계
        total_reviews = len(product_df)

        # 평점 변환
        product_df_copy = product_df.copy()
        product_df_copy['rating_numeric'] = pd.to_numeric(product_df_copy['rating'], errors='coerce')

        avg_rating = product_df_copy['rating_numeric'].mean() if 'rating_numeric' in product_df_copy.columns else 0
        positive_count = len(product_df_copy[product_df_copy['rating_numeric'] >= 4]) if 'rating_numeric' in product_df_copy.columns else 0
        negative_count = len(product_df_copy[product_df_copy['rating_numeric'] <= 3]) if 'rating_numeric' in product_df_copy.columns else 0

        positive_ratio = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
        negative_ratio = (negative_count / total_reviews * 100) if total_reviews > 0 else 0

        # 3. 제품 정보
        product_name = product_df['product_name'].iloc[0] if 'product_name' in product_df.columns else "제품"
        brand = product_df['brand'].iloc[0] if 'brand' in product_df.columns else "브랜드"

        # 4. GPT 프롬프트
        prompt = f"""
다음은 '{brand} {product_name}' 제품의 리뷰 키워드 분석 결과입니다:

**기본 통계:**
- 채널: {channel}
- 총 리뷰 수: {total_reviews:,}개
- 평균 평점: {avg_rating:.2f}점 (5점 만점)
- 긍정 리뷰 (4-5점): {positive_count:,}개 ({positive_ratio:.1f}%)
- 부정 리뷰 (1-3점): {negative_count:,}개 ({negative_ratio:.1f}%)

**상위 20개 키워드 (중요도 순):**
{chr(10).join(keyword_list)}

위 키워드 분석 결과를 해석하고 다음 관점에서 조언해주세요:

1. **키워드 패턴 분석**
   - 어떤 키워드들이 주로 등장하는지
   - 긍정적/부정적 키워드의 특징
   - 고객들이 중요하게 생각하는 요소들

2. **제품 개선 방향**
   - 키워드를 통해 파악된 개선점
   - 고객 불만사항과 해결 방안
   - 강화해야 할 긍정 요소들

3. **마케팅 전략 제안**
   - 키워드 기반 마케팅 포인트
   - 고객 커뮤니케이션 방향
   - 경쟁 우위 확보 방안

4. **우선순위 액션 아이템**
   - 즉시 실행 가능한 개선사항
   - 중장기 전략 과제
   - 성과 측정 방법

구체적이고 실용적인 조언을 마크다운 형식으로 작성해주세요.
답변은 한국어로 작성해주세요.
"""

        # 5. GPT API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 텍스트 마이닝 전문가이자 비즈니스 컨설턴트입니다. 키워드 분석 결과를 해석하여 구체적이고 실행 가능한 비즈니스 조언을 제공합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )

        interpretation = response.choices[0].message.content

        return {
            'interpretation': interpretation,
            'keywords_summary': keyword_list,
            'product_name': product_name,
            'brand': brand,
            'channel': channel,
            'total_reviews': total_reviews,
            'avg_rating': avg_rating,
            'positive_ratio': positive_ratio,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    except Exception as e:
        print(f"키워드 해석 생성 중 오류: {e}")
        return {
            'interpretation': None,
            'error': str(e),
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
