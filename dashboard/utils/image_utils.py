#//==============================================================================//#
"""
utils/image_utils.py
제품 이미지 로딩 유틸리티

last_updated: 2025.10.25
"""
#//==============================================================================//#

import os
import glob
from pathlib import Path
import streamlit as st

# 이미지 경로 설정
IMAGE_BASE_DIR = Path(r"C:\ReviewFW_LG_hnh\data")

IMAGE_PATHS = {
    'Daiso': IMAGE_BASE_DIR / "data_daiso" / "raw_data" / "products_image_daiso",
    'OliveYoung': IMAGE_BASE_DIR / "data_oliveyoung" / "raw_data" / "reviews_image_oliveyoung"
}


def get_product_image_by_rank(channel, rank):
    """
    랭크로 제품 이미지 경로 가져오기
    
    Args:
        channel: 'OliveYoung' or 'Daiso'
        rank: 1, 2, 3...
    
    Returns:
        str or None: 이미지 경로 (없으면 None)
    """
    
    if channel not in IMAGE_PATHS:
        return None
    
    base_path = IMAGE_PATHS[channel]
    
    if not base_path.exists():
        return None
    
    rank_str = f"{rank:03d}"  # 001, 002, 003
    
    # 채널별 파일명 패턴 (하드코딩)
    if channel == 'OliveYoung':
        # oliveyoung_makeup_001_product_main.jpg
        # oliveyoung_skincare_001_product_main.jpg (등)
        pattern = f"oliveyoung_*_{rank_str}_product_main.*"
        
    elif channel == 'Daiso':
        # makeup_SALES_rank001_1061379.jpg
        pattern = f"*_SALES_rank{rank_str}_*.*"
    
    else:
        return None
    
    # 패턴에 맞는 파일 찾기
    matches = glob.glob(str(base_path / pattern))
    
    if matches:
        return matches[0]  # 첫 번째 매치 반환
    
    return None


def display_product_image(image_path, width=None, caption=None):
    """
    Streamlit에서 이미지 표시 (없으면 placeholder)
    
    Args:
        image_path: 이미지 경로
        width: 이미지 너비
        caption: 캡션
    
    Returns:
        bool: 이미지 표시 성공 여부
    """
    
    if image_path and os.path.exists(image_path):
        st.image(image_path, width=width, caption=caption, use_column_width=True if not width else False)
        return True
    else:
        # 이미지 없음 placeholder
        st.markdown(
            """
            <div style="
                background-color: #f0f0f0; 
                height: 200px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                border-radius: 8px;
                color: #999;
            ">
                📦 이미지 없음
            </div>
            """,
            unsafe_allow_html=True
        )
        return False