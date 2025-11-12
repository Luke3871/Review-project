#//==============================================================================//#
"""
dashboard_config.py
streamlit 기반 대시보드 기본 설정 파일
 - LG 생활건강 브랜드 제품 하이라이트

last_updated : 2025.10.23
"""
#//==============================================================================//#
import streamlit as st  # 캐싱을 위해 추가
import os
import pandas as pd
import psycopg2
from pathlib import Path
from datetime import datetime, timedelta

# 기본 경로 설정 (상대 경로 사용)
BASE_DIR = Path(__file__).parent.resolve()
ASSETS_DIR = BASE_DIR / "assets"
HISTORY_DIR = BASE_DIR / "user_histories"

# 로그인 정보 (환경변수 우선, 없으면 기본값)
def _load_users():
    """환경변수에서 사용자 정보 로드"""
    users_env = os.getenv('DASHBOARD_USERS', '')
    if users_env:
        users = {}
        for user_pair in users_env.split(','):
            if ':' in user_pair:
                username, password = user_pair.split(':', 1)
                users[username.strip()] = password.strip()
        return users
    # 기본값
    return {
        "admin": "123",
        "임현석": "1234",
        "박지연": "1234"
    }

USERS = _load_users()

PERIOD_OPTIONS = [
    "전체",
    "최근 1개월",
    "최근 3개월", 
    "최근 6개월",
    "최근 1년"
]

# 디렉토리 생성
for dir_path in [ASSETS_DIR, HISTORY_DIR]:
    dir_path.mkdir(exist_ok=True)


# PostgreSQL 연결 (환경변수 우선, 없으면 기본값)
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'cosmetic_reviews'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432))
}

# LG생활건강 브랜드 리스트
LGHH_BRANDS = [
    '후',
    'The history of 후',
    '오휘',
    'SU:M37°',
    '숨',
    '빌리프',
    '프리메라',
    '더 사가 오브 수',
    '이자녹스',
    '수려한',
    '라끄베르',
    '코드글로컬러',
    'VDL',
    'VDIVOV',
    '클리오',
    'CNP',
    '차앤박',
    'CNP차앤박',
    'CNP Laboratory',
    '닥터지',
    '닥터벨머',
    '케어존',
    '피지오겔',
    '보닌',
    '더페이스샵',
    '네이처컬렉션',
    '비욘드',
    '생활정원',
    'fmgt',
    '예화담',
    '엘라스틴',
    '리엔',
    '오가니스트',
    '피토더마',
    '실크테라피',
    '닥터그루트',
    '온더바디',
    '벨먼',
    '드봉',
    '세이',
    '바이 오디-티디'
]


# ========== 데이터 로딩 (캐싱) ==========

