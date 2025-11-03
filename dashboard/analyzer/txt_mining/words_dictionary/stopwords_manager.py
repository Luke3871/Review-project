"""
불용어 사전 관리 모듈
- 채널/플랫폼별 불용어 사전 분리
    - common -> 모든 플랫폼에 적용되는 기본적인 잡음 제거용 사전
    - _channelname -> 각 채널별 사전, 채널마다 특화된 잡음 제거용 사전
    - _brands -> 브랜드명, 화장품 시장 특성과 관련된 잡음 제거용 사전

- 여러 불용어 사전 로딩 및 union
- 이후 대시보드에 사전 관리 기능을 추가하여 실무자가 분석결과를 보고 불용어 사전을 관리하여 잡음을 제거할 수 있도록

stopwords_manager.py
- 불용어 사전 관리 모듈
- 기능:
    1. 불용어 txt 파일 로드
    2. 불용어 추가/삭제 (카테고리별)
    3. 수정 로그 기록
    4. 채널별 최종 stopwords 조합 반환
    5. UI용 카테고리 옵션 제공
"""

import datetime
import os
from pathlib import Path

# -------------------------------------------------------------------------
# 경로 설정
# -------------------------------------------------------------------------
BASE_PATH = Path(__file__).resolve().parent   # stopwords_manager.py 위치
STOPWORDS_DIR = BASE_PATH / "stopwords"       # stopwords txt 폴더
LOG_FILE = STOPWORDS_DIR / "stopwords_log.csv"

# -------------------------------------------------------------------------
# 공통 함수
# -------------------------------------------------------------------------
def load_stopwords(filename: str) -> set[str]:
    """특정 stopwords 파일 불러오기"""
    path = STOPWORDS_DIR / filename
    if not path.exists():
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_stopwords(filename: str, stopwords: set[str]):
    """stopwords 집합을 txt 파일로 저장"""
    path = STOPWORDS_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(stopwords)))

def log_action(word: str, action: str, user: str = "default", memo: str = "", filename: str = "unknown"):
    """불용어 추가/삭제 로그 기록"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = "word,action,user,timestamp,memo,filename\n"

    # 로그 파일 없으면 헤더 포함 생성
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(header)

    # 행 추가
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{word},{action},{user},{now},{memo},{filename}\n")

# -------------------------------------------------------------------------
# 불용어 추가/삭제 (카테고리 기반)
# -------------------------------------------------------------------------
def add_stopword(category: str, word: str, user="default", memo=""):
    """
    불용어 추가

    Args:
        category: 'common' | 'brands' | 'products' | 'ingredients' | 'channels' | 'daiso' | 'oliveyoung' | 'coupang'
        word: 추가할 불용어
        user: 사용자명
        memo: 메모
    """
    filename = f"stopwords_{category}.txt"
    stopwords = load_stopwords(filename)

    if word not in stopwords:
        stopwords.add(word)
        save_stopwords(filename, stopwords)
        log_action(word, "add", user, memo, filename)

def remove_stopword(category: str, word: str, user="default", memo=""):
    filename = f"stopwords_{category}.txt"
    stopwords = load_stopwords(filename)

    if word in stopwords:
        stopwords.remove(word)
        save_stopwords(filename, stopwords)
        log_action(word, "remove", user, memo, filename)

# -------------------------------------------------------------------------
# 채널별 stopwords 조합
# -------------------------------------------------------------------------
def get_stopwords_for_channel(channel: str) -> set[str]:
    """
    채널별 최종 stopwords 반환
    - common.txt : 기본 공통 불용어 (구 origin.txt)
    - brands.txt : 브랜드명
    - products.txt : 제품명 관련
    - ingredients.txt : 성분명
    - channels.txt : 채널명
    - 각 채널별 전용 txt : daiso, oliveyoung, coupang
    """
    # 공통 불용어 로드 (backward compatibility: origin.txt도 지원)
    common = load_stopwords("stopwords_common.txt")
    if not common:  # common.txt가 없으면 origin.txt 시도
        common = load_stopwords("stopwords_origin.txt")

    brands = load_stopwords("stopwords_brands.txt")
    products = load_stopwords("stopwords_products.txt")
    ingredients = load_stopwords("stopwords_ingredients.txt")
    channels = load_stopwords("stopwords_channels.txt")

    # 기본 공통 불용어 합집합
    all_common = common.union(brands, products, ingredients, channels)

    # 채널별 추가 불용어
    if channel == "daiso":
        daiso = load_stopwords("stopwords_daiso.txt")
        return all_common.union(daiso)

    elif channel == "oliveyoung":
        olive = load_stopwords("stopwords_oliveyoung.txt")
        return all_common.union(olive)

    elif channel == "coupang":
        coupang = load_stopwords("stopwords_coupang.txt")
        return all_common.union(coupang)

    else:
        # 기본값: 공통 불용어만
        return all_common

# -------------------------------------------------------------------------
# UI용 카테고리 옵션
# -------------------------------------------------------------------------
def get_category_options(channel: str = None) -> dict[str, str]:
    """
    불용어 카테고리 옵션 반환 (UI용)

    Args:
        channel: 현재 채널명 (daiso, coupang, oliveyoung 등)

    Returns:
        {카테고리_키: 표시_텍스트} 딕셔너리
    """
    # 공통 카테고리
    options = {
        "common": "🌐 공통 - 조사, 수량 등 기본 불용어",
        "brands": "🏷️ 브랜드 - 브랜드명",
        "products": "📦 제품 관련 - 제품 유형, 색상 등",
        "ingredients": "🧪 성분 - 성분명 (레티놀, 시카 등)",
        "channels": "🏪 채널 - 채널명",
    }

    # 채널별 카테고리 (현재 채널을 맨 앞에 추가)
    channel_specific = {
        "daiso": "🛒 다이소 전용",
        "coupang": "📱 쿠팡 전용",
        "oliveyoung": "💄 올리브영 전용"
    }

    if channel and channel.lower() in channel_specific:
        channel_key = channel.lower()
        # 현재 채널을 맨 앞에 추가
        options = {
            channel_key: f"⭐ {channel_specific[channel_key]} (현재 채널)",
            **options
        }

    return options
