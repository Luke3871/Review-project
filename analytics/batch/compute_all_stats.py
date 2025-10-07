#//==============================================================================//#
"""
compute_all_stats.py
전체 통계 계산 및 DB 적재

실행: python batch/compute_all_stats.py

last_updated : 2025.10.02
"""
#//==============================================================================//#

import sys
import os

# analytics 폴더 고정
current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import psycopg2
from core.basic_stats import compute_product_statistics
from core.brand_analysis import analyze_brand_attributes
from core.keyword_analysis import analyze_product_keywords
from core.trend_analysis import analyze_monthly_trends
from core.topic_analysis import analyze_product_topics
from utils.db_insert import (
    insert_product_stats_batch,
    insert_brand_attribute_stats_batch,
    insert_product_keywords_batch,
    insert_monthly_trends_batch,
    insert_product_topics_batch
)

#//==============================================================================//#
# DB 설정
#//==============================================================================//#

DB_CONFIG = {
    "dbname": "ragdb",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

#//==============================================================================//#
# 메인 실행
#//==============================================================================//#

def compute_all():
    print("DB 연결 중...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    print("reviews 테이블 로드 중...")
    df = pd.read_sql("SELECT * FROM reviews", conn)
    print(f"로드 완료: {len(df):,}개 리뷰")
    
    print("\n제품별 통계 계산 중...")
    products = compute_product_statistics(df)
    print(f"계산 완료: {len(products)}개 제품")
    
    print("DB 저장 중...")
    insert_product_stats_batch(conn, products)
    
    print("\n브랜드 속성 분석 중...")
    brand_attrs = analyze_brand_attributes(df)
    print(f"계산 완료: {len(brand_attrs)}개 브랜드 x 속성")
    
    print("DB 저장 중...")
    insert_brand_attribute_stats_batch(conn, brand_attrs)

    print("\n키워드 분석 중...")
    keywords = analyze_product_keywords(df, analysis_type='tfidf', max_keywords=30)
    print(f"계산 완료: {len(keywords)}개 제품 키워드")
    
    print("DB 저장 중...")
    insert_product_keywords_batch(conn, keywords)

    print("\n월별 트렌드 분석 중...")
    trends = analyze_monthly_trends(df)
    print(f"계산 완료: {len(trends)}개 월별 데이터")

    print("DB 저장 중...")
    insert_monthly_trends_batch(conn, trends)
    
    print("\n토픽 분석 중...")
    topics = analyze_product_topics(df, n_topics=5, min_topic_size=15)
    print(f"계산 완료: {len(topics)}개 제품 토픽")

    print("DB 저장 중...")
    insert_product_topics_batch(conn, topics)
    
    conn.close()
    print("\n완료")


if __name__ == "__main__":
    compute_all()