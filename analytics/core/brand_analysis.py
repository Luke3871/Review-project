#//==============================================================================//#
"""
brand_analysis.py
브랜드별 속성 분석

입력: DataFrame (reviews)
출력: List[Dict] (brand_attribute_stats 테이블용)

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
from typing import List, Dict
from config import ATTRIBUTES, POSITIVE_RATING_THRESHOLD, NEGATIVE_RATING_THRESHOLD, MIN_SAMPLE_SIZE
from utils.validators import validate_common_columns, preprocess_dataframe

#//==============================================================================//#
# 브랜드 x 속성 분석
#//==============================================================================//#

def analyze_brand_attributes(
    df: pd.DataFrame,
    min_samples: int = MIN_SAMPLE_SIZE,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    브랜드별 속성 통계 계산
    
    Args:
        df: reviews DataFrame
        min_samples: 최소 표본 수
    
    Returns:
        List[Dict]: brand_attribute_stats 테이블용 데이터
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'brand' not in df.columns:
        raise ValueError("brand 컬럼 필요")
    
    results = []
    
    for brand in df['brand'].dropna().unique():
        brand_df = df[df['brand'] == brand]
        
        for channel in brand_df['channel'].unique():
            channel_df = brand_df[brand_df['channel'] == channel]
            
            for attr, keywords in ATTRIBUTES.items():
                pattern = '|'.join(keywords)
                mask = channel_df['review_text'].str.contains(pattern, case=False, na=False, regex=True)
                relevant = channel_df[mask]
                
                if len(relevant) < min_samples:
                    continue
                
                positive = relevant[relevant['rating'] >= POSITIVE_RATING_THRESHOLD]
                negative = relevant[relevant['rating'] <= NEGATIVE_RATING_THRESHOLD]
                neutral = relevant[
                    (relevant['rating'] > NEGATIVE_RATING_THRESHOLD) & 
                    (relevant['rating'] < POSITIVE_RATING_THRESHOLD)
                ]
                
                top_reviews = positive.nlargest(3, 'rating')['review_text'].tolist() if len(positive) > 0 else []
                
                results.append({
                    'brand': brand,
                    'attribute': attr,
                    'channel': channel,
                    'positive_count': len(positive),
                    'negative_count': len(negative),
                    'neutral_count': len(neutral),
                    'positive_ratio': len(positive) / len(relevant) if len(relevant) > 0 else 0,
                    'negative_ratio': len(negative) / len(relevant) if len(relevant) > 0 else 0,
                    'sample_size': len(relevant),
                    'avg_rating': float(relevant['rating'].mean()),
                    'representative_reviews': top_reviews,
                    'period_start': df['review_date'].min().strftime('%Y-%m-%d'),
                    'period_end': df['review_date'].max().strftime('%Y-%m-%d'),
                })
    
    return results
