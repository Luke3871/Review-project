#//==============================================================================//#
"""
trend_analysis.py
시계열 트렌드 분석

last_updated : 2025.10.02
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
from typing import List, Dict
from utils.validators import validate_common_columns, preprocess_dataframe

#//==============================================================================//#
# 월별 트렌드 분석
#//==============================================================================//#

def analyze_monthly_trends(
    df: pd.DataFrame,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    브랜드 x 채널별 월별 트렌드 계산
    
    Returns:
        List[Dict]: monthly_trends 테이블용 데이터
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'brand' not in df.columns:
        raise ValueError("brand 컬럼 필요")
    
    df['year_month'] = pd.to_datetime(df['review_date']).dt.to_period('M').astype(str)
    
    results = []
    
    for (brand, channel, year_month) in df.groupby(['brand', 'channel', 'year_month']).groups.keys():
        month_df = df[
            (df['brand'] == brand) & 
            (df['channel'] == channel) & 
            (df['year_month'] == year_month)
        ]
        
        results.append({
            'brand': brand,
            'channel': channel,
            'year_month': year_month,
            'review_count': len(month_df),
            'avg_rating': float(month_df['rating'].mean())
        })
    
    return results


def analyze_product_trends(
    df: pd.DataFrame,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    제품별 월별 트렌드 (상세 분석용)
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'product_name' not in df.columns:
        raise ValueError("product_name 컬럼 필요")
    
    df['year_month'] = pd.to_datetime(df['review_date']).dt.to_period('M').astype(str)
    
    results = []
    
    for (product, channel, year_month) in df.groupby(['product_name', 'channel', 'year_month']).groups.keys():
        month_df = df[
            (df['product_name'] == product) & 
            (df['channel'] == channel) & 
            (df['year_month'] == year_month)
        ]
        
        results.append({
            'product_name': product,
            'channel': channel,
            'year_month': year_month,
            'review_count': len(month_df),
            'avg_rating': float(month_df['rating'].mean())
        })
    
    return results