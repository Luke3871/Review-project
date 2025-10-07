#//==============================================================================//#
"""
basic_stats.py
기본 통계 분석

last_updated : 2025.10.02
"""
#//==============================================================================//#
import sys
import os

# analytics 폴더 고정
current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)
    
import pandas as pd
from typing import Dict, List
from utils.validators import validate_common_columns, preprocess_dataframe

#//==============================================================================//#
# 제품별 통계 계산 (배치용 - product_stats 테이블에 적재)
#//==============================================================================//#

def compute_product_statistics(
    df: pd.DataFrame,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    모든 제품별 통계 계산
    
    Args:
        df: reviews DataFrame
    
    Returns:
        List[Dict]: 제품별 통계 리스트
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'product_name' not in df.columns:
        raise ValueError("product_name 컬럼 필요")
    
    results = []
    
    for (product, channel) in df.groupby(['product_name', 'channel']).groups.keys():
        product_df = df[(df['product_name'] == product) & (df['channel'] == channel)]
        
        results.append({
            'product_name': product,
            'brand': product_df['brand'].iloc[0] if 'brand' in product_df.columns else None,
            'channel': channel,
            'category': product_df['category'].iloc[0] if 'category' in product_df.columns else None,
            'total_reviews': len(product_df),
            'avg_rating': float(product_df['rating'].mean()),
            'median_rating': float(product_df['rating'].median()),
            'std_rating': float(product_df['rating'].std()),
            'rating_1': int((product_df['rating'] == 1.0).sum()),
            'rating_2': int((product_df['rating'] == 2.0).sum()),
            'rating_3': int((product_df['rating'] == 3.0).sum()),
            'rating_4': int((product_df['rating'] == 4.0).sum()),
            'rating_5': int((product_df['rating'] == 5.0).sum()),
            'product_price_sale': float(product_df['product_price_sale'].iloc[0]) if 'product_price_sale' in product_df.columns and pd.notna(product_df['product_price_sale'].iloc[0]) else None,
            'product_price_origin': float(product_df['product_price_origin'].iloc[0]) if 'product_price_origin' in product_df.columns and pd.notna(product_df['product_price_origin'].iloc[0]) else None,
            'date_start': product_df['review_date'].min().strftime('%Y-%m-%d'),
            'date_end': product_df['review_date'].max().strftime('%Y-%m-%d'),
        })
    
    return results


#//==============================================================================//#
# 기본 통계 (기존 함수들 그대로 유지)
#//==============================================================================//#

def get_basic_statistics(
    df: pd.DataFrame,
    auto_preprocess: bool = True
) -> Dict:
    """
    전체 데이터 기본 통계
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    return {
        'total_reviews': len(df),
        'avg_rating': float(df['rating'].mean()),
        'median_rating': float(df['rating'].median()),
        'std_rating': float(df['rating'].std()),
        'min_rating': float(df['rating'].min()),
        'max_rating': float(df['rating'].max()),
        'rating_distribution': df['rating'].value_counts().to_dict(),
        'date_range': {
            'start': df['review_date'].min().strftime('%Y-%m-%d'),
            'end': df['review_date'].max().strftime('%Y-%m-%d'),
        },
        'avg_text_length': float(df['review_text'].str.len().mean()),
    }


def get_channel_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    채널별 통계
    """
    
    if 'channel' not in df.columns:
        return None
    
    return df.groupby('channel').agg({
        'rating': ['count', 'mean', 'std'],
        'review_text': lambda x: x.str.len().mean()
    }).round(2)


def get_brand_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    브랜드별 기본 통계
    """
    
    if 'brand' not in df.columns:
        return None
    
    return df.groupby('brand').agg({
        'rating': ['count', 'mean', 'std'],
        'review_text': lambda x: x.str.len().mean()
    }).round(2).sort_values(('rating', 'count'), ascending=False)