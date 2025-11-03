#//==============================================================================//#
"""
텍스트 마이닝 모듈 init.py
 
last_updated : 2025.10.25
"""
#//==============================================================================//#

# 토크나이저
from .tokenizer import (
    my_beauty_korean_tokenizer,
    get_tokenizer_for_channel,
    get_tfidf_vectorizer,
    get_count_vectorizer,
)

# 키워드 분석
from .keyword_analyzer import (
    extract_keywords_tfidf,
    calculate_keyword_matrix,
    get_products_by_keyword,
    calculate_cooccurrence,
    calculate_keyword_trend,
)

# 불용어 관리
from .words_dictionary.stopwords_manager import (
    add_stopword,
    remove_stopword,
    get_stopwords_for_channel,
    get_category_options,
    load_stopwords,
)

# 시각화
from .txt_visualizations import (  # ← 여기!
    create_keyword_wordcloud,
    create_keyword_table,
    create_keyword_bar_chart,
    create_channel_keyword_comparison,
    create_keyword_trend_line_chart,
    create_cooccurrence_bar_chart,
    create_product_keyword_table,
    create_keyword_trend_chart,
)

__all__ = [
    # 토크나이저
    'my_beauty_korean_tokenizer',
    'get_tokenizer_for_channel',
    'get_tfidf_vectorizer',
    'get_count_vectorizer',
    
    # 키워드 분석
    'extract_keywords_tfidf',
    'calculate_keyword_matrix',
    'get_products_by_keyword',
    'calculate_cooccurrence',
    'calculate_keyword_trend',
    
    # 불용어 관리
    'add_stopword',
    'remove_stopword',
    'get_stopwords_for_channel',
    'get_category_options',
    'load_stopwords',

    # 시각화
    'create_keyword_wordcloud',
    'create_keyword_table',
    'create_keyword_bar_chart',
    'create_channel_keyword_comparison',
    'create_keyword_trend_line_chart',
    'create_cooccurrence_bar_chart',
    'create_product_keyword_table',
    'create_keyword_trend_chart',
]