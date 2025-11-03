#//==============================================================================//#
"""
keyword_analyzer.py
키워드 분석 모듈
- TF-IDF 기반 키워드 추출
- 제품별 키워드 매트릭스 계산
- 키워드 공출현 분석
- 시계열 트렌드 분석

last_updated : 2025.10.25
"""
#//==============================================================================//#
import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
from analyzer.txt_mining.tokenizer import get_tfidf_vectorizer, get_tokenizer_for_channel
from analyzer.txt_mining.words_dictionary.stopwords_manager import (
    load_stopwords,
    get_stopwords_for_channel
)

#//==============================================================================//#
# 전체 채널 불용어 통합
#//==============================================================================//#
def get_stopwords_for_all_channels():
    """전체 채널 불용어 통합

    Returns:
        set: 모든 채널의 불용어 합집합
    """
    # 공통 불용어 (backward compatibility)
    common = load_stopwords("stopwords_common.txt")
    if not common:
        common = load_stopwords("stopwords_origin.txt")

    brands = load_stopwords("stopwords_brands.txt")
    products = load_stopwords("stopwords_products.txt")
    ingredients = load_stopwords("stopwords_ingredients.txt")
    channels = load_stopwords("stopwords_channels.txt")
    daiso = load_stopwords("stopwords_daiso.txt")
    oliveyoung = load_stopwords("stopwords_oliveyoung.txt")
    coupang = load_stopwords("stopwords_coupang.txt")

    return common.union(brands, products, ingredients, channels, daiso, oliveyoung, coupang)

#//==============================================================================//#
# TF-IDF 기반 키워드 추출
#//==============================================================================//#
def extract_keywords_tfidf(df, channel, top_n=30):
    """TF-IDF 기반 키워드 추출

    Args:
        df (DataFrame): 필터링된 리뷰 데이터 (review_text 컬럼 필요)
        channel (str): 채널명 ('oliveyoung', 'daiso', 'coupang', 'all')
        top_n (int): 상위 N개 키워드

    Returns:
        tuple: (keyword_df, keyword_to_indices)
            - keyword_df (DataFrame): [키워드, TF-IDF점수, 문서빈도]
            - keyword_to_indices (dict): {키워드: [원본 df의 인덱스 리스트]}
    """
    empty_result = (
        pd.DataFrame(columns=['키워드', 'TF-IDF점수', '문서빈도']),
        {}
    )

    if df.empty or 'review_text' not in df.columns:
        return empty_result

    # 결측치 제거 (원본 인덱스 유지)
    df_clean = df[df['review_text'].notna()].copy()

    if len(df_clean) == 0:
        return empty_result

    # TF-IDF Vectorizer 생성
    vectorizer = get_tfidf_vectorizer(
        channel_name=channel if channel != 'all' else 'oliveyoung',
        min_df=2,
        max_df=0.85,
        max_features=10000,
        ngram_range=(1,1)
    )

    try:
        # TF-IDF 계산
        tfidf_matrix = vectorizer.fit_transform(df_clean['review_text'])
        feature_names = vectorizer.get_feature_names_out()

        # 키워드별 평균 TF-IDF 점수 계산
        tfidf_mean = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

        # 문서 빈도 계산 (해당 키워드가 등장한 문서 수)
        doc_freq = np.asarray((tfidf_matrix > 0).sum(axis=0)).flatten()

        # DataFrame 생성
        keyword_df = pd.DataFrame({
            '키워드': feature_names,
            'TF-IDF점수': tfidf_mean,
            '문서빈도': doc_freq
        })

        # 정렬 및 상위 N개 추출
        keyword_df = keyword_df.sort_values('TF-IDF점수', ascending=False).head(top_n)
        keyword_df = keyword_df.reset_index(drop=True)

        # Top N 키워드에 대한 리뷰 인덱스 매핑 생성
        keyword_to_indices = {}
        top_keywords = set(keyword_df['키워드'].tolist())

        for i, keyword in enumerate(feature_names):
            if keyword in top_keywords:
                # tfidf_matrix에서 해당 키워드 컬럼의 0이 아닌 값들의 행 인덱스 추출
                doc_indices = tfidf_matrix[:, i].nonzero()[0]
                # df_clean의 인덱스를 원본 df의 인덱스로 매핑
                original_indices = df_clean.iloc[doc_indices].index.tolist()
                keyword_to_indices[keyword] = original_indices

        return keyword_df, keyword_to_indices

    except Exception as e:
        st.error(f"키워드 추출 중 오류 발생: {str(e)}")
        return empty_result

