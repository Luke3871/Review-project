#//==============================================================================//#
"""
keyword_analyzer.py
V1 Rule-based 키워드 분석

- TfidfVectorizer 기반 키워드 추출 (dashboard tokenizer 사용)
- 긍정/부정 키워드 분석

UI 버전(tab1_daiso_section.py)에서 이식
last_updated: 2025.10.26
"""
#//==============================================================================//#

import sys
import os
import pandas as pd
import numpy as np

# dashboard 경로 추가
dashboard_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

# dashboard의 커스텀 벡터라이저 사용
from analyzer.txt_mining.tokenizer import get_tfidf_vectorizer, get_count_vectorizer

#//==============================================================================//#
# 제품 키워드 분석
#//==============================================================================//#

def analyze_product_keywords(product_df, channel):
    """제품 키워드 분석 (TF-IDF 기반, dashboard tokenizer 사용)

    Args:
        product_df (DataFrame): 제품 리뷰 데이터
        channel (str): 채널명

    Returns:
        list: [(키워드, TF-IDF 점수), ...] 튜플 리스트
    """
    if product_df.empty or 'review_text' not in product_df.columns:
        return None

    # 리뷰 텍스트 추출
    reviews = product_df['review_text'].fillna('').astype(str)
    reviews = reviews[reviews.str.len() > 0]

    if len(reviews) == 0:
        return None

    try:
        # dashboard의 TF-IDF 벡터라이저 사용
        vectorizer = get_tfidf_vectorizer(
            channel_name=channel,
            min_df=2,
            max_features=30,
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(reviews)
        feature_names = vectorizer.get_feature_names_out()
        scores = matrix.mean(axis=0).A1

        word_scores = list(zip(feature_names, scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)

        return word_scores

    except Exception as e:
        print(f"키워드 분석 중 오류: {e}")
        return None

#//==============================================================================//#
# 긍정/부정 키워드 분석
#//==============================================================================//#

def analyze_sentiment_keywords(product_df, channel):
    """긍정/부정 키워드 분석 (Count 기반, dashboard tokenizer 사용)

    Args:
        product_df (DataFrame): 제품 리뷰 데이터
        channel (str): 채널명

    Returns:
        tuple: (positive_keywords, negative_keywords)
               각각 [(키워드, 빈도), ...] 형태
               하나가 없어도 나머지는 반환
    """
    if product_df.empty or 'review_text' not in product_df.columns or 'rating' not in product_df.columns:
        return None, None

    # 평점을 숫자로 변환
    product_df = product_df.copy()
    product_df['rating_numeric'] = pd.to_numeric(product_df['rating'], errors='coerce')

    # 긍정/부정 리뷰 분리 (4점 이상: 긍정, 3점 이하: 부정)
    positive_reviews = product_df[product_df['rating_numeric'] >= 4]['review_text'].fillna('').astype(str)
    negative_reviews = product_df[product_df['rating_numeric'] <= 3]['review_text'].fillna('').astype(str)

    positive_keywords = None
    negative_keywords = None

    try:
        # dashboard의 Count 벡터라이저 사용
        vectorizer = get_count_vectorizer(
            channel_name=channel,
            min_df=1,
            max_features=20,
            ngram_range=(1, 2)
        )

        # 긍정 키워드 (있는 경우만)
        if len(positive_reviews) > 0:
            positive_reviews_filtered = positive_reviews[positive_reviews.str.len() > 0]
            if len(positive_reviews_filtered) > 0:
                pos_matrix = vectorizer.fit_transform(positive_reviews_filtered)
                pos_features = vectorizer.get_feature_names_out()
                pos_scores = pos_matrix.sum(axis=0).A1

                positive_keywords = list(zip(pos_features, pos_scores))
                positive_keywords.sort(key=lambda x: x[1], reverse=True)
                positive_keywords = positive_keywords[:10]

        # 부정 키워드 (있는 경우만)
        if len(negative_reviews) > 0:
            negative_reviews_filtered = negative_reviews[negative_reviews.str.len() > 0]
            if len(negative_reviews_filtered) > 0:
                # 벡터라이저 재생성 (다른 corpus이므로)
                vectorizer_neg = get_count_vectorizer(
                    channel_name=channel,
                    min_df=1,
                    max_features=20,
                    ngram_range=(1, 2)
                )
                neg_matrix = vectorizer_neg.fit_transform(negative_reviews_filtered)
                neg_features = vectorizer_neg.get_feature_names_out()
                neg_scores = neg_matrix.sum(axis=0).A1

                negative_keywords = list(zip(neg_features, neg_scores))
                negative_keywords.sort(key=lambda x: x[1], reverse=True)
                negative_keywords = negative_keywords[:10]

        return positive_keywords, negative_keywords

    except Exception as e:
        print(f"감정 분석 중 오류: {e}")
        return positive_keywords, negative_keywords


def extract_overall_keywords(product_df, channel):
    """전체 키워드 분석 (긍정/부정 구분 없이, TF-IDF 기반, dashboard tokenizer 사용)

    Args:
        product_df (DataFrame): 제품 리뷰 데이터
        channel (str): 채널명

    Returns:
        list: [(키워드, TF-IDF 점수), ...] 형태
    """
    if product_df.empty or 'review_text' not in product_df.columns:
        return None

    # 리뷰 텍스트 추출
    reviews = product_df['review_text'].fillna('').astype(str)
    reviews = reviews[reviews.str.len() > 0]

    if len(reviews) == 0:
        return None

    try:
        # dashboard의 TF-IDF 벡터라이저 사용
        vectorizer = get_tfidf_vectorizer(
            channel_name=channel,
            min_df=2,
            max_features=30,
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(reviews)
        feature_names = vectorizer.get_feature_names_out()
        scores = matrix.mean(axis=0).A1

        word_scores = list(zip(feature_names, scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)

        return word_scores[:20]  # TOP 20 반환

    except Exception as e:
        print(f"전체 키워드 분석 중 오류: {e}")
        return None
