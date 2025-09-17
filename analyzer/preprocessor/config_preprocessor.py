#//==============================================================================//#
"""
전처리 모듈 설정 파일

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#



#//==============================================================================//#
# 채널별 데이터 경로 설정
#//==============================================================================//#
CHANNEL_CONFIGS = {
    'daiso': {
        'name': '다이소',
        'raw_data_path': r'C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data\data_daiso\raw_data\reviews_daiso',
        'file_pattern': '*_reviews.csv',
        'encoding': ['utf-8', 'cp949']
    },
    'coupang': {
        'name': '쿠팡',
        'raw_data_path': '../data/data_coupang/raw_data/',
        'file_pattern': '*_reviews.csv',
        'encoding': ['utf-8', 'cp949']
    },
    'oliveyoung': {
        'name': '올리브영',
        'raw_data_path': '../data/data_oliveyoung/raw_data/',
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