#//==============================================================================//#
# 제품별 키워드 매트릭스 계산 (캐싱)
#//==============================================================================//#
@st.cache_data(ttl=3600, show_spinner=False)
def calculate_keyword_matrix(_df, channel, keywords):
    """제품별 × 키워드별 TF-IDF 평균 점수 매트릭스 생성
    1시간 캐싱
    
    Args:
        _df (DataFrame): 필터링된 리뷰 데이터
        channel (str): 채널명
        keywords (list): 분석할 키워드 리스트
    
    Returns:
        DataFrame: [제품명, 브랜드, 리뷰수, 평균평점, keyword1, keyword2, ...]
    """
    if _df.empty:
        return pd.DataFrame()
    
    # 필요한 컬럼 확인
    required_cols = ['product_name', 'brand', 'review_text', 'rating']
    if not all(col in _df.columns for col in required_cols):
        return pd.DataFrame()
    
    # 제품별로 그룹화
    grouped = _df.groupby('product_name')
    
    results = []
    
    for product_name, product_df in grouped:
        # 기본 정보
        brand = product_df['brand'].iloc[0]
        review_count = len(product_df)
        avg_rating = product_df['rating'].mean()
        
        # 리뷰 텍스트 정제
        review_texts = product_df['review_text'].fillna('')
        
        if review_texts.empty or review_texts.str.strip().eq('').all():
            continue
        
        # TF-IDF 계산
        vectorizer = get_tfidf_vectorizer(
            channel_name=channel if channel != 'all' else 'oliveyoung',
            min_df=1,
            max_df=1.0,
            ngram_range=(1,1)
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(review_texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # 각 키워드별 평균 TF-IDF 점수
            keyword_scores = {}
            for keyword in keywords:
                if keyword in feature_names:
                    idx = list(feature_names).index(keyword)
                    keyword_scores[keyword] = tfidf_matrix[:, idx].mean()
                else:
                    keyword_scores[keyword] = 0.0
            
            # 결과 추가
            result_row = {
                '제품명': product_name,
                '브랜드': brand,
                '리뷰수': review_count,
                '평균평점': round(avg_rating, 2)
            }
            result_row.update(keyword_scores)
            results.append(result_row)
            
        except Exception as e:
            print(f"제품 {product_name} 처리 중 오류: {str(e)}")
            continue
    
    if not results:
        return pd.DataFrame()
    
    return pd.DataFrame(results)

#//==============================================================================//#
# 키워드별 제품 TOP N 조회
#//==============================================================================//#
def get_products_by_keyword(matrix_df, keyword, top_n=10, min_reviews=20):
    """특정 키워드에 대한 제품 TOP N 조회
    
    Args:
        matrix_df (DataFrame): calculate_keyword_matrix() 결과
        keyword (str): 키워드명
        top_n (int): 상위 N개 제품
        min_reviews (int): 최소 리뷰 수
    
    Returns:
        DataFrame: [순위, 제품명, 브랜드, TF-IDF점수, 리뷰수, 평균평점, 워닝]
    """
    if matrix_df.empty or keyword not in matrix_df.columns:
        return pd.DataFrame()
    
    # 최소 리뷰 수 필터링
    filtered_df = matrix_df[matrix_df['리뷰수'] >= min_reviews].copy()
    
    if filtered_df.empty:
        return pd.DataFrame()
    
    # 키워드 점수로 정렬
    filtered_df = filtered_df.sort_values(keyword, ascending=False).head(top_n)
    
    # 결과 DataFrame 생성
    result_df = pd.DataFrame({
        '순위': range(1, len(filtered_df) + 1),
        '제품명': filtered_df['제품명'].values,
        '브랜드': filtered_df['브랜드'].values,
        'TF-IDF점수': filtered_df[keyword].values,
        '리뷰수': filtered_df['리뷰수'].values,
        '평균평점': filtered_df['평균평점'].values
    })
    
    # 워닝 플래그 추가 (리뷰 20~50개)
    result_df['워닝'] = result_df['리뷰수'].apply(lambda x: True if 20 <= x < 50 else False)
    
    return result_df.reset_index(drop=True)

#//==============================================================================//#
# 키워드 공출현 분석
#//==============================================================================//#
def calculate_cooccurrence(df, channel, target_keyword, top_n=10):
    """특정 키워드와 함께 나오는 키워드 분석 (같은 리뷰 내)
    
    Args:
        df (DataFrame): 필터링된 리뷰 데이터
        channel (str): 채널명
        target_keyword (str): 대상 키워드
        top_n (int): 상위 N개 키워드
    
    Returns:
        DataFrame: [키워드, 공출현횟수, 비율(%)]
    """
    if df.empty or 'review_text' not in df.columns:
        return pd.DataFrame(columns=['키워드', '공출현횟수', '비율(%)'])
    
    # 토크나이저 가져오기
    tokenizer = get_tokenizer_for_channel(channel if channel != 'all' else 'oliveyoung')
    
    # 공출현 카운터
    cooccur_counter = Counter()
    target_count = 0
    
    for review_text in df['review_text'].dropna():
        tokens = tokenizer(review_text)
        
        # 대상 키워드가 포함된 리뷰만
        if target_keyword in tokens:
            target_count += 1
            # 같은 리뷰에 나온 다른 키워드들 카운트
            for token in tokens:
                if token != target_keyword:
                    cooccur_counter[token] += 1
    
    if target_count == 0:
        return pd.DataFrame(columns=['키워드', '공출현횟수', '비율(%)'])
    
    # 상위 N개 추출
    top_cooccur = cooccur_counter.most_common(top_n)
    
    # DataFrame 생성
    result_df = pd.DataFrame({
        '키워드': [item[0] for item in top_cooccur],
        '공출현횟수': [item[1] for item in top_cooccur],
        '비율(%)': [round(item[1] / target_count * 100, 2) for item in top_cooccur]
    })
    
    return result_df

#//==============================================================================//#
# 키워드 시계열 트렌드
#//==============================================================================//#
def calculate_keyword_trend(df, channel, keyword, freq='M'):
    """키워드 시계열 트렌드 분석
    
    Args:
        df (DataFrame): 필터링된 리뷰 데이터 (review_date 컬럼 필요)
        channel (str): 채널명
        keyword (str): 키워드명
        freq (str): 집계 단위 ('M': 월, 'W': 주, 'D': 일)
    
    Returns:
        DataFrame: [날짜, 언급수]
    """
    if df.empty or 'review_date' not in df.columns or 'review_text' not in df.columns:
        return pd.DataFrame(columns=['날짜', '언급수'])
    
    # 날짜 변환
    df = df.copy()
    df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
    df = df.dropna(subset=['review_date'])
    
    if df.empty:
        return pd.DataFrame(columns=['날짜', '언급수'])
    
    # 토크나이저 가져오기
    tokenizer = get_tokenizer_for_channel(channel if channel != 'all' else 'oliveyoung')
    
    # 키워드 포함 여부 확인
    df['contains_keyword'] = df['review_text'].apply(
        lambda text: keyword in tokenizer(text) if pd.notna(text) else False
    )
    
    # 기간별 집계
    df['period'] = df['review_date'].dt.to_period(freq)
    trend_df = df[df['contains_keyword']].groupby('period').size().reset_index(name='언급수')
    trend_df['날짜'] = trend_df['period'].dt.to_timestamp()
    
    return trend_df[['날짜', '언급수']].sort_values('날짜')