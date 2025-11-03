#//==============================================================================//#
"""
utils.py
V1 Rule-based 보고서 유틸리티 함수

- 제품 기본 정보 추출
- 텍스트 전처리

UI 버전(tab1_daiso_section.py)에서 이식
last_updated: 2025.10.26
"""
#//==============================================================================//#

import pandas as pd
import numpy as np
import re

#//==============================================================================//#
# 텍스트 전처리
#//==============================================================================//#

def preprocess_korean_text(text):
    """한국어 텍스트 전처리

    Args:
        text: 원본 텍스트

    Returns:
        str: 전처리된 텍스트
    """
    if not text or pd.isna(text):
        return ''

    text = str(text)
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # URL 제거
    text = re.sub(r'https?://[^\s]+', '', text)
    # 한글, 영문, 숫자, 기본 문장부호만 유지
    text = re.sub(r'[^\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318Fa-zA-Z0-9\s.,!?~\-()]', ' ', text)
    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text)

    return text.strip()

#//==============================================================================//#
# 제품 기본 정보 추출
#//==============================================================================//#

def get_product_basic_info(product_df):
    """제품 기본 정보 추출

    Args:
        product_df (DataFrame): 특정 제품의 리뷰 데이터

    Returns:
        dict: 제품 기본 정보
    """
    if product_df.empty:
        return {}

    first_row = product_df.iloc[0]

    # 평점을 숫자로 변환
    product_df = product_df.copy()
    product_df['rating_numeric'] = pd.to_numeric(product_df['rating'], errors='coerce')

    # 평점 분포
    rating_counts = product_df['rating'].value_counts().to_dict()

    # 텍스트 길이 분석
    text_lengths = product_df['review_text'].fillna('').str.len()
    long_reviews = len(text_lengths[text_lengths > 100])
    negative_reviews = len(product_df[product_df['rating_numeric'] <= 3])

    # 날짜 범위
    dates = pd.to_datetime(product_df['review_date'], errors='coerce').dropna()
    if not dates.empty:
        date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}"
    else:
        date_range = "N/A"

    return {
        'product_name': first_row.get('product_name', 'N/A'),
        'price': first_row.get('product_price_sale', 'N/A'),
        'category': first_row.get('category', 'N/A'),
        'sort_type': first_row.get('sort_type', 'N/A'),
        'rank': first_row.get('ranking', 'N/A'),
        'brand': first_row.get('brand', 'N/A'),
        'channel': first_row.get('channel', 'N/A'),
        'total_reviews': len(product_df),
        'rating_counts': rating_counts,
        'avg_length': round(text_lengths.mean()) if len(text_lengths) > 0 else 0,
        'max_length': text_lengths.max() if len(text_lengths) > 0 else 0,
        'min_length': text_lengths.min() if len(text_lengths) > 0 else 0,
        'long_reviews': long_reviews,
        'negative_reviews': negative_reviews,
        'date_range': date_range
    }
