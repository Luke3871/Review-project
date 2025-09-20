# analyzer/preprocessor/raw_data_preprocessor.py
#//==============================================================================//#
"""
리뷰 데이터 전처리 모듈

기능:
- 결측치/중복 제거
- 별점 숫자화
- 텍스트 길이, 단어 수 등 통계치 추가
- 날짜 처리 (연/월/일, PLC 등)
- processed_data 폴더에 저장

last_updated : 2025.09.21
"""
#//==============================================================================//#

import pandas as pd
import numpy as np
import os
from pathlib import Path
from config_preprocessor import PREPROCESSING_CONFIG, CHANNEL_CONFIGS


class DataPreprocessor:

    def __init__(self):
        self.config = PREPROCESSING_CONFIG

    def clean_dataframe(self, df):
        if df.empty:
            return df

        print(f"전처리 시작: {len(df)}개 리뷰")

        df = self._clean_basic_data(df)
        df = self._extract_numeric_rating(df)
        df = self._calculate_text_metrics(df)
        df = self._process_dates(df)

        print(f"전처리 완료: {len(df)}개 리뷰")

        return df

    # 1. 기본 데이터 정리
    def _clean_basic_data(self, df):
        original_count = len(df)

        # 필수 컬럼 확인
        required_columns = ['product_name', 'review_text']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"⚠️ 필수 컬럼 누락: {missing_columns}")
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

        print(f"✅ 기본 데이터 정리: {original_count} → {len(df)}개")
        return df

    # 2. 별점 정리
    def _extract_numeric_rating(self, df):
        """별점 정리"""
        def extract_rating(rating_value):
            if pd.isna(rating_value):
                return np.nan

            rating_str = str(rating_value).strip()

            if '점' in rating_str:
                try:
                    numeric_part = rating_str.replace('점', '').strip()
                    return float(numeric_part)
                except Exception as e:
                    print(f"DEBUG: '점' 처리 실패: {e}")
                    return np.nan
            elif '★' in rating_str:
                return float(rating_str.count('★'))
            else:
                try:
                    rating_num = float(rating_str)
                    return rating_num if 1 <= rating_num <= 5 else np.nan
                except:
                    print(f"DEBUG: 숫자 변환 실패: '{rating_str}'")
                    return np.nan

        return df

    # 3. 텍스트 메트릭
    def _calculate_text_metrics(self, df):
        if 'review_text' in df.columns:
            df['text_length'] = df['review_text'].str.len()
            df['word_count'] = df['review_text'].str.split().str.len()
            df['is_long_review'] = df['text_length'] >= self.config['long_review_threshold']
            df['is_short_review'] = df['text_length'] <= 20
        return df

    # 4. 날짜 처리
    def _process_dates(self, df):
        """날짜 처리 - 완전히 다시 작성"""
        if 'review_date' in df.columns:
            # 날짜 변환 전에 원본 데이터 확인
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
            valid_dates = df['review_date'].notna()

            if valid_dates.any():
                df.loc[valid_dates, 'review_year'] = df.loc[valid_dates, 'review_date'].dt.year
                df.loc[valid_dates, 'review_month'] = df.loc[valid_dates, 'review_date'].dt.month
                df.loc[valid_dates, 'review_day'] = df.loc[valid_dates, 'review_date'].dt.day
                df.loc[valid_dates, 'review_weekday'] = df.loc[valid_dates, 'review_date'].dt.dayofweek
                df.loc[valid_dates, 'review_month_str'] = df.loc[valid_dates, 'review_date'].dt.strftime('%Y-%m')

        return df
    # 5. 저장
    def clean_and_save(self, df, channel_name, file_name):
        """전처리하고 CSV 저장 - 인코딩 문제 해결"""
        cleaned_df = self.clean_dataframe(df)

        if cleaned_df.empty:
            print("전처리 결과가 비어있어 저장하지 않습니다.")
            return cleaned_df

        # 프로젝트 루트 기준
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        DATA_ROOT = PROJECT_ROOT / "data"

        # 저장 폴더
        processed_dir = DATA_ROOT / f"data_{channel_name}" / "processed_data" / f"reviews_{channel_name}"
        processed_dir.mkdir(parents=True, exist_ok=True)

        # 파일명 변환: _reviews.csv → _processed.csv
        save_name = file_name.replace("_reviews.csv", "_processed.csv")
        save_path = processed_dir / save_name

        # CSV 저장 - 인코딩과 구분자 명시
        cleaned_df.to_csv(
            save_path, 
            index=False, 
            encoding="utf-8-sig",  # BOM 포함 UTF-8
            sep=',',               # 구분자 명시
            escapechar='\\',       # 이스케이프 문자
            quoting=1              # 모든 필드를 따옴표로 감싸기
        )
        
        print(f"전처리 결과 저장: {save_path}")
        print(f"저장된 데이터: {len(cleaned_df)}개 리뷰, {len(cleaned_df.columns)}개 컬럼")

        return cleaned_df

    def process_all_channel_files(self, channel_name):
        """채널의 모든 raw_data 파일들을 개별 처리해서 processed_data에 저장"""
        
        import glob
        import os
        
        print(f"{channel_name} 채널 전처리 시작")
        
        # 프로젝트 루트 기준 경로
        PROJECT_ROOT = Path(__file__).resolve().parents[2]
        raw_data_dir = PROJECT_ROOT / "data" / f"data_{channel_name}" / "raw_data" / f"reviews_{channel_name}"
        
        # _reviews.csv 파일들 찾기
        pattern = str(raw_data_dir / "*_reviews.csv")
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            print(f"{raw_data_dir}에서 *_reviews.csv 파일을 찾을 수 없습니다")
            return
        
        print(f"발견된 파일: {len(csv_files)}개")
        
        # 각 파일 처리
        success_count = 0
        for file_path in csv_files:
            try:
                file_name = os.path.basename(file_path)
                print(f"처리 중: {file_name}")
                
                # CSV 파일 로딩 - 여러 인코딩 시도
                df = None
                for encoding in ['utf-8', 'cp949', 'euc-kr']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    print(f"인코딩 실패: {file_name}")
                    continue
                    
                if df.empty:
                    print(f"빈 파일 건너뜀: {file_name}")
                    continue
                
                # 전처리 후 저장
                cleaned_df = self.clean_and_save(df, channel_name, file_name)
                
                if not cleaned_df.empty:
                    success_count += 1
                    print(f"성공: {file_name}")
                
            except Exception as e:
                print(f"에러: {file_name} - {str(e)}")
                continue
        
        print(f"{channel_name} 채널 완료: {success_count}개 파일 처리됨")