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