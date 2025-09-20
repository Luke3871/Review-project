"""
간단한 감정 분석 모듈 (평점 기반)
- 4-5점: 긍정, 1-3점: 부정
- 나중에 딥러닝 모델로 교체 가능하도록 인터페이스 통일
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from analyzer.txt_mining.tokenizer import get_count_vectorizer

class SentimentAnalyzer:
    
    def __init__(self, channel_name="daiso"):
        self.channel_name = channel_name
    
    def analyze_sentiment_keywords(self, product_df, min_rating_positive=4, max_rating_negative=3):
        """
        긍정/부정 감정별 키워드 분석
        
        Args:
            product_df: 제품 리뷰 데이터프레임
            min_rating_positive: 긍정으로 분류할 최소 평점 (기본값: 4점 이상)
            max_rating_negative: 부정으로 분류할 최대 평점 (기본값: 3점 이하)
        
        Returns:
            tuple: (positive_keywords, negative_keywords)
                   각각 [(키워드, 빈도수)] 형태의 리스트
        """
        if product_df.empty or 'review_text' not in product_df.columns or 'rating' not in product_df.columns:
            return None, None
        
        # 평점을 숫자로 변환
        product_df = product_df.copy()
        product_df['rating_numeric'] = product_df['rating'].apply(self._extract_rating)
        
        # 긍정/부정 리뷰 분리
        positive_reviews = product_df[product_df['rating_numeric'] >= min_rating_positive]['review_text'].fillna('').astype(str)
        negative_reviews = product_df[product_df['rating_numeric'] <= max_rating_negative]['review_text'].fillna('').astype(str)
        
        positive_reviews = positive_reviews[positive_reviews.str.len() > 0]
        negative_reviews = negative_reviews[negative_reviews.str.len() > 0]
        
        if len(positive_reviews) == 0 or len(negative_reviews) == 0:
            return None, None
        
        try:
            # Count 벡터라이저 사용 (감정 분석에는 빈도가 직관적)
            vectorizer = get_count_vectorizer(
                channel_name=self.channel_name,
                max_features=20,
                min_df=1,
                ngram_range=(1, 2)
            )
            
            # 긍정 키워드 분석
            positive_keywords = []
            if len(positive_reviews) > 0:
                pos_matrix = vectorizer.fit_transform(positive_reviews)
                pos_features = vectorizer.get_feature_names_out()
                pos_scores = pos_matrix.sum(axis=0).A1
                positive_keywords = list(zip(pos_features, pos_scores))
                positive_keywords.sort(key=lambda x: x[1], reverse=True)
            
            # 부정 키워드 분석 (새로운 벡터라이저로)
            negative_keywords = []
            if len(negative_reviews) > 0:
                neg_vectorizer = get_count_vectorizer(
                    channel_name=self.channel_name,
                    max_features=20,
                    min_df=1,
                    ngram_range=(1, 2)
                )
                neg_matrix = neg_vectorizer.fit_transform(negative_reviews)
                neg_features = neg_vectorizer.get_feature_names_out()
                neg_scores = neg_matrix.sum(axis=0).A1
                negative_keywords = list(zip(neg_features, neg_scores))
                negative_keywords.sort(key=lambda x: x[1], reverse=True)
            
            return positive_keywords[:10], negative_keywords[:10]
            
        except Exception as e:
            print(f"감정 분석 중 오류: {e}")
            return None, None
    
    def get_sentiment_distribution(self, product_df):
        """
        감정 분포 계산
        
        Returns:
            dict: {'positive_count', 'negative_count', 'positive_ratio', 'negative_ratio'}
        """
        if product_df.empty or 'rating' not in product_df.columns:
            return None
        
        product_df = product_df.copy()
        product_df['rating_numeric'] = product_df['rating'].apply(self._extract_rating)
        valid_ratings = product_df.dropna(subset=['rating_numeric'])
        
        if len(valid_ratings) == 0:
            return None
        
        positive_count = len(valid_ratings[valid_ratings['rating_numeric'] >= 4])
        negative_count = len(valid_ratings[valid_ratings['rating_numeric'] <= 3])
        total_count = len(valid_ratings)
        
        return {
            'positive_count': positive_count,
            'negative_count': negative_count,
            'total_count': total_count,
            'positive_ratio': positive_count / total_count if total_count > 0 else 0,
            'negative_ratio': negative_count / total_count if total_count > 0 else 0
        }
    
    def classify_sentiment(self, rating):
        """
        평점을 감정으로 분류 (단순 평점 기반)
        
        Args:
            rating: 평점 (문자열 또는 숫자)
        
        Returns:
            str: "긍정", "부정"
        """
        rating_numeric = self._extract_rating(rating)
        
        if pd.isna(rating_numeric):
            return "중립"
        elif rating_numeric >= 4:
            return "긍정"
        else:  # 1-3점
            return "부정"
    
    def add_sentiment_labels(self, df, rating_column='rating'):
        """
        데이터프레임에 감정 라벨 추가
        
        Args:
            df: 데이터프레임
            rating_column: 평점 컬럼명
        
        Returns:
            pd.DataFrame: 감정 라벨이 추가된 데이터프레임
        """
        df = df.copy()
        df['sentiment'] = df[rating_column].apply(self.classify_sentiment)
        return df
    
    # 나중에 딥러닝 모델로 교체할 때를 위한 인터페이스
    def predict_sentiment(self, text):
        """
        텍스트 기반 감정 예측 (현재는 미구현, 나중에 BERT 등으로 교체)
        
        Args:
            text: 예측할 텍스트
        
        Returns:
            dict: 예측 결과 (나중에 구현)
        """
        # TODO: 나중에 딥러닝 모델로 교체
        return {
            "prediction": "구현 예정",
            "confidence": 0.0,
            "method": "rating_based"
        }
    
    def _extract_rating(self, rating_str):
        """평점을 숫자로 변환"""
        if pd.isna(rating_str):
            return np.nan
        
        rating_str = str(rating_str)
        
        if '점' in rating_str:
            try:
                return float(rating_str.replace('점', ''))
            except:
                return np.nan
        elif '★' in rating_str:
            return float(rating_str.count('★'))
        
        try:
            return float(rating_str)
        except:
            return np.nan