"""
설정 파일
"""

import os
import glob
import pandas as pd
from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\dashboard")
DATA_BASE_DIR = Path(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data")
ASSETS_DIR = BASE_DIR / "assets" 
HISTORY_DIR = BASE_DIR / "user_histories"

# 데이터 파일 경로
DATA_PATHS = {
    "다이소": DATA_BASE_DIR / "data_daiso" / "processed_data" / "reviews_daiso",
    "올리브영": DATA_BASE_DIR / "data_oliveyoung" / "processed_data" / "reviews_oliveyoung",
    "쿠팡": DATA_BASE_DIR / "data_coupang" / "processed_data" / "reviews_coupang",
}


# 로그인 정보
USERS = {
    "admin": "123",
    "임현석": "1234",
    "박지연": "1234"
}

# 분석 옵션
CHANNELS = [
    "다이소",
    "올리브영",
    "쿠팡", 
    "화해",
    "글로우픽",
    "이마트"
]

CATEGORIES = [
    "skincare",
    "makeup",
]

SORT_OPTIONS = [
    "판매순",
    "좋아요순",
    "리뷰많은순",
]

PERIOD_OPTIONS = [
    "최근 1개월",
    "최근 3개월", 
    "최근 6개월",
    "최근 1년",
    "전체"
]


for dir_path in [ASSETS_DIR, HISTORY_DIR]:
    dir_path.mkdir(exist_ok=True)

def get_product_files(channel, category):
    """채널과 카테고리에 따른 제품 파일 목록 반환"""
    if channel not in DATA_PATHS:
        return []
    
    data_path = DATA_PATHS[channel]
    pattern = str(data_path / f"{category.lower()}_*.csv")
    files = glob.glob(pattern)
    
    # 파일명에서 제품명 추출
    product_names = []
    for file in files:
        filename = Path(file).stem
        # 예: makeup_LIKE_[01 밀키 페어리]프릴루드 딘토... -> [01 밀키 페어리]프릴루드 딘토...
        product_name = filename.replace(f"{category.lower()}_LIKE_", "").replace("_processed", "")
        product_names.append(product_name)
    
    return sorted(product_names)

def get_file_path(channel, category, product_name):
    """특정 제품의 파일 경로 반환"""
    if channel not in DATA_PATHS:
        return None
    
    data_path = DATA_PATHS[channel]
    filename = f"{category.lower()}_LIKE_{product_name}_processed.csv"
    file_path = data_path / filename
    
    if file_path.exists():
        return file_path
    return None

def load_product_data(channel, category, product_name):
    """제품 데이터 로드"""
    file_path = get_file_path(channel, category, product_name)
    if file_path and file_path.exists():
        return pd.read_csv(file_path)
    return None

def load_channel_data(channel):
    """특정 채널의 모든 데이터 로드"""
    if channel not in DATA_PATHS:
        return pd.DataFrame()
    
    data_path = DATA_PATHS[channel]
    csv_files = glob.glob(str(data_path / "*.csv"))
    
    all_reviews = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            df['channel'] = channel
            all_reviews.append(df)
        except:
            try:
                df = pd.read_csv(file, encoding='cp949')
                df['channel'] = channel
                all_reviews.append(df)
            except:
                continue
    
    if all_reviews:
        df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        return df
    return pd.DataFrame()