#//==============================================================================//#
"""
validators.py
데이터 검증 및 전처리 유틸리티

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
from typing import List
from config import COMMON_REQUIRED_COLUMNS

#//==============================================================================//#
# 검증 함수
#//==============================================================================//#

def validate_common_columns(df: pd.DataFrame) -> None:
    """
    공통 필수 컬럼 검증
    
    Args:
        df: 검증할 DataFrame
    
    Raises:
        ValueError: 공통 필수 컬럼 누락 시
    """
    
    missing = [col for col in COMMON_REQUIRED_COLUMNS if col not in df.columns]
    
    if missing:
        raise ValueError(
            f"공통 필수 컬럼 누락: {missing}\n"
            f"필요한 컬럼: {COMMON_REQUIRED_COLUMNS}"
        )


def validate_specific_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    특정 함수에서 필요한 추가 컬럼 검증
    
    Args:
        df: 검증할 DataFrame
        required_cols: 필요한 컬럼 리스트
    
    Raises:
        ValueError: 필수 컬럼 누락 시
    """
    
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrame 전처리
    - rating을 numeric으로 (필요시)
    - review_date를 datetime으로 (필요시)
    - 결측치 제거
    
    Args:
        df: 원본 DataFrame
    
    Returns:
        전처리된 DataFrame
    """
    
    df = df.copy()
    
    # DB에서 온 경우 이미 올바른 타입
    # CSV 등에서 온 경우를 위해 안전하게 처리
    if df['rating'].dtype == 'object':
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    
    if df['review_date'].dtype == 'object':
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
    
    # 공통 필수 컬럼 결측치 제거
    df = df.dropna(subset=COMMON_REQUIRED_COLUMNS)
    
    # 빈 텍스트 제거
    df = df[df['review_text'].str.strip() != '']
    
    return df