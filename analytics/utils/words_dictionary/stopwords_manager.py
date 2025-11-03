"""
불용어 사전 관리 모듈
- 채널/플랫폼별 불용어 사전 분리
    - origin -> 모든 플랫폼에 적용되는 기본적인 잡음 제거용 사전
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
    category: 'origin' | 'brands' | 'daiso' | 'oliveyoung' | 'coupang' 
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
    - origin.txt : 모든 채널 공통
    - brands.txt : 브랜드명 제거
    - 각 채널별 전용 txt : daiso, oliveyoung, coupang ...
    """
    origin = load_stopwords("stopwords_origin.txt")
    cosmetic = load_stopwords("stopwords_cosmetic.txt")
    brands = load_stopwords("stopwords_brands.txt")

    if channel == "daiso":
        daiso = load_stopwords("stopwords_daiso.txt")
        cosmetic = load_stopwords("stopwords_cosmetic.txt")
        return origin.union(brands, daiso, cosmetic)

    elif channel == "oliveyoung":
        olive = load_stopwords("stopwords_oliveyoung.txt")
        cosmetic = load_stopwords("stopwords_cosmetic.txt")
        return origin.union(brands, olive, cosmetic)

    elif channel == "coupang":
        coupang = load_stopwords("stopwords_coupang.txt")
        cosmetic = load_stopwords("stopwords_cosmetic.txt")
        return origin.union(brands, coupang, cosmetic)

    else:
        # 기본값: origin + brands
        return origin.union(brands)
