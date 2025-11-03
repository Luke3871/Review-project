#//==============================================================================//#
"""
report_generator.py
V2 LLM-based 보고서 생성

- GPT를 활용한 비즈니스 인사이트 자동 생성
- ui/daiso.py의 AI Insights 기능 이식

last_updated: 2025.10.26
"""
#//==============================================================================//#

import pandas as pd
from datetime import datetime, timedelta

#//==============================================================================//#
# LLM 보고서 생성
#//==============================================================================//#

def generate_llm_report(product_df, channel, api_key):
    """GPT를 활용한 제품 분석 보고서 생성

    Args:
        product_df (DataFrame): 제품 리뷰 데이터
        channel (str): 채널명
        api_key (str): OpenAI API 키

    Returns:
        dict: 보고서 데이터
            - summary: 데이터 요약
            - insights: GPT 생성 인사이트
            - generated_at: 생성 시각
    """
    if product_df.empty:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # 1. 데이터 요약 생성
        summary = _create_data_summary(product_df)

        # 2. 제품 정보 추출
        product_name = product_df['product_name'].iloc[0] if 'product_name' in product_df.columns else "제품"
        brand = product_df['brand'].iloc[0] if 'brand' in product_df.columns else "브랜드"
        category = product_df['category'].iloc[0] if 'category' in product_df.columns else "카테고리"

        # 3. GPT 프롬프트 생성
        prompt = f"""
다음은 {channel} 채널의 '{brand} {product_name}' 제품 리뷰 데이터입니다.

{summary}

위 데이터를 바탕으로 다음 관점에서 비즈니스 인사이트를 제공해주세요:

1. **제품 강점 분석**: 리뷰 데이터에서 나타나는 이 제품의 핵심 강점과 차별점
2. **고객 만족도 패턴**: 평점 분포와 리뷰 내용을 통해 본 고객 만족/불만족 요인
3. **개선 기회**: 부정적 피드백이나 개선이 필요한 영역
4. **시장 포지셔닝**: 이 제품이 시장에서 차지하는 위치와 타겟 고객층

마크다운 형식으로 구조화하여 작성하고, 구체적인 수치를 인용하며 실용적인 비즈니스 제안을 포함해주세요.
답변은 한국어로 작성해주세요.
"""

        # 4. GPT API 호출
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 화장품 리뷰 데이터 분석 전문가입니다. 제공된 리뷰 데이터를 분석하여 실용적인 비즈니스 인사이트를 제공합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.7
        )

        insights = response.choices[0].message.content

        return {
            'summary': summary,
            'insights': insights,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'product_name': product_name,
            'brand': brand,
            'channel': channel
        }

    except Exception as e:
        print(f"LLM 보고서 생성 중 오류: {e}")
        return {
            'summary': None,
            'insights': None,
            'error': str(e),
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
        }

#//==============================================================================//#
# 데이터 요약 생성
#//==============================================================================//#

def _create_data_summary(df):
    """데이터 요약 생성

    Args:
        df (DataFrame): 리뷰 데이터

    Returns:
        str: 요약 텍스트
    """
    summary_parts = []

    # 1. 기본 통계
    total_reviews = len(df)
    summary_parts.append(f"- 총 리뷰 수: {total_reviews:,}개")

    # 2. 평점 정보
    if 'rating' in df.columns:
        df_copy = df.copy()
        df_copy['rating_numeric'] = pd.to_numeric(df_copy['rating'], errors='coerce')

        if not df_copy['rating_numeric'].isna().all():
            avg_rating = df_copy['rating_numeric'].mean()
            rating_dist = df_copy['rating_numeric'].value_counts().sort_index()

            summary_parts.append(f"- 평균 평점: {avg_rating:.2f}점")

            # 평점 분포
            rating_dist_dict = {}
            for i in range(1, 6):
                count = rating_dist.get(float(i), 0)
                rating_dist_dict[f"{i}점"] = int(count)

            summary_parts.append(f"- 평점 분포: {rating_dist_dict}")

            # 긍정/부정 비율
            positive_count = len(df_copy[df_copy['rating_numeric'] >= 4])
            negative_count = len(df_copy[df_copy['rating_numeric'] <= 3])
            positive_ratio = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
            negative_ratio = (negative_count / total_reviews * 100) if total_reviews > 0 else 0

            summary_parts.append(f"- 긍정 리뷰(4점 이상): {positive_count}개 ({positive_ratio:.1f}%)")
            summary_parts.append(f"- 부정 리뷰(3점 이하): {negative_count}개 ({negative_ratio:.1f}%)")

    # 3. 리뷰 길이 정보
    if 'review_text' in df.columns:
        text_lengths = df['review_text'].fillna('').str.len()
        if len(text_lengths) > 0:
            avg_length = text_lengths.mean()
            max_length = text_lengths.max()
            min_length = text_lengths.min()

            summary_parts.append(f"- 평균 리뷰 길이: {avg_length:.0f}자")
            summary_parts.append(f"- 최대/최소 리뷰 길이: {max_length:.0f}자 / {min_length:.0f}자")

            # 긴 리뷰 비율 (100자 이상)
            long_reviews = len(text_lengths[text_lengths > 100])
            long_ratio = (long_reviews / total_reviews * 100) if total_reviews > 0 else 0
            summary_parts.append(f"- 긴 리뷰(100자 이상): {long_reviews}개 ({long_ratio:.1f}%)")

    # 4. 시간 트렌드
    if 'review_date' in df.columns:
        df_copy = df.copy()
        df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
        valid_dates = df_copy.dropna(subset=['review_date'])

        if not valid_dates.empty:
            # 데이터 기간
            date_range_days = (valid_dates['review_date'].max() - valid_dates['review_date'].min()).days
            summary_parts.append(f"- 데이터 수집 기간: {date_range_days}일")

            # 최근 6개월 월별 트렌드
            monthly_trend = valid_dates.groupby(valid_dates['review_date'].dt.to_period('M')).size().tail(6)
            if not monthly_trend.empty:
                trend_dict = {str(month): int(count) for month, count in monthly_trend.items()}
                summary_parts.append(f"- 최근 6개월 월별 리뷰 수: {trend_dict}")

            # 최근 1개월 활동
            recent_month = valid_dates[valid_dates['review_date'] >= (datetime.now() - timedelta(days=30))]
            if not recent_month.empty:
                recent_ratio = len(recent_month) / len(valid_dates) * 100
                summary_parts.append(f"- 최근 1개월 리뷰 비율: {recent_ratio:.1f}%")

    # 5. 주요 키워드 (간단히)
    if 'review_text' in df.columns:
        # 자주 언급되는 단어들 (매우 간단한 버전)
        all_text = ' '.join(df['review_text'].fillna('').astype(str))

        # 간단한 키워드 추출 (자주 나오는 단어)
        common_words = ['좋아요', '추천', '만족', '보습', '촉촉', '가성비', '향', '발림', '끈적']
        mentioned_words = [word for word in common_words if word in all_text]

        if mentioned_words:
            summary_parts.append(f"- 자주 언급된 키워드: {', '.join(mentioned_words[:5])}")

    return "\n".join(summary_parts)
