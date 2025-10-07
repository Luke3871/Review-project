#//==============================================================================//#
"""
db_insert.py
분석 결과 DB 저장

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
    
import psycopg2
from typing import Dict, List

#//==============================================================================//#
# product_stats 저장
#//==============================================================================//#

def insert_product_stats(conn, product_data: Dict):
    """
    제품 통계 1개를 product_stats 테이블에 저장
    
    Args:
        conn: psycopg2 connection
        product_data: compute_product_statistics() 결과 중 1개
    """
    
    sql = """
    INSERT INTO product_stats (
        product_name, brand, channel, category,
        total_reviews, avg_rating, median_rating, std_rating,
        rating_1, rating_2, rating_3, rating_4, rating_5,
        product_price_sale, product_price_origin,
        date_start, date_end
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (product_name, channel) 
    DO UPDATE SET
        brand = EXCLUDED.brand,
        category = EXCLUDED.category,
        total_reviews = EXCLUDED.total_reviews,
        avg_rating = EXCLUDED.avg_rating,
        median_rating = EXCLUDED.median_rating,
        std_rating = EXCLUDED.std_rating,
        rating_1 = EXCLUDED.rating_1,
        rating_2 = EXCLUDED.rating_2,
        rating_3 = EXCLUDED.rating_3,
        rating_4 = EXCLUDED.rating_4,
        rating_5 = EXCLUDED.rating_5,
        product_price_sale = EXCLUDED.product_price_sale,
        product_price_origin = EXCLUDED.product_price_origin,
        date_start = EXCLUDED.date_start,
        date_end = EXCLUDED.date_end,
        updated_at = NOW()
    """
    
    with conn.cursor() as cur:
        cur.execute(sql, (
            product_data['product_name'],
            product_data['brand'],
            product_data['channel'],
            product_data['category'],
            product_data['total_reviews'],
            product_data['avg_rating'],
            product_data['median_rating'],
            product_data['std_rating'],
            product_data['rating_1'],
            product_data['rating_2'],
            product_data['rating_3'],
            product_data['rating_4'],
            product_data['rating_5'],
            product_data['product_price_sale'],
            product_data['product_price_origin'],
            product_data['date_start'],
            product_data['date_end']
        ))
    
    conn.commit()


def insert_product_stats_batch(conn, products: List[Dict]):
    """
    여러 제품 통계를 한 번에 저장
    
    Args:
        products: compute_product_statistics() 결과 전체
    """
    
    for product_data in products:
        insert_product_stats(conn, product_data)
    
    print(f"{len(products)}개 제품 통계 저장 완료")

#//==============================================================================//#
# brand_attributes 저장
#//==============================================================================//#

def insert_brand_attribute_stats(conn, brand_data: Dict):
    """
    브랜드 속성 통계 1개 저장
    """
    
    sql = """
    INSERT INTO brand_attribute_stats (
        brand, attribute, channel,
        positive_count, negative_count, neutral_count,
        positive_ratio, negative_ratio,
        sample_size, avg_rating,
        representative_reviews,
        period_start, period_end
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (brand, attribute, channel)
    DO UPDATE SET
        positive_count = EXCLUDED.positive_count,
        negative_count = EXCLUDED.negative_count,
        neutral_count = EXCLUDED.neutral_count,
        positive_ratio = EXCLUDED.positive_ratio,
        negative_ratio = EXCLUDED.negative_ratio,
        sample_size = EXCLUDED.sample_size,
        avg_rating = EXCLUDED.avg_rating,
        representative_reviews = EXCLUDED.representative_reviews,
        period_start = EXCLUDED.period_start,
        period_end = EXCLUDED.period_end,
        updated_at = NOW()
    """
    
    with conn.cursor() as cur:
        cur.execute(sql, (
            brand_data['brand'],
            brand_data['attribute'],
            brand_data['channel'],
            brand_data['positive_count'],
            brand_data['negative_count'],
            brand_data['neutral_count'],
            brand_data['positive_ratio'],
            brand_data['negative_ratio'],
            brand_data['sample_size'],
            brand_data['avg_rating'],
            brand_data['representative_reviews'],
            brand_data['period_start'],
            brand_data['period_end']
        ))
    
    conn.commit()


def insert_brand_attribute_stats_batch(conn, brands: List[Dict]):
    """
    여러 브랜드 속성 통계 한번에 저장
    """
    
    for brand_data in brands:
        insert_brand_attribute_stats(conn, brand_data)
    
    print(f"{len(brands)}개 브랜드 속성 통계 저장 완료")


#//==============================================================================//#
# 제품별 대표 키워드
#//==============================================================================//#

import json

def insert_product_keywords(conn, keyword_data: Dict):
    """
    제품 키워드 1개 저장
    """
    
    sql = """
    INSERT INTO product_keywords (
        product_name, channel, keywords, top_keywords,
        analysis_type, period_start, period_end
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (product_name, channel)
    DO UPDATE SET
        keywords = EXCLUDED.keywords,
        top_keywords = EXCLUDED.top_keywords,
        analysis_type = EXCLUDED.analysis_type,
        period_start = EXCLUDED.period_start,
        period_end = EXCLUDED.period_end,
        updated_at = NOW()
    """
    
    with conn.cursor() as cur:
        cur.execute(sql, (
            keyword_data['product_name'],
            keyword_data['channel'],
            json.dumps(keyword_data['keywords'], ensure_ascii=False),
            keyword_data['top_keywords'],
            keyword_data['analysis_type'],
            keyword_data['period_start'],
            keyword_data['period_end']
        ))
    
    conn.commit()


def insert_product_keywords_batch(conn, keywords: List[Dict]):
    """
    여러 제품 키워드 한번에 저장
    """
    
    for keyword_data in keywords:
        insert_product_keywords(conn, keyword_data)
    
    print(f"{len(keywords)}개 제품 키워드 저장 완료")


#//==============================================================================//#
# 트렌드 분석 (델타)
#//==============================================================================//#

def insert_monthly_trend(conn, trend_data: Dict):
    """
    월별 트렌드 1개 저장
    """
    
    sql = """
    INSERT INTO monthly_trends (
        brand, channel, year_month, review_count, avg_rating
    ) VALUES (
        %s, %s, %s, %s, %s
    )
    ON CONFLICT (brand, channel, year_month)
    DO UPDATE SET
        review_count = EXCLUDED.review_count,
        avg_rating = EXCLUDED.avg_rating,
        updated_at = NOW()
    """
    
    with conn.cursor() as cur:
        cur.execute(sql, (
            trend_data['brand'],
            trend_data['channel'],
            trend_data['year_month'],
            trend_data['review_count'],
            trend_data['avg_rating']
        ))
    
    conn.commit()


def insert_monthly_trends_batch(conn, trends: List[Dict]):
    for trend_data in trends:
        insert_monthly_trend(conn, trend_data)
    
    print(f"{len(trends)}개 월별 트렌드 저장 완료")


#//==============================================================================//#
# 토픽 모델링 기존 임베딩 데이터 활용 (BERT)
#//==============================================================================//#

def insert_product_topic(conn, topic_data: Dict):
    """
    제품 토픽 1개 저장
    """
    
    import json
    
    sql = """
    INSERT INTO product_topics (
        product_name, channel, topics, topic_distribution,
        representative_docs, period_start, period_end
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (product_name, channel)
    DO UPDATE SET
        topics = EXCLUDED.topics,
        topic_distribution = EXCLUDED.topic_distribution,
        representative_docs = EXCLUDED.representative_docs,
        period_start = EXCLUDED.period_start,
        period_end = EXCLUDED.period_end,
        updated_at = NOW()
    """
    
    with conn.cursor() as cur:
        cur.execute(sql, (
            topic_data['product_name'],
            topic_data['channel'],
            json.dumps(topic_data['topics'], ensure_ascii=False),
            json.dumps(topic_data['topic_distribution'], ensure_ascii=False),
            json.dumps(topic_data['representative_docs'], ensure_ascii=False),
            topic_data['period_start'],
            topic_data['period_end']
        ))
    
    conn.commit()


def insert_product_topics_batch(conn, topics: List[Dict]):
    for topic_data in topics:
        insert_product_topic(conn, topic_data)
    
    print(f"{len(topics)}개 제품 토픽 저장 완료")