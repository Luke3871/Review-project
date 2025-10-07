#//==============================================================================//#
"""
keyword_analysis.py
제품별 키워드 분석

last_updated : 2025.10.02
"""
#//==============================================================================//#

import pandas as pd
from typing import List, Dict
from pathlib import Path
import sys
import os

# analytics 폴더 고정
current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from utils.tokenizer import get_count_vectorizer, get_tfidf_vectorizer
from utils.validators import validate_common_columns, preprocess_dataframe

#//==============================================================================//#
# 제품별 키워드 분석
#//==============================================================================//#

def analyze_product_keywords(
    df: pd.DataFrame,
    analysis_type: str = 'tfidf',
    max_keywords: int = 30,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    제품별 대표 키워드 추출
    
    Args:
        df: reviews DataFrame
        analysis_type: 'count' or 'tfidf'
        max_keywords: 추출할 키워드 개수
    
    Returns:
        List[Dict]: product_keywords 테이블용 데이터
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'product_name' not in df.columns or 'review_text' not in df.columns:
        raise ValueError("product_name, review_text 컬럼 필요")
    
    results = []
    
    for (product, channel) in df.groupby(['product_name', 'channel']).groups.keys():
        product_df = df[(df['product_name'] == product) & (df['channel'] == channel)]
        
        keywords = extract_keywords(
            product_df['review_text'], 
            channel.lower(), 
            analysis_type, 
            max_keywords
        )
        
        if not keywords:
            continue
        
        results.append({
            'product_name': product,
            'channel': channel,
            'keywords': [{'word': word, 'score': float(score)} for word, score in keywords],
            'top_keywords': [word for word, _ in keywords[:10]],
            'analysis_type': analysis_type,
            'period_start': product_df['review_date'].min().strftime('%Y-%m-%d'),
            'period_end': product_df['review_date'].max().strftime('%Y-%m-%d'),
        })
    
    return results


def extract_keywords(reviews: pd.Series, channel: str, analysis_type: str, max_keywords: int) -> List:
    """
    리뷰에서 키워드 추출
    """
    
    reviews = reviews.fillna('').astype(str)
    reviews = reviews[reviews.str.len() > 0]
    
    if len(reviews) == 0:
        return []
    
    try:
        if analysis_type == 'count':
            vectorizer = get_count_vectorizer(
                channel_name=channel,
                max_features=max_keywords,
                min_df=2,
                ngram_range=(1, 2)
            )
        else:
            vectorizer = get_tfidf_vectorizer(
                channel_name=channel,
                max_features=max_keywords,
                min_df=2,
                max_df=0.85,
                ngram_range=(1, 2)
            )
        
        matrix = vectorizer.fit_transform(reviews)
        features = vectorizer.get_feature_names_out()
        
        if analysis_type == 'count':
            scores = matrix.sum(axis=0).A1
        else:
            scores = matrix.mean(axis=0).A1
        
        keywords = list(zip(features, scores))
        keywords.sort(key=lambda x: x[1], reverse=True)
        
        return keywords
        
    except Exception as e:
        print(f"키워드 추출 오류: {e}")
        return []