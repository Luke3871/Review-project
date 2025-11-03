#//==============================================================================//#
"""
report_generator.py
V1 Rule-based 분석 보고서 생성

- 통계 기반 규칙으로 인사이트 생성
- UI 버전(tab1_daiso_section.py - subtab7)에서 이식

last_updated: 2025.10.26
"""
#//==============================================================================//#

import sys
import os
import pandas as pd
from datetime import datetime

# dashboard 경로 추가
dashboard_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

from .utils import get_product_basic_info
from .keyword_analyzer import analyze_sentiment_keywords, extract_overall_keywords

#//==============================================================================//#
# 보고서 생성 메인 함수
#//==============================================================================//#

def generate_product_report(product_df, channel):
    """제품 분석 보고서 생성

    Args:
        product_df (DataFrame): 특정 제품의 리뷰 데이터
        channel (str): 채널명

    Returns:
        dict: 보고서 데이터
            - basic_info: 기본 정보
            - satisfaction: 만족도 분석
            - keywords: 키워드 분석
            - trend: 트렌드 요약
            - insights: 핵심 인사이트
    """
    # 1. 기본 정보
    basic_info = get_product_basic_info(product_df)

    # 2. 만족도 분석
    satisfaction = _analyze_satisfaction(product_df, basic_info)

    # 3. 키워드 분석
    keywords = _analyze_keywords(product_df, channel)

    # 4. 시간별 트렌드 요약
    trend = _analyze_trend(product_df)

    # 5. 핵심 인사이트 생성 (규칙 기반)
    insights = _generate_insights(basic_info, satisfaction, keywords, trend)

    return {
        'basic_info': basic_info,
        'satisfaction': satisfaction,
        'keywords': keywords,
        'trend': trend,
        'insights': insights,
        'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M")
    }

#//==============================================================================//#
# 만족도 분석
#//==============================================================================//#

def _analyze_satisfaction(product_df, basic_info):
    """고객 만족도 분석

    Args:
        product_df (DataFrame): 리뷰 데이터
        basic_info (dict): 기본 정보

    Returns:
        dict: 만족도 분석 결과
    """
    rating_counts = basic_info.get('rating_counts', {})

    if not rating_counts:
        return None

    # 평점별 개수
    total_reviews = sum(rating_counts.values())

    # 문자열 키를 숫자로 변환 (DB에서는 '5', '4' 형태로 올 수 있음)
    rating_5 = rating_counts.get('5', rating_counts.get(5, 0))
    rating_4 = rating_counts.get('4', rating_counts.get(4, 0))
    rating_3 = rating_counts.get('3', rating_counts.get(3, 0))
    rating_2 = rating_counts.get('2', rating_counts.get(2, 0))
    rating_1 = rating_counts.get('1', rating_counts.get(1, 0))

    # 긍정/부정 비율
    positive_count = rating_5 + rating_4
    negative_count = rating_1 + rating_2 + rating_3

    positive_ratio = (positive_count / total_reviews * 100) if total_reviews > 0 else 0
    negative_ratio = (negative_count / total_reviews * 100) if total_reviews > 0 else 0

    # 평균 평점
    total_rating = (rating_5 * 5 + rating_4 * 4 + rating_3 * 3 + rating_2 * 2 + rating_1 * 1)
    avg_rating = total_rating / total_reviews if total_reviews > 0 else 0

    return {
        'total_reviews': total_reviews,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'positive_ratio': round(positive_ratio, 1),
        'negative_ratio': round(negative_ratio, 1),
        'avg_rating': round(avg_rating, 2),
        'rating_distribution': {
            '5점': rating_5,
            '4점': rating_4,
            '3점': rating_3,
            '2점': rating_2,
            '1점': rating_1
        }
    }

#//==============================================================================//#
# 키워드 분석
#//==============================================================================//#

def _analyze_keywords(product_df, channel):
    """키워드 분석

    Args:
        product_df (DataFrame): 리뷰 데이터
        channel (str): 채널명

    Returns:
        dict: 키워드 분석 결과
    """
    # 1. 전체 키워드 추출
    overall_keywords = extract_overall_keywords(product_df, channel)

    # 2. 긍정/부정 키워드 추출
    positive_keywords, negative_keywords = analyze_sentiment_keywords(product_df, channel)

    result = {}

    # 전체 키워드 (TF-IDF 점수는 소수점 유지)
    if overall_keywords:
        result['overall_top10'] = [(kw, round(score, 4)) for kw, score in overall_keywords[:10]]

    # 긍정 키워드 (빈도수는 정수)
    if positive_keywords:
        result['positive_top5'] = [(kw, int(freq)) for kw, freq in positive_keywords[:5]]

    # 부정 키워드 (빈도수는 정수)
    if negative_keywords:
        result['negative_top5'] = [(kw, int(freq)) for kw, freq in negative_keywords[:5]]

    # 하나라도 있으면 반환
    return result if result else None

