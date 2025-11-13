#//==============================================================================//#
"""
전처리 모듈 설정 파일

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
from pathlib import Path

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"

#//==============================================================================//#
# 채널별 데이터 경로 설정
#//==============================================================================//#
CHANNEL_CONFIGS = {
    'daiso': {
        'name': '다이소',
        'raw_data_path': str(DATA_ROOT / 'data_daiso' / 'raw_data' / 'reviews_daiso'),
        'file_pattern': '*_reviews.csv',
        'encoding': ['utf-8', 'cp949']
    },
    'coupang': {
        'name': '쿠팡',
        'raw_data_path': str(DATA_ROOT / 'data_coupang' / 'raw_data' / 'reviews_coupang'),
        'file_pattern': '*_reviews.csv',
        'encoding': ['utf-8', 'cp949']
    },
    'oliveyoung': {
        'name': '올리브영',
        'raw_data_path': str(DATA_ROOT / 'data_oliveyoung' / 'raw_data' / 'reviews_oliveyoung'),
        'file_pattern': '*_reviews.csv',
        'encoding': ['utf-8', 'cp949']
    }
}

#//==============================================================================//#
# 전처리 기본 설정
#//==============================================================================//#
PREPROCESSING_CONFIG = {
    'min_text_length': 3,
    'long_review_threshold': 100,
    'positive_rating_threshold': 4,
    'negative_rating_threshold': 3,
    'max_text_length': 5000, 
    'remove_duplicates': True,
    'clean_html': True,
    'clean_urls': True
}

#//==============================================================================//#
# stopwords 사전 경로
#//==============================================================================//#
STOPWORDS_PATH = 'analyzer/txt_mining/words_dictionary/stopwords/stopwords_origin.txt'


#//==============================================================================//#
# 신조어 사전 경로
#//==============================================================================//#
NEWWORDS_PATH = "analyzer/txt_mining/words_dictionary/newwords/newwords"


#//==============================================================================//#
# LG 생활건강 브랜드 리스트 (dashboard_config.py와 동일한 107개)
#//==============================================================================//#
LG_BRANDS = [
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