@st.cache_data(ttl=3600, show_spinner=False)
def load_all_data():
    """전체 데이터 한 번만 로드 (1시간 캐시)
    
    Returns:
        DataFrame: 전체 리뷰 데이터
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        query = """
            SELECT 
                review_id,
                channel,
                brand,
                product_name,
                category,
                selected_option,
                review_text,
                review_clean,
                review_date,
                rating,
                helpful_count,
                product_price_sale,
                reviewer_skin_features,
                ranking
            FROM reviews 
            WHERE brand != 'Unknown'
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # 날짜 변환
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        
        # 평점 변환
        if 'rating' in df.columns:
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
        
        print(f"전체 데이터 로드 완료: {len(df):,}개")
        return df
        
    except Exception as e:
        print(f"DB 로드 에러: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def load_filtered_data(channel=None, brand=None, category=None, product=None, option=None, period=None):
    """
    캐시된 전체 데이터에서 필터링 (메모리 기반)
    
    Args:
        channel: 채널명 ("전체" 또는 특정 채널)
        brand: 브랜드명
        category: 카테고리
        product: 제품명
        option: selected_option
        period: 기간 ("전체", "최근 3개월" 등)
    
    Returns:
        DataFrame
    """
    # 캐시된 데이터 가져오기
    df = load_all_data()
    
    if df.empty:
        return df
    
    # 메모리에서 필터링
    if channel and channel != "전체":
        df = df[df['channel'] == channel]
    
    if brand and brand != "전체":
        df = df[df['brand'] == brand]
    
    if category and category != "전체":
        df = df[df['category'] == category]
    
    if product and product != "전체":
        df = df[df['product_name'] == product]
    
    if option and option != "전체":
        df = df[df['selected_option'] == option]
    
    # 기간 필터
    if period and period != "전체":
        period_map = {
            "최근 1개월": 30,
            "최근 3개월": 90,
            "최근 6개월": 180,
            "최근 1년": 365
        }
        if period in period_map:
            days = period_map[period]
            cutoff_date = datetime.now() - timedelta(days=days)
            df = df[df['review_date'] >= cutoff_date]
    
    print(f"필터링 완료: {len(df):,}개")
    return df


# ========== 계층 구조 캐싱 (한 번만 계산) ==========

@st.cache_data(ttl=3600, show_spinner=False)
def get_data_hierarchy():
    """전체 데이터 계층 구조 캐싱 (채널 > 브랜드 > 제품 > 옵션)
    
    Returns:
        dict: {
            'Coupang': {
                'VT': {
                    '시카크림': ['50ml', '100ml'],
                    ...
                },
                ...
            },
            ...
        }
    """
    print("[DEBUG] 계층 구조 생성 시작...")
    import time
    start = time.time()
    
    df = load_all_data()
    
    if df.empty:
        return {}
    
    hierarchy = {}
    
    # 채널별
    for channel in df['channel'].dropna().unique():
        hierarchy[channel] = {}
        channel_df = df[df['channel'] == channel]
        
        # 브랜드별
        for brand in channel_df['brand'].dropna().unique():
            hierarchy[channel][brand] = {}
            brand_df = channel_df[channel_df['brand'] == brand]
            
            # 제품별
            for product in brand_df['product_name'].dropna().unique():
                product_df = brand_df[brand_df['product_name'] == product]
                
                # 옵션 리스트
                options = product_df['selected_option'].dropna()
                options = options[options != ''].unique().tolist()
                
                hierarchy[channel][brand][product] = options
    
    print(f"[DEBUG] 계층 구조 생성 완료: {time.time() - start:.2f}초")
    return hierarchy


# ========== 필터 옵션 가져오기 (계층 구조 사용) ==========

def get_available_channels():
    """사용 가능한 채널 목록 (올리브영 우선)"""
    hierarchy = get_data_hierarchy()
    all_channels = list(hierarchy.keys())

    # 원하는 순서 지정 (올리브영 제일 앞)
    preferred_order = ['OliveYoung', 'Coupang', 'Daiso']

    # preferred_order에 있는 것 먼저, 나머지는 알파벳 순
    ordered = []
    for channel in preferred_order:
        if channel in all_channels:
            ordered.append(channel)

    # 나머지 채널 추가 (있을 경우)
    for channel in sorted(all_channels):
        if channel not in ordered:
            ordered.append(channel)

    return ordered


def get_brand_list(channel=None):
    """브랜드 목록 조회
    
    Args:
        channel: 채널명 (None이면 전체)
    """
    hierarchy = get_data_hierarchy()
    
    if not channel or channel == "전체":
        # 전체 브랜드
        brands = set()
        for channel_data in hierarchy.values():
            brands.update(channel_data.keys())
        return sorted(brands)
    
    # 특정 채널의 브랜드
    return sorted(hierarchy.get(channel, {}).keys())


def get_category_list(channel=None):
    """카테고리 목록 조회
    
    Note: 카테고리는 계층 구조에 없으므로 기존 방식 유지
    """
    df = load_all_data()
    
    if df.empty or 'category' not in df.columns:
        return ["skincare", "makeup"]
    
    if channel and channel != "전체":
        df = df[df['channel'] == channel]
    
    return sorted(df['category'].dropna().unique().tolist())


def get_product_list(channel=None, brand=None, category=None):
    """제품 목록 조회
    
    Args:
        channel: 채널명
        brand: 브랜드명
        category: 카테고리 (계층 구조에 없으므로 별도 필터링)
    """
    hierarchy = get_data_hierarchy()
    
    products = set()
    
    if not channel or channel == "전체":
        # 전체 채널
        if not brand or brand == "전체":
            # 전체 브랜드
            for channel_data in hierarchy.values():
                for brand_data in channel_data.values():
                    products.update(brand_data.keys())
        else:
            # 특정 브랜드
            for channel_data in hierarchy.values():
                if brand in channel_data:
                    products.update(channel_data[brand].keys())
    else:
        # 특정 채널
        if not brand or brand == "전체":
            # 전체 브랜드
            channel_data = hierarchy.get(channel, {})
            for brand_data in channel_data.values():
                products.update(brand_data.keys())
        else:
            # 특정 브랜드
            channel_data = hierarchy.get(channel, {})
            products.update(channel_data.get(brand, {}).keys())
    
    # 카테고리 필터링 (별도로 처리)
    if category and category != "전체":
        df = load_all_data()
        
        # 기존 필터 적용
        if channel and channel != "전체":
            df = df[df['channel'] == channel]
        if brand and brand != "전체":
            df = df[df['brand'] == brand]
        
        df = df[df['category'] == category]
        products = set(df['product_name'].dropna().unique())
    
    return sorted(products)[:1000]  # 최대 1000개


def get_selected_options(channel=None, brand=None, category=None, product=None):
    """기획 옵션 목록 조회
    
    Args:
        channel: 채널명
        brand: 브랜드명
        category: 카테고리 (계층 구조에 없으므로 별도 필터링)
        product: 제품명
    """
    hierarchy = get_data_hierarchy()
    
    options = set()
    
    if product and product != "전체":
        # 특정 제품의 옵션
        if channel and channel != "전체" and brand and brand != "전체":
            # 채널 + 브랜드 지정
            options.update(hierarchy.get(channel, {}).get(brand, {}).get(product, []))
        else:
            # 전체에서 해당 제품 찾기
            for channel_data in hierarchy.values():
                for brand_data in channel_data.values():
                    if product in brand_data:
                        options.update(brand_data[product])
    else:
        # 전체 옵션
        if channel and channel != "전체":
            if brand and brand != "전체":
                # 특정 채널 + 브랜드의 모든 옵션
                brand_data = hierarchy.get(channel, {}).get(brand, {})
                for product_options in brand_data.values():
                    options.update(product_options)
            else:
                # 특정 채널의 모든 옵션
                channel_data = hierarchy.get(channel, {})
                for brand_data in channel_data.values():
                    for product_options in brand_data.values():
                        options.update(product_options)
        else:
            # 전체 옵션
            for channel_data in hierarchy.values():
                for brand_data in channel_data.values():
                    for product_options in brand_data.values():
                        options.update(product_options)
    
    # 카테고리 필터링 (별도로 처리)
    if category and category != "전체":
        df = load_all_data()
        
        if channel and channel != "전체":
            df = df[df['channel'] == channel]
        if brand and brand != "전체":
            df = df[df['brand'] == brand]
        if product and product != "전체":
            df = df[df['product_name'] == product]
        
        df = df[df['category'] == category]
        options = set(df['selected_option'].dropna())
        options = {opt for opt in options if opt != ''}
    
    return sorted(options)[:500]  # 최대 500개


# ========== 호환성 유지: 기존 함수 ==========

def load_channel_data_from_db(channel):
    """
    PostgreSQL에서 채널별 데이터 로드 (호환성 유지용)
    가능하면 load_filtered_data() 사용 권장
    
    Args:
        channel: "Coupang", "OliveYoung" 등
    
    Returns:
        pandas DataFrame
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        if channel == "전체":
            query = """
                SELECT * FROM reviews 
                WHERE brand != 'Unknown'
                ORDER BY review_date DESC
            """
            df = pd.read_sql(query, conn)
        else:
            query = """
                SELECT * FROM reviews 
                WHERE channel = %s 
                AND brand != 'Unknown'
                ORDER BY review_date DESC
            """
            df = pd.read_sql(query, conn, params=(channel,))
        
        conn.close()
        
        # 날짜 변환
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        
        # rating을 숫자로 변환
        if 'rating' in df.columns:
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
        
        print(f"{channel} 데이터 로드 완료: {len(df):,}개")
        return df
        
    except Exception as e:
        print(f"DB 로드 에러: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


# ========== 유틸리티 함수 ==========

def is_lghh_product(brand):
    """LG생건 제품인지 확인"""
    return brand in LGHH_BRANDS


def clear_data_cache():
    """데이터 캐시 초기화"""
    st.cache_data.clear()
    print("캐시 초기화 완료")