#//==============================================================================//#
# 트렌드 분석
#//==============================================================================//#

def _analyze_trend(product_df):
    """시간별 트렌드 요약

    Args:
        product_df (DataFrame): 리뷰 데이터

    Returns:
        dict: 트렌드 분석 결과
    """
    if 'review_date' not in product_df.columns:
        return None

    # 날짜 변환
    product_df = product_df.copy()
    product_df['review_date'] = pd.to_datetime(product_df['review_date'], errors='coerce')
    trend_data = product_df.dropna(subset=['review_date'])

    if len(trend_data) <= 1:
        return None

    # 월별 리뷰 수 집계
    trend_data['month'] = trend_data['review_date'].dt.to_period('M')
    monthly_counts = trend_data.groupby('month').size()

    if len(monthly_counts) <= 1:
        return None

    # 최고 리뷰 달
    peak_month = str(monthly_counts.idxmax())
    peak_count = int(monthly_counts.max())

    # 최근 리뷰 달
    recent_month = str(monthly_counts.index[-1])
    recent_count = int(monthly_counts.iloc[-1])

    # 최근 트렌드 (증가/감소)
    trend_direction = "증가" if monthly_counts.iloc[-1] > monthly_counts.iloc[-2] else "감소"

    return {
        'peak_month': peak_month,
        'peak_count': peak_count,
        'recent_month': recent_month,
        'recent_count': recent_count,
        'trend_direction': trend_direction
    }

#//==============================================================================//#
# 인사이트 생성 (규칙 기반)
#//==============================================================================//#

def _generate_insights(basic_info, satisfaction, keywords, trend):
    """규칙 기반 인사이트 생성

    Args:
        basic_info (dict): 기본 정보
        satisfaction (dict): 만족도 분석
        keywords (dict): 키워드 분석
        trend (dict): 트렌드 분석

    Returns:
        list: 인사이트 문자열 리스트
    """
    insights = []

    # 1. 만족도 기반 인사이트
    if satisfaction:
        positive_ratio = satisfaction['positive_ratio']

        if positive_ratio >= 80:
            insights.append(
                f"✅ **높은 고객 만족도**: 긍정 리뷰가 {positive_ratio}%로 매우 높은 만족도를 보임"
            )
        elif positive_ratio >= 60:
            insights.append(
                f"⚠️ **보통 고객 만족도**: 긍정 리뷰가 {positive_ratio}%로 개선 여지가 있음"
            )
        else:
            insights.append(
                f"❌ **낮은 고객 만족도**: 긍정 리뷰가 {positive_ratio}%로 품질 개선이 필요함"
            )

    # 2. 리뷰 수 기반 인사이트
    total_reviews = basic_info.get('total_reviews', 0)

    if total_reviews >= 500:
        insights.append(
            f"🔥 **높은 관심도**: 총 {total_reviews:,}개의 리뷰로 높은 구매율 및 관심도 확인"
        )
    elif total_reviews >= 100:
        insights.append(
            f"📊 **적당한 관심도**: 총 {total_reviews:,}개의 리뷰로 꾸준한 관심 확인"
        )
    else:
        insights.append(
            f"📉 **낮은 관심도**: 총 {total_reviews:,}개의 리뷰로 마케팅 강화 필요"
        )

    # 3. 키워드 기반 인사이트
    if keywords and keywords.get('positive_top5'):
        top_pos_keyword = keywords['positive_top5'][0][0]
        insights.append(
            f"💡 **핵심 강점**: '{top_pos_keyword}' 키워드가 가장 많이 언급되어 주요 장점으로 인식"
        )

    if keywords and keywords.get('negative_top5'):
        top_neg_keyword = keywords['negative_top5'][0][0]
        insights.append(
            f"🔧 **개선 포인트**: '{top_neg_keyword}' 키워드 개선을 통한 고객 만족도 향상 가능"
        )

    # 4. 랭킹 기반 인사이트
    rank = basic_info.get('rank', 'N/A')
    channel = basic_info.get('channel', '')

    if rank != 'N/A':
        try:
            rank_num = int(rank)
            if rank_num <= 10:
                insights.append(
                    f"🏆 **우수한 성과**: {channel} {rank_num}위로 카테고리 내 상위권 제품"
                )
            elif rank_num <= 50:
                insights.append(
                    f"📈 **중위권 성과**: {channel} {rank_num}위로 안정적인 성과"
                )
        except:
            pass

    # 5. 트렌드 기반 인사이트
    if trend:
        trend_direction = trend.get('trend_direction', '')
        if trend_direction == "증가":
            insights.append(
                f"📈 **상승 트렌드**: 최근 리뷰 수가 증가하며 인기 상승 중"
            )
        else:
            insights.append(
                f"📉 **하락 트렌드**: 최근 리뷰 수가 감소하며 관심도 하락"
            )

    return insights
