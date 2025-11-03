#//==============================================================================//#
"""
rating_metrics.py

 - 평점별 리뷰수


last_updated : 2025.10.16
"""
#//==============================================================================//#

import pandas as pd


def calculate_rating_distribution(df):
    """
    평점 분포 계산
    
    Args:
        df: DataFrame
    
    Returns:
        dict: {
            'distribution': Series (평점별 리뷰 수),
            'stats': dict (mean, median, std),
            'valid_ratings': Series (유효한 평점 데이터)
        }
    """
    if 'rating_numeric' not in df.columns:
        return None
    
    valid_ratings = df['rating_numeric'].dropna()

    if valid_ratings.empty:
        return None

    # 평점을 정수로 변환 (1, 2, 3, 4, 5만 표시)
    valid_ratings_int = valid_ratings.round().astype(int)

    result = {
        'valid_ratings': valid_ratings_int,
        'distribution': valid_ratings_int.value_counts().sort_index(),
        'stats': {
            'mean': valid_ratings.mean(),
            'median': valid_ratings.median(),
            'std': valid_ratings.std()
        }
    }

    return result