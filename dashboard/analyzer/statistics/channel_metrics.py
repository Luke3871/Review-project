#//==============================================================================//#
"""
channel_metrics.py
채널 레벨 전용 분석 지표

last_updated : 2025.10.25
"""
#//==============================================================================//#

import pandas as pd
from datetime import datetime, timedelta


def get_product_ranking(df, top_n=20):
    """
    제품별 랭킹 (DB의 ranking 컬럼 사용)
    
    Args:
        df: DataFrame
        top_n: 상위 N개
    
    Returns:
        DataFrame: 순위, 제품명, 브랜드, 리뷰 수, 평균 평점
    """
    if 'ranking' not in df.columns:
        return pd.DataFrame()
    
    # ranking 컬럼이 있는 데이터만
    ranked_df = df[df['ranking'].notna()].copy()
    
    if ranked_df.empty:
        return pd.DataFrame()
    
    # ranking을 숫자로 변환
    ranked_df['ranking'] = pd.to_numeric(ranked_df['ranking'], errors='coerce')
    ranked_df = ranked_df[ranked_df['ranking'].notna()]
    
    # 제품별 집계
    ranking = ranked_df.groupby(['product_name', 'brand']).agg({
        'review_id': 'count',
        'rating_numeric': 'mean',
        'ranking': 'min'
    }).reset_index()
    
    ranking.columns = ['제품명', '브랜드', '리뷰 수', '평균 평점', '순위']
    ranking['평균 평점'] = ranking['평균 평점'].round(2)
    ranking['순위'] = ranking['순위'].astype(int)
    
    # ranking 기준 정렬
    ranking = ranking.sort_values('순위').head(top_n)
    
    return ranking[['순위', '제품명', '브랜드', '리뷰 수', '평균 평점']]


def get_category_distribution(df):
    """
    카테고리별 분포
    
    Args:
        df: DataFrame
    
    Returns:
        DataFrame: 카테고리, 리뷰 수, 비율
    """
    if 'category' not in df.columns:
        return pd.DataFrame()
    
    dist = df['category'].value_counts().reset_index()
    dist.columns = ['카테고리', '리뷰 수']
    dist['비율(%)'] = (dist['리뷰 수'] / dist['리뷰 수'].sum() * 100).round(1)
    
    return dist


def get_channel_summary(df):
    """
    채널 요약 통계
    
    Args:
        df: DataFrame
    
    Returns:
        dict: {
            'total_reviews': int,
            'total_brands': int,
            'total_products': int,
            'avg_rating': float,
            'date_range': str
        }
    """
    summary = {}
    
    summary['total_reviews'] = len(df)
    summary['total_brands'] = df['brand'].nunique() if 'brand' in df.columns else 0
    summary['total_products'] = df['product_name'].nunique() if 'product_name' in df.columns else 0
    summary['avg_rating'] = df['rating_numeric'].mean() if 'rating_numeric' in df.columns else None
    
    if 'review_date' in df.columns:
        df_copy = df.copy()
        df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
        valid_dates = df_copy['review_date'].dropna()
        if not valid_dates.empty:
            summary['date_range'] = f"{valid_dates.min().date()} ~ {valid_dates.max().date()}"
        else:
            summary['date_range'] = "N/A"
    else:
        summary['date_range'] = "N/A"
    
    return summary
