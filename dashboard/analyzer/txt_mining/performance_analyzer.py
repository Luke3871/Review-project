"""
대시보드용 기본 성과 분석 모듈
- 기존 모듈들(sentiment_analyzer, tokenizer)을 조합해서 사용
- 대시보드에서 필요한 성과 지표 및 통계 계산
- 사용자 설정 가능한 벡터라이저 파라미터 지원
"""

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from analyzer.txt_mining.sentiment_analyzer import SentimentAnalyzer
from analyzer.txt_mining.tokenizer import get_count_vectorizer, get_tfidf_vectorizer

class PerformanceAnalyzer:
    
    def __init__(self, channel_name="daiso"):
        self.channel_name = channel_name
        self.sentiment_analyzer = SentimentAnalyzer(channel_name=channel_name)
    
    def calculate_product_performance(self, df):
        """
        제품별 성과 지표 계산 (대시보드용)
        
        Args:
            df: 리뷰 데이터프레임
            
        Returns:
            pd.DataFrame: 제품별 성과 지표
        """
        if df.empty or 'product_name' not in df.columns:
            return pd.DataFrame()
        
        performance_list = []
        
        for product in df['product_name'].unique():
            product_data = df[df['product_name'] == product].copy()
            first_row = product_data.iloc[0]
            
            # 감정 분석
            sentiment_dist = self.sentiment_analyzer.get_sentiment_distribution(product_data)
            
            # 평점 통계
            product_data['rating_numeric'] = product_data['rating'].apply(self._extract_rating)
            valid_ratings = product_data.dropna(subset=['rating_numeric'])
            
            # 기본 성과 지표
            performance = {
                'product_name': product,
                'category': first_row.get('category', 'Unknown'),
                'rank': first_row.get('rank', np.nan),
                'price': first_row.get('product_price', 'N/A'),
                'sort_type': first_row.get('sort_type', 'Unknown'),
                'review_count': len(product_data),
                'avg_rating': valid_ratings['rating_numeric'].mean() if not valid_ratings.empty else np.nan,
                'rating_std': valid_ratings['rating_numeric'].std() if not valid_ratings.empty else np.nan
            }
            
            # 감정 분석 결과 추가
            if sentiment_dist:
                performance.update({
                    'positive_count': sentiment_dist['positive_count'],
                    'negative_count': sentiment_dist['negative_count'],
                    'positive_ratio': sentiment_dist['positive_ratio'],
                    'negative_ratio': sentiment_dist['negative_ratio']
                })
            
            # 평점 분포
            if not valid_ratings.empty:
                for rating in range(1, 6):
                    performance[f'rating_{rating}_count'] = len(valid_ratings[valid_ratings['rating_numeric'] == rating])
            
            # 리뷰 텍스트 통계
            if 'review_text' in product_data.columns:
                text_lengths = product_data['review_text'].fillna('').str.len()
                performance.update({
                    'avg_review_length': text_lengths.mean(),
                    'long_review_count': len(text_lengths[text_lengths > 100])
                })
            
            performance_list.append(performance)
        
        return pd.DataFrame(performance_list)
    
    def get_product_basic_info(self, product_df):
        """
        제품 기본 정보 추출 (대시보드 표시용)
        
        Args:
            product_df: 특정 제품의 리뷰 데이터
            
        Returns:
            dict: 제품 기본 정보
        """
        if product_df.empty:
            return {}
        
        first_row = product_df.iloc[0]
        
        # 감정 분석 결과
        sentiment_dist = self.sentiment_analyzer.get_sentiment_distribution(product_df)
        
        # 평점 처리
        product_df = product_df.copy()
        product_df['rating_numeric'] = product_df['rating'].apply(self._extract_rating)
        valid_ratings = product_df.dropna(subset=['rating_numeric'])
        
        # 기본 정보
        basic_info = {
            'product_name': first_row.get('product_name', 'N/A'),
            'price': first_row.get('product_price', 'N/A'),
            'category': first_row.get('category', 'N/A'),
            'sort_type': first_row.get('sort_type', 'N/A'),
            'rank': first_row.get('rank', 'N/A'),
            'total_reviews': len(product_df)
        }
        
        # 감정 분석 결과
        if sentiment_dist:
            basic_info.update(sentiment_dist)
        
        # 평점 통계
        if not valid_ratings.empty:
            basic_info.update({
                'avg_rating': valid_ratings['rating_numeric'].mean(),
                'rating_counts': valid_ratings['rating_numeric'].value_counts().to_dict()
            })
        
        # 리뷰 텍스트 통계
        if 'review_text' in product_df.columns:
            text_lengths = product_df['review_text'].fillna('').str.len()
            basic_info.update({
                'avg_length': text_lengths.mean(),
                'max_length': text_lengths.max(),
                'min_length': text_lengths.min(),
                'long_reviews': len(text_lengths[text_lengths > 100])
            })
        
        # 날짜 범위
        if 'review_date' in product_df.columns:
            dates = product_df['review_date'].dropna()
            if not dates.empty:
                basic_info['date_range'] = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}"
        
        return basic_info
    
    def analyze_keywords_with_config(self, product_df, vectorizer_config):
        """
        사용자 설정 기반 키워드 분석
        
        Args:
            product_df: 제품 리뷰 데이터
            vectorizer_config: 벡터라이저 설정
                {
                    'analysis_type': 'count' or 'tfidf',
                    'min_df': int,
                    'max_df': float,
                    'max_features': int,
                    'ngram_range': tuple (min_n, max_n)
                }
        
        Returns:
            list: [(키워드, 점수)] 형태의 리스트
        """
        if product_df.empty or 'review_text' not in product_df.columns:
            return None
        
        reviews = product_df['review_text'].fillna('').astype(str)
        reviews = reviews[reviews.str.len() > 0]
        
        if len(reviews) == 0:
            return None
        
        try:
            # 설정에 따라 벡터라이저 선택
            if vectorizer_config['analysis_type'] == 'count':
                vectorizer = get_count_vectorizer(
                    channel_name=self.channel_name,
                    min_df=vectorizer_config.get('min_df', 2),
                    max_df=vectorizer_config.get('max_df', 1.0),
                    max_features=vectorizer_config.get('max_features', 30),
                    ngram_range=vectorizer_config.get('ngram_range', (1, 2))
                )
            else:  # tfidf
                vectorizer = get_tfidf_vectorizer(
                    channel_name=self.channel_name,
                    min_df=vectorizer_config.get('min_df', 2),
                    max_df=vectorizer_config.get('max_df', 0.85),
                    max_features=vectorizer_config.get('max_features', 30),
                    ngram_range=vectorizer_config.get('ngram_range', (1, 2))
                )
            
            # 벡터화 및 점수 계산
            matrix = vectorizer.fit_transform(reviews)
            feature_names = vectorizer.get_feature_names_out()
            
            if vectorizer_config['analysis_type'] == 'count':
                scores = matrix.sum(axis=0).A1
            else:
                scores = matrix.mean(axis=0).A1
            
            # 결과 정렬
            word_scores = list(zip(feature_names, scores))
            word_scores.sort(key=lambda x: x[1], reverse=True)
            
            return word_scores
            
        except Exception as e:
            print(f"키워드 분석 중 오류: {e}")
            return None
    
    def get_sentiment_keywords(self, product_df):
        """
        감정별 키워드 분석 (기존 모듈 활용)
        
        Args:
            product_df: 제품 리뷰 데이터
            
        Returns:
            tuple: (positive_keywords, negative_keywords)
        """
        return self.sentiment_analyzer.analyze_sentiment_keywords(product_df)
    
    def get_top_products(self, performance_df, metric='rating', top_n=10, min_reviews=3):
        """
        상위 제품 추출
        
        Args:
            performance_df: 성과 데이터프레임
            metric: 'rating' 또는 'reviews'
            top_n: 상위 몇 개
            min_reviews: 최소 리뷰 수 (평점 기준 시에만)
            
        Returns:
            pd.DataFrame: 상위 제품들
        """
        if performance_df.empty:
            return pd.DataFrame()
        
        if metric == 'rating':
            valid_products = performance_df[
                (performance_df['avg_rating'].notna()) & 
                (performance_df['review_count'] >= min_reviews)
            ]
            return valid_products.nlargest(top_n, 'avg_rating')
        else:  # reviews
            return performance_df.nlargest(top_n, 'review_count')
    
    def analyze_category_performance(self, performance_df):
        """
        카테고리별 성과 분석
        
        Args:
            performance_df: 성과 데이터프레임
            
        Returns:
            pd.DataFrame: 카테고리별 통계
        """
        if performance_df.empty or 'category' not in performance_df.columns:
            return pd.DataFrame()
        
        category_stats = performance_df.groupby('category').agg({
            'avg_rating': ['mean', 'std', 'count'],
            'review_count': ['sum', 'mean'],
            'positive_ratio': 'mean'
        }).round(2)
        
        # 컬럼명 정리
        category_stats.columns = [
            'avg_rating_mean', 'avg_rating_std', 'product_count',
            'total_reviews', 'avg_reviews_per_product', 'avg_positive_ratio'
        ]
        
        return category_stats.reset_index()
    
    def get_brand_performance(self, performance_df, brand_keywords=None):
        """
        브랜드별 성과 분석
        
        Args:
            performance_df: 성과 데이터프레임
            brand_keywords: 분석할 브랜드 키워드 리스트
            
        Returns:
            pd.DataFrame: 브랜드별 통계
        """
        if performance_df.empty or 'product_name' not in performance_df.columns:
            return pd.DataFrame()
        
        if brand_keywords is None:
            brand_keywords = ['CNP', 'TFS', '코드글로컬러', '케어존']
        
        brand_stats = []
        
        for brand in brand_keywords:
            brand_products = performance_df[
                performance_df['product_name'].str.contains(brand, case=False, na=False)
            ]
            
            if not brand_products.empty:
                valid_ratings = brand_products[brand_products['avg_rating'].notna()]
                
                stats = {
                    'brand': brand,
                    'product_count': len(brand_products),
                    'total_reviews': brand_products['review_count'].sum(),
                    'avg_rating': valid_ratings['avg_rating'].mean() if not valid_ratings.empty else np.nan,
                    'avg_reviews_per_product': brand_products['review_count'].mean(),
                    'avg_positive_ratio': brand_products['positive_ratio'].mean() if 'positive_ratio' in brand_products.columns else np.nan
                }
                
                brand_stats.append(stats)
        
        return pd.DataFrame(brand_stats)
    
    def calculate_performance_score(self, performance_df, rating_weight=0.6, review_weight=0.4):
        """
        종합 성과 점수 계산
        
        Args:
            performance_df: 성과 데이터프레임
            rating_weight: 평점 가중치
            review_weight: 리뷰수 가중치
            
        Returns:
            pd.DataFrame: 성과 점수가 추가된 데이터프레임
        """
        df = performance_df.copy()
        
        if df.empty:
            return df
        
        # 정규화
        if 'avg_rating' in df.columns and df['avg_rating'].notna().any():
            df['rating_normalized'] = (df['avg_rating'] - 1) / 4
        else:
            df['rating_normalized'] = 0
        
        if 'review_count' in df.columns and df['review_count'].max() > 0:
            df['review_normalized'] = df['review_count'] / df['review_count'].max()
        else:
            df['review_normalized'] = 0
        
        # 종합 점수
        df['performance_score'] = (
            df['rating_normalized'] * rating_weight + 
            df['review_normalized'] * review_weight
        )
        
        return df
    
    def get_competitive_position(self, product_name, performance_df):
        """
        특정 제품의 경쟁 위치 분석
        
        Args:
            product_name: 분석할 제품명
            performance_df: 성과 데이터프레임
            
        Returns:
            dict: 경쟁 위치 정보
        """
        product_data = performance_df[performance_df['product_name'] == product_name]
        
        if product_data.empty:
            return {"error": f"제품 '{product_name}'을 찾을 수 없습니다."}
        
        product_info = product_data.iloc[0]
        category = product_info.get('category', 'Unknown')
        
        # 같은 카테고리 제품들과 비교
        category_products = performance_df[performance_df['category'] == category]
        
        position = {
            "product_name": product_name,
            "category": category,
            "avg_rating": product_info.get('avg_rating', 0),
            "review_count": product_info.get('review_count', 0),
            "positive_ratio": product_info.get('positive_ratio', 0),
            "rank": product_info.get('rank', None)
        }
        
        if len(category_products) > 1:
            # 카테고리 내 순위
            rating_rank = (category_products['avg_rating'] > product_info.get('avg_rating', 0)).sum() + 1
            review_rank = (category_products['review_count'] > product_info.get('review_count', 0)).sum() + 1
            
            position.update({
                "rating_rank_in_category": f"{rating_rank}/{len(category_products)}",
                "review_rank_in_category": f"{review_rank}/{len(category_products)}",
                "category_avg_rating": category_products['avg_rating'].mean(),
                "category_avg_reviews": category_products['review_count'].mean()
            })
        
        return position
    
    def get_basic_insights(self, performance_df):
        """
        기본 통계 인사이트 (대시보드 표시용)
        
        Args:
            performance_df: 성과 데이터프레임
            
        Returns:
            dict: 기본 인사이트
        """
        if performance_df.empty:
            return {}
        
        valid_ratings = performance_df[performance_df['avg_rating'].notna()]
        
        insights = {
            'total_products': len(performance_df),
            'total_reviews': performance_df['review_count'].sum(),
            'avg_reviews_per_product': performance_df['review_count'].mean()
        }
        
        if not valid_ratings.empty:
            insights.update({
                'avg_rating_overall': valid_ratings['avg_rating'].mean(),
                'high_rated_products': len(valid_ratings[valid_ratings['avg_rating'] >= 4.5]),
                'low_rated_products': len(valid_ratings[valid_ratings['avg_rating'] <= 3.0]),
                'rating_review_correlation': valid_ratings['avg_rating'].corr(valid_ratings['review_count'])
            })
        
        if 'positive_ratio' in performance_df.columns:
            insights['avg_positive_ratio'] = performance_df['positive_ratio'].mean()
        
        return insights
    
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