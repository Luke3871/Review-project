#//==============================================================================//#
"""
keyword_extraction.py
키워드 추출 (TF-IDF 기반)

last_updated: 2025.10.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter

# 토크나이저 import
utils_path = os.path.join(analytics_dir, 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

from utils.tokenizer import get_tfidf_vectorizer, get_tokenizer_for_channel

#//==============================================================================//#
# Keyword Extractor
#//==============================================================================//#

class KeywordExtractor:
    """
    TF-IDF 기반 키워드 추출기
    """
    
    def __init__(self, channel: str = 'OliveYoung'):
        """
        초기화
        
        Args:
            channel: 채널명 (토크나이저 선택용)
        """
        self.channel = channel
        self.tokenizer = get_tokenizer_for_channel(channel)
    
    def extract(
        self,
        texts: List[str],
        top_n: int = 30,
        min_df: int = 2,
        max_df: float = 0.85
    ) -> Dict:
        """
        TF-IDF 기반 키워드 추출
        
        Args:
            texts: 텍스트 리스트
            top_n: 상위 N개
            min_df: 최소 문서 빈도
            max_df: 최대 문서 빈도 비율
        
        Returns:
            {
                'keywords': [
                    {'word': '보습', 'tfidf_score': 0.85, 'doc_freq': 120},
                    ...
                ],
                'total_docs': int
            }
        """
        
        if len(texts) == 0:
            return {
                'keywords': [],
                'total_docs': 0
            }
        
        # TF-IDF Vectorizer
        vectorizer = get_tfidf_vectorizer(
            channel_name=self.channel,
            min_df=min_df,
            max_df=max_df,
            max_features=top_n * 2,
            ngram_range=(1, 1)  # Unigram만
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # 평균 TF-IDF 점수
            mean_scores = tfidf_matrix.mean(axis=0).A1
            
            # 문서 빈도 (몇 개 문서에 등장했는지)
            doc_freq = (tfidf_matrix > 0).sum(axis=0).A1
            
            # 정렬
            indices = mean_scores.argsort()[::-1][:top_n]
            
            keywords = []
            for i in indices:
                keywords.append({
                    'word': feature_names[i],
                    'tfidf_score': float(mean_scores[i]),
                    'doc_freq': int(doc_freq[i])
                })
            
            return {
                'keywords': keywords,
                'total_docs': len(texts)
            }
            
        except Exception as e:
            print(f"TF-IDF 추출 실패: {e}")
            return {
                'keywords': [],
                'total_docs': len(texts)
            }

#//==============================================================================//#
# Product Keyword Analysis
#//==============================================================================//#

def extract_product_keywords(
    df: pd.DataFrame,
    product_name: str,
    channel: str = 'OliveYoung',
    top_n: int = 30,
    with_sentiment: bool = False
) -> Dict:
    """
    제품별 키워드 추출
    
    Args:
        df: 리뷰 DataFrame
        product_name: 제품명
        channel: 채널명
        top_n: 상위 N개
        with_sentiment: 감성 분석 결과 포함 여부
    
    Returns:
        {
            'product_name': str,
            'channel': str,
            'total_reviews': int,
            'keywords': [
                {
                    'word': str,
                    'tfidf_score': float,
                    'doc_freq': int,
                    'sentiment': {...}  # with_sentiment=True일 때
                }
            ]
        }
    """
    
    # 제품 필터
    product_df = df[
        (df['product_name'] == product_name) & 
        (df['channel'] == channel)
    ].copy()
    
    if product_df.empty:
        return {
            'error': '데이터 없음',
            'product_name': product_name,
            'channel': channel
        }
    
    # 키워드 추출
    extractor = KeywordExtractor(channel=channel)
    texts = product_df['review_text'].fillna('').astype(str).tolist()
    
    result = extractor.extract(texts, top_n=top_n)
    
    # 감성 결합
    if with_sentiment and 'overall_label' in product_df.columns:
        result['keywords'] = _attach_sentiment(
            result['keywords'],
            product_df,
            extractor.tokenizer
        )
    
    return {
        'product_name': product_name,
        'channel': channel,
        'total_reviews': len(product_df),
        'keywords': result['keywords']
    }


def extract_brand_keywords(
    df: pd.DataFrame,
    brand: str,
    channel: Optional[str] = None,
    top_n: int = 30,
    with_sentiment: bool = False
) -> Dict:
    """
    브랜드별 키워드 추출
    
    Args:
        df: 리뷰 DataFrame
        brand: 브랜드명
        channel: 채널명 (Optional, None이면 전체)
        top_n: 상위 N개
        with_sentiment: 감성 분석 결과 포함 여부
    
    Returns:
        {
            'brand': str,
            'channel': str,
            'total_reviews': int,
            'keywords': [...]
        }
    """
    
    # 브랜드 필터
    if channel:
        brand_df = df[
            (df['brand'] == brand) & 
            (df['channel'] == channel)
        ].copy()
        use_channel = channel
    else:
        brand_df = df[df['brand'] == brand].copy()
        use_channel = brand_df['channel'].mode()[0] if len(brand_df) > 0 else 'OliveYoung'
    
    if brand_df.empty:
        return {
            'error': '데이터 없음',
            'brand': brand,
            'channel': channel
        }
    
    # 키워드 추출
    extractor = KeywordExtractor(channel=use_channel)
    texts = brand_df['review_text'].fillna('').astype(str).tolist()
    
    result = extractor.extract(texts, top_n=top_n)
    
    # 감성 결합
    if with_sentiment and 'overall_label' in brand_df.columns:
        result['keywords'] = _attach_sentiment(
            result['keywords'],
            brand_df,
            extractor.tokenizer
        )
    
    return {
        'brand': brand,
        'channel': channel if channel else 'all',
        'total_reviews': len(brand_df),
        'keywords': result['keywords']
    }


def compare_brand_keywords(
    df: pd.DataFrame,
    brands: List[str],
    channel: Optional[str] = None,
    top_n: int = 20
) -> Dict:
    """
    브랜드 간 키워드 비교
    
    Args:
        df: 리뷰 DataFrame
        brands: 브랜드 리스트
        channel: 채널명 (Optional)
        top_n: 각 브랜드당 상위 N개
    
    Returns:
        {
            'brands': {
                'VT': {
                    'keywords': [...],
                    'total_reviews': int
                },
                'laundrylab': {...}
            },
            'comparison': {
                'common': [...],  # 공통 키워드
                'unique': {       # 브랜드별 고유 키워드
                    'VT': [...],
                    'laundrylab': [...]
                }
            }
        }
    """
    
    results = {}
    all_keywords = {}
    
    # 각 브랜드별 키워드 추출
    for brand in brands:
        brand_result = extract_brand_keywords(
            df,
            brand=brand,
            channel=channel,
            top_n=top_n,
            with_sentiment=False
        )
        
        if 'error' not in brand_result:
            results[brand] = brand_result
            all_keywords[brand] = set([kw['word'] for kw in brand_result['keywords']])
    
    if len(results) < 2:
        return {'error': '비교할 브랜드 데이터 부족'}
    
    # 공통 키워드
    common = set.intersection(*all_keywords.values())
    
    # 브랜드별 고유 키워드
    unique = {}
    for brand, keywords in all_keywords.items():
        other_keywords = set()
        for other_brand, other_kws in all_keywords.items():
            if other_brand != brand:
                other_keywords.update(other_kws)
        
        unique[brand] = list(keywords - other_keywords)
    
    return {
        'brands': results,
        'comparison': {
            'common': list(common),
            'unique': unique
        }
    }


def compare_product_keywords(
    df: pd.DataFrame,
    products: List[Tuple[str, str]],
    top_n: int = 20
) -> Dict:
    """
    제품 간 키워드 비교
    
    Args:
        df: 리뷰 DataFrame
        products: [(product_name, channel), ...] 리스트
        top_n: 각 제품당 상위 N개
    
    Returns:
        {
            'products': {
                'VT 리들샷': {...},
                '라운드랩 토너': {...}
            },
            'comparison': {
                'common': [...],
                'unique': {...}
            }
        }
    """
    
    results = {}
    all_keywords = {}
    
    # 각 제품별 키워드 추출
    for product_name, channel in products:
        product_result = extract_product_keywords(
            df,
            product_name=product_name,
            channel=channel,
            top_n=top_n,
            with_sentiment=False
        )
        
        if 'error' not in product_result:
            key = f"{product_name} ({channel})"
            results[key] = product_result
            all_keywords[key] = set([kw['word'] for kw in product_result['keywords']])
    
    if len(results) < 2:
        return {'error': '비교할 제품 데이터 부족'}
    
    # 공통 키워드
    common = set.intersection(*all_keywords.values())
    
    # 제품별 고유 키워드
    unique = {}
    for product, keywords in all_keywords.items():
        other_keywords = set()
        for other_product, other_kws in all_keywords.items():
            if other_product != product:
                other_keywords.update(other_kws)
        
        unique[product] = list(keywords - other_keywords)
    
    return {
        'products': results,
        'comparison': {
            'common': list(common),
            'unique': unique
        }
    }


#//==============================================================================//#
# Sentiment Integration
#//==============================================================================//#

def _attach_sentiment(
    keywords: List[Dict],
    df: pd.DataFrame,
    tokenizer
) -> List[Dict]:
    """
    키워드에 감성 분석 결과 추가
    
    Args:
        keywords: 키워드 리스트
        df: 리뷰 DataFrame (overall_label 컬럼 포함)
        tokenizer: 토크나이저
    
    Returns:
        감성 정보가 추가된 키워드 리스트
    """
    
    result = []
    
    for kw in keywords:
        word = kw['word']
        
        # 해당 키워드가 포함된 리뷰 찾기
        matching_reviews = []
        for idx, row in df.iterrows():
            tokens = tokenizer(row['review_text'])
            if word in tokens:
                matching_reviews.append(row)
        
        if not matching_reviews:
            result.append(kw)
            continue
        
        # 감성 집계
        sentiments = [
            r['overall_label'] 
            for r in matching_reviews 
            if 'overall_label' in r
        ]
        
        if sentiments:
            positive_count = sentiments.count('positive')
            negative_count = sentiments.count('negative')
            total = len(sentiments)
            
            kw['sentiment'] = {
                'positive': positive_count,
                'negative': negative_count,
                'positive_ratio': positive_count / total if total > 0 else 0
            }
        
        result.append(kw)
    
    return result


#//==============================================================================//#
# Helper Functions
#//==============================================================================//#

def get_keyword_contexts(
    df: pd.DataFrame,
    keyword: str,
    channel: str = 'OliveYoung',
    max_samples: int = 5
) -> List[str]:
    """
    특정 키워드가 사용된 문맥 추출
    
    Args:
        df: 리뷰 DataFrame
        keyword: 키워드
        channel: 채널명
        max_samples: 최대 샘플 수
    
    Returns:
        문맥 리스트
    """
    
    tokenizer = get_tokenizer_for_channel(channel)
    contexts = []
    
    for text in df['review_text']:
        tokens = tokenizer(text)
        if keyword in tokens:
            contexts.append(text)
            if len(contexts) >= max_samples:
                break
    
    return contexts