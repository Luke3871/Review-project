#//==============================================================================//#
"""
brand_metrics.py

 - 브랜드별 리뷰수
 - 브랜드별 평점


last_updated : 2025.10.16
"""
#//==============================================================================//#
import pandas as pd


def calculate_brand_stats(df, top_n=15, min_reviews=5):
    """
    브랜드별 통계 계산
    
    Args:
        df: DataFrame
        top_n: 상위 N개
        min_reviews: 최소 리뷰 수 (평점 계산시)
    
    Returns:
        dict: {
            'review_counts': Series (브랜드별 리뷰 수),
            'avg_ratings': DataFrame (브랜드별 평균 평점)
        }
    """
    if 'brand' not in df.columns:
        return None
    
    stats = {}
    
    # 브랜드별 리뷰 수 TOP N
    stats['review_counts'] = df['brand'].value_counts().head(top_n)
    
    # 브랜드별 평균 평점
    if 'rating_numeric' in df.columns:
        brand_ratings = df.groupby('brand').agg({
            'rating_numeric': ['count', 'mean']
        }).round(2)
        brand_ratings.columns = ['count', 'mean']
        
        # 최소 리뷰 수 필터링
        brand_ratings = brand_ratings[brand_ratings['count'] >= min_reviews]
        
        # 평점 높은 순으로 정렬
        stats['avg_ratings'] = brand_ratings.sort_values('mean', ascending=False).head(10)
    else:
        stats['avg_ratings'] = None
    
    return stats