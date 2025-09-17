#//==============================================================================//#
"""
리뷰 데이터 전처리 모듈

기능:
- raw data preprocessing
    - converge str into float
    - delete unnecessary parts
    - delete punctuation
    - delete stopwords
    - create new columns for stats
        - classify date format
        - PLC
        - 추가 예정
    - classify sentiments (수정 예정)
    - calculate text metrics

last_updated : 2025.09.15
"""
#//==============================================================================//#
# Library import
#//==============================================================================//#
import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
from pathlib import Path

from config_preprocessor import PREPROCESSING_CONFIG, STOPWORDS_PATH, CHANNEL_CONFIGS

#//==============================================================================//#
# 리뷰 데이터 전처리 및 분석용 칼럼 생성
class DataPreprocessor:

    # 초기화
    def __init__(self):
        self.config = PREPROCESSING_CONFIG
        self.stopwords = self._load_stopwords()
    
    def clean_dataframe(self, df):
        if df.empty:
            return df
        
        print(f"전처리 시작: {len(df)}개 리뷰")
        
        # 1. 기본 데이터 정리
        df = self._clean_basic_data(df)
        
        # 2. 평점 숫자화
        df = self._extract_numeric_rating(df)
        
        # 3. 텍스트 정리
        df = self._clean_review_text(df)
        
        # 4. 감정 분류
        df = self._classify_sentiment(df)
        
        # 5. 텍스트 메트릭 계산
        df = self._calculate_text_metrics(df)
        
        # 6. 날짜 처리
        df = self._process_dates(df)
        
        print(f"전처리 완료: {len(df)}개 리뷰")
        
        return df
    
    def _clean_basic_data(self, df):
        original_count = len(df)
        
        # 필수 컬럼 확인
        required_columns = ['product_name', 'review_text']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"경고: 필수 컬럼 누락 - {missing_columns}")
            return pd.DataFrame()
        
        # 결측치 제거
        df = df.dropna(subset=required_columns)
        
        # 빈 리뷰 제거
        df = df[df['review_text'].astype(str).str.strip() != '']
        
        # 너무 짧은 리뷰 제거
        min_length = self.config['min_text_length']
        df = df[df['review_text'].astype(str).str.len() >= min_length]
        
        # 너무 긴 리뷰 제거
        max_length = self.config['max_text_length']
        df = df[df['review_text'].astype(str).str.len() <= max_length]
        
        # 중복 제거
        if self.config['remove_duplicates']:
            if all(col in df.columns for col in ['product_name', 'reviewer_name', 'review_text']):
                df = df.drop_duplicates(subset=['product_name', 'reviewer_name', 'review_text'])
            else:
                df = df.drop_duplicates(subset=['product_name', 'review_text'])
        
        print(f"전처리 완료: {original_count} → {len(df)}개")
        
        return df
    
    def _extract_numeric_rating(self, df):
        def extract_rating(rating_value):
            if pd.isna(rating_value):
                return np.nan
            
            rating_str = str(rating_value).strip()
            
            # "5점" 형태
            if '점' in rating_str:
                try:
                    return float(rating_str.replace('점', ''))
                except:
                    return np.nan
            
            # "★★★★★" 형태
            elif '★' in rating_str:
                return float(rating_str.count('★'))
            
            # 순수 숫자
            try:
                rating_num = float(rating_str)
                # 1-5 범위 체크
                if 1 <= rating_num <= 5:
                    return rating_num
                else:
                    return np.nan
            except:
                return np.nan
        
        if 'rating' in df.columns:
            df['rating_numeric'] = df['rating'].apply(extract_rating)
        
        return df
    
    # 리뷰 텍스트 기본 전처리
    def _clean_review_text(self, df):
        def clean_text(text):
            if pd.isna(text) or text == '':
                return ''
            
            text = str(text)
            
            # delete HTML tag
            if self.config['clean_html']:
                text = re.sub(r'<[^>]+>', '', text)
            
            # delete URL
            if self.config['clean_urls']:
                text = re.sub(r'https?://[^\s]+', '', text)
                text = re.sub(r'www\.[^\s]+', '', text)
            
            # delete punctuation
            text = re.sub(r'[^\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318Fa-zA-Z0-9\s.,!?~\-()]', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
        
        if 'review_text' in df.columns:
            df['review_text_cleaned'] = df['review_text'].apply(clean_text)
            
            # 정리 후 빈 텍스트 제거
            df = df[df['review_text_cleaned'] != '']
        
        return df
    
    # 0~3 부정적 리뷰, 4~5 긍정적 리뷰 (우선 이렇게)
    def _classify_sentiment(self, df):
        def classify_sentiment(rating):
            if pd.isna(rating):
                return 'unknown'
            elif rating >= self.config['positive_rating_threshold']:
                return 'positive'
            elif rating <= self.config['negative_rating_threshold']:
                return 'negative'

        
        if 'rating_numeric' in df.columns:
            df['sentiment'] = df['rating_numeric'].apply(classify_sentiment)
        
        return df
    
    # 
    def _calculate_text_metrics(self, df):
        if 'review_text_cleaned' in df.columns:
            # 글자수
            df['text_length'] = df['review_text_cleaned'].str.len()
            
            # 단어수 (공백 기준)
            df['word_count'] = df['review_text_cleaned'].str.split().str.len()
            
            # 긴 리뷰 여부
            threshold = self.config['long_review_threshold']
            df['is_long_review'] = df['text_length'] >= threshold
            
            # 짧은 리뷰 여부
            df['is_short_review'] = df['text_length'] <= 20
        
        return df
    
    # 리뷰 날짜 관련 처리 w/ PLC
    def _process_dates(self, df):
        if 'review_date' in df.columns:
            # 날짜 변환
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
            
            # 유효한 날짜만 처리
            valid_dates = df['review_date'].notna()
            
            if valid_dates.any():
                # 연, 월, 일 분리
                df.loc[valid_dates, 'review_year'] = df.loc[valid_dates, 'review_date'].dt.year
                df.loc[valid_dates, 'review_month'] = df.loc[valid_dates, 'review_date'].dt.month
                df.loc[valid_dates, 'review_day'] = df.loc[valid_dates, 'review_date'].dt.day
                df.loc[valid_dates, 'review_weekday'] = df.loc[valid_dates, 'review_date'].dt.dayofweek
                
                # 문자열 형태 (분석용)
                df.loc[valid_dates, 'review_month_str'] = df.loc[valid_dates, 'review_date'].dt.strftime('%Y-%m')
                df.loc[valid_dates, 'review_week_str'] = df.loc[valid_dates, 'review_date'].dt.strftime('%Y-W%U')
                
                # 제품 생명주기 (첫 리뷰 기준)
                first_date = df['review_date'].min()
                if pd.notna(first_date):
                    df['days_since_launch'] = (df['review_date'] - first_date).dt.days
                    
                    def get_lifecycle_stage(days):
                        if pd.isna(days):
                            return 'unknown'
                        elif days <= 30:
                            return '출시 1개월'
                        elif days <= 180:
                            return '1-6개월'
                        elif days <= 365:
                            return '6-12개월'
                        else:
                            return '1년 이상'
                    
                    df['lifecycle_stage'] = df['days_since_launch'].apply(get_lifecycle_stage)
        
        return df
    
    def _load_stopwords(self):
        """불용어 로딩"""
        basic_stopwords = [
            '것', '수', '있', '하', '되', '그', '이', '저', '때', '더', '또', '같', '좋', 
            '정말', '너무', '진짜', '완전', '그냥', '약간', '조금', '많이', '잘', '안',
            '하지만', '그런데', '그리고', '또한', '그래서', '따라서', '하면', '하니까',
            '입니다', '습니다', '해요', '이에요', '예요', '이죠', '네요', '어요', '재구매',
            '감사합니다', '잘쓸게요', '잘쓸께요', '같아요', "이거", "같이", "사용하기"
        ]
        
        try:
            with open(STOPWORDS_PATH, 'r', encoding='utf-8') as f:
                file_stopwords = [line.strip() for line in f if line.strip()]
                return set(basic_stopwords + file_stopwords)
        except FileNotFoundError:
            print(f"불용어 사전을 찾을 수 없음: {STOPWORDS_PATH}")
            return set(basic_stopwords)
    
    def get_stopwords(self):
        """불용어 목록 반환"""
        return self.stopwords

    def clean_and_save(self, df, channel_name, save_name=None):
        """전처리하고 CSV로 저장"""
        cleaned_df = self.clean_dataframe(df)
        
        if cleaned_df.empty:
            print("전처리 결과가 비어있어 저장하지 않습니다.")
            return cleaned_df
        
        # 저장 경로 설정
        channel_config = CHANNEL_CONFIGS[channel_name]
        processed_dir = channel_config['raw_data_path'].replace('raw_data', 'processed_data')
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        
        # 파일명 설정
        if save_name is None:
            if 'source_file' in cleaned_df.columns and not cleaned_df['source_file'].isna().all():
                # 원본 파일명 기반
                source_file = cleaned_df['source_file'].iloc[0]
                save_name = source_file.replace('_reviews.csv', '_processed.csv')
            else:
                # 기본 파일명
                save_name = f"{channel_name}_all_processed.csv"
        
        save_path = os.path.join(processed_dir, save_name)
        
        # CSV 저장
        cleaned_df.to_csv(save_path, index=False, encoding='utf-8')
        print(f"전처리 결과 저장: {save_path}")
        print(f"저장된 데이터: {len(cleaned_df)}개 리뷰, {len(cleaned_df.columns)}개 컬럼")
        
        return cleaned_df
    
    # 모든 csv 개별 저장
    def process_all_channel_files(self, channel_name):
        from data_loader_preprocessor import DataLoader
        
        loader = DataLoader(channel_name)
        available_files = loader.get_available_files()
        
        if not available_files:
            print(f"{channel_name} 채널에서 처리할 파일이 없습니다.")
            return
        
        print(f"{channel_name} 채널 전체 파일 전처리 시작: {len(available_files)}개 파일")
        
        success_count = 0
        for file_name in available_files:
            try:
                # 개별 파일 로딩
                df = loader.load_single_product(file_name)
                
                if df.empty:
                    continue
                
                # 전처리 및 저장
                processed_name = file_name.replace('_reviews.csv', '_processed.csv')
                self.clean_and_save(df, channel_name, processed_name)
                success_count += 1
                
            except Exception as e:
                print(f"파일 처리 실패 {file_name}: {e}")
        
        print(f"{channel_name} 채널 전처리 완료: {success_count}/{len(available_files)} 파일 성공")
        return success_count