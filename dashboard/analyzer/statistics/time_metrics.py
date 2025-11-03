#//==============================================================================//#
"""
time_metrics.py

 - 시계열 계산
    - 일
    - 주
    - 월


last_updated : 2025.10.16
"""
#//==============================================================================//#
import pandas as pd


def calculate_time_series(df, time_unit='M'):
    """
    시계열 데이터 계산
    
    Args:
        df: DataFrame
        time_unit: 'D' (일별), 'W' (주별), 'M' (월별)
    
    Returns:
        Series: 기간별 리뷰 수
    """
    if 'review_date' not in df.columns:
        return None
    
    df_copy = df.copy()
    df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
    df_copy = df_copy.dropna(subset=['review_date'])
    
    if df_copy.empty:
        return None
    
    # 시간 단위별 그룹화
    if time_unit == 'D':
        df_copy['period'] = df_copy['review_date'].dt.date
    elif time_unit == 'W':
        df_copy['period'] = df_copy['review_date'].dt.to_period('W')
    else:  # 'M'
        df_copy['period'] = df_copy['review_date'].dt.to_period('M')
    
    period_counts = df_copy.groupby('period').size()
    
    return period_counts