#//==============================================================================//#
"""
basic_metrics.py

 - 제품 수
 - 브랜드 수
 - 리뷰 수
 - 리뷰 길이
 - 평점

last_updated : 2025.10.16
"""
#//==============================================================================//#
import pandas as pd


def calculate_basic_metrics(df):
    """
    기본 통계 지표 계산
    
    Args:
        df: DataFrame
    
    Returns:
        dict: {
            'total_reviews': int,
            'unique_products': int,
            'avg_rating': float,
            'avg_review_length': float,
            'unique_brands': int
        }
    """
    metrics = {}
    
    # 총 리뷰 수
    metrics['total_reviews'] = len(df)
    
    # 제품 수
    metrics['unique_products'] = df['product_name'].nunique() if 'product_name' in df.columns else 0
    
    # 평균 평점
    if 'rating_numeric' in df.columns:
        metrics['avg_rating'] = df['rating_numeric'].mean()
    else:
        metrics['avg_rating'] = None
    
    # 평균 리뷰 길이
    if 'review_text' in df.columns:
        metrics['avg_review_length'] = df['review_text'].str.len().mean()
    else:
        metrics['avg_review_length'] = None
    
    # 브랜드 수
    metrics['unique_brands'] = df['brand'].nunique() if 'brand' in df.columns else 0
    
    return metrics