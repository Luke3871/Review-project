#//==============================================================================//#
"""
Customized Tokenizer
- kiwi 형태소 분석기 사용
- Konlpy 형태소 분석기 사용
- TF-IDF / Count parameter 조절하여 사용 하도록 세팅
- Stopwords 따로 정리

last_updated : 2025.09.20
"""
#//==============================================================================//#

#//==============================================================================//#
# Library Import
#//==============================================================================//#
import sys
import os

# analytics 폴더 고정
current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from pathlib import Path
import re
import pandas as pd
from kiwipiepy import Kiwi
from utils.words_dictionary.stopwords_manager import get_stopwords_for_channel
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
#//==============================================================================//#
kw = Kiwi()

#//==============================================================================//#
# 커스텀 토크나이저
#//==============================================================================//#
def my_beauty_korean_tokenizer(text, stopwords):

    if pd.isna(text) or not text:
        return []
    
    """
    1. 기본 정제 (punctuation제거)
    """
    # 타입
    text = str(text)
    # html 제거
    text = re.sub(r'<[^>]+>', '', text)
     # url 제거
    text = re.sub(r'https?://\S+', '', text)
    # 한글+영어+숫자만 남기고
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', text) 
     # 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()

    # 너무 짧은 리뷰는 삭제
    if len(text) < 2:
        return []


    """
    2. 형태소 분석 (kiwi사용)
    """
    result = kw.analyze(text)
    if not result:
        return []
    
    tokens = result[0][0]

    """
    3. 품사 필터링 & 불용어 제거 & 너무 짧은 리뷰 제거
    """
    keywords = []
    for token in tokens:
        word = token.lemma         # lemma or form 선택? 
        pos = token.tag
        # 품사 필터링
        if pos in ['NNG', 'NNP', 'VA', 'VV']:
            # 불용어 제거
            if len(word) >= 1 and word not in stopwords:
                # 숫자만 있는 리뷰 제거
                if not word.isdigit():
                    keywords.append(word)
    
    return keywords

#//==============================================================================//#
# 채널별 토크나이저 호출 반환
#//==============================================================================//#
def get_tokenizer_for_channel(channel_name):
    """
    채널별로 stopwords를 로드해서 토크나이저 리턴
    """
    stopwords = get_stopwords_for_channel(channel_name)
    return lambda text: my_beauty_korean_tokenizer(text, stopwords)

#//==============================================================================//#-
# TF-IDF / CountVectorizer 생성기
#//==============================================================================//#
def get_tfidf_vectorizer(channel_name,
                         min_df=2,
                         max_df=0.85,
                         max_features=10000,
                         ngram_range=(1,1)):
    tokenizer = get_tokenizer_for_channel(channel_name)
    return TfidfVectorizer(
        tokenizer=tokenizer,
        token_pattern=None,
        min_df=min_df,
        max_df=max_df,
        max_features=max_features,
        ngram_range=ngram_range
    )

def get_count_vectorizer(channel_name,
                         min_df=2,
                         max_df=1.0,
                         max_features=None,
                         ngram_range=(1,1)):
    tokenizer = get_tokenizer_for_channel(channel_name)
    return CountVectorizer(
        tokenizer=tokenizer,
        token_pattern=None,
        min_df=min_df,
        max_df=max_df,
        max_features=max_features,
        ngram_range=ngram_range
    )