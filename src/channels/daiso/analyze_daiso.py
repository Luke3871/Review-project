#//==============================================================================//#
"""
다이소 리뷰 데이터 분석 모듈

기능:
- 데이터 정리
- CountVectorizer
- TF-IDF
- 감정분석
- 

last_updated : 2025.09.10
"""
#//==============================================================================//#

#//==============================================================================//#
"""
csv 개별 정리 모듈
"""
#//==============================================================================//#
import pandas as pd



def clean_data(df):
    
    # 별점 문자형 -> 숫자형
    df["rating"] = df["rating"].astype(str).str.replace("점","").astype(int)

    # 날짜 문자형 -> datetime형
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")

    # 제품 가격 정수형 변환
    df["product_price"] = df["product_price"].astype(str).str.replace(",","").astype(int)

    # 결측 제거
    df = df.dropna(subset=["review_text"])

    return df

df = pd.read_csv(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\src\channels\daiso\data_daiso\reviews_daiso\skincare_REVIEW_BEST [화잘먹템] 미모 바이 마몽드 로지-히알론 리퀴드 마스크 2 ml 6개입 (아모레_reviews.csv")

clean_data(df)

#//==============================================================================//#
"""
형태소 분석기 Kiwipiepy 활용

1. analyze_count
    - 단순 빈도 기반

2. analyze_tfidf
    - 특정 단어 및 문서 기반
"""
#//==============================================================================//#
from kiwipiepy import Kiwi
from sklearn.feature_extraction.text import CountVectorizer

kiwi = Kiwi()

# 2) stopwords 불러오기 (예: origin만 사용)
with open(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\src\stopwords\stopwords_origin.txt", encoding="utf-8") as f:
    STOPWORDS = set(line.strip() for line in f if line.strip())

# 3) 토크나이저 정의
def kiwi_tokenizer(text, allowed_pos={'NNG','NNP','VA','VV'}):
    tokens = [t.form for t in kiwi.tokenize(text) if t.tag in allowed_pos]
    tokens = [t for t in tokens if t not in STOPWORDS]  # 불용어 제거
    return tokens

# 4) CountVectorizer 적용
vectorizer = CountVectorizer(tokenizer=kiwi_tokenizer)
X = vectorizer.fit_transform(df["review_text"].astype(str))

# 5) 단어-빈도 집계
word_counts = X.toarray().sum(axis=0)
words = vectorizer.get_feature_names_out()
result = sorted(zip(words, word_counts), key=lambda x: x[1], reverse=True)[:20]

print(result)

def analyze_count(df, top_n=20, stopwords= None):

    # Count 기반 Top-N 단어 추출
    return result_df

def analyze_tfidf(df, top_n=20):
    # TF-IDF 기반 Top-N 단어 추출
    return result_df