#//==============================================================================//#
"""
topic_analysis.py
토픽 모델링 (BERTopic + 기존 임베딩 활용)

last_updated : 2025.10.02
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import numpy as np
from typing import List, Dict
from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from utils.validators import validate_common_columns, preprocess_dataframe

#//==============================================================================//#
# 제품별 토픽 분석
#//==============================================================================//#

def analyze_product_topics(
    df: pd.DataFrame,
    n_topics: int = 5,
    min_topic_size: int = 15,
    auto_preprocess: bool = True
) -> List[Dict]:
    """
    제품별 토픽 분석 (기존 임베딩 활용)
    
    Args:
        df: reviews DataFrame (embedding 컬럼 포함)
        n_topics: 추출할 토픽 수
        min_topic_size: 최소 토픽 크기
    
    Returns:
        List[Dict]: product_topics 테이블용 데이터
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    if 'product_name' not in df.columns or 'embedding' not in df.columns:
        raise ValueError("product_name, embedding 컬럼 필요")
    
    results = []
    
    for (product, channel) in df.groupby(['product_name', 'channel']).groups.keys():
        product_df = df[(df['product_name'] == product) & (df['channel'] == channel)]
        
        if len(product_df) < 50:  # 최소 50개 리뷰 필요
            continue
        
        topics_result = extract_topics(
            product_df,
            n_topics=n_topics,
            min_topic_size=min_topic_size
        )
        
        if not topics_result:
            continue
        
        results.append({
            'product_name': product,
            'channel': channel,
            'topics': topics_result['topics'],
            'topic_distribution': topics_result['distribution'],
            'representative_docs': topics_result['representative_docs'],
            'period_start': product_df['review_date'].min().strftime('%Y-%m-%d'),
            'period_end': product_df['review_date'].max().strftime('%Y-%m-%d'),
        })
    
    return results


def extract_topics(
    product_df: pd.DataFrame,
    n_topics: int,
    min_topic_size: int
) -> Dict:
    """
    단일 제품의 토픽 추출
    """
    
    try:
        # 임베딩 문자열을 numpy 배열로 변환
        def parse_embedding(emb_str):
            if isinstance(emb_str, str):
                # 대괄호 제거하고 split
                emb_str = emb_str.strip("[]'\"")
                values = emb_str.split(',')
                # 첫 번째 값(768)만 제외하고 변환
                return np.array([float(v.strip()) for v in values[1:]])
            return emb_str
        
        embeddings = np.array([parse_embedding(emb) for emb in product_df['embedding']])
        reviews = product_df['review_text'].tolist()
        ratings = product_df['rating'].values
        
        # BERTopic 모델 설정
        umap_model = UMAP(
            n_components=5,
            n_neighbors=15,
            random_state=42
        )
        
        hdbscan_model = HDBSCAN(
            min_cluster_size=min_topic_size,
            metric='euclidean',
            prediction_data=True
        )
        
        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            nr_topics=n_topics,
            calculate_probabilities=True
        )
        
        # 토픽 추출 (임베딩 직접 사용)
        topics, probs = topic_model.fit_transform(reviews, embeddings)
        
        # 토픽 정보 추출
        topic_info = topic_model.get_topic_info()
        
        # 토픽별 통계
        topics_data = []
        for topic_id in topic_info['Topic'].unique():
            if topic_id == -1:  # 노이즈 제외
                continue
            
            topic_mask = np.array(topics) == topic_id
            topic_reviews = product_df[topic_mask]
            
            if len(topic_reviews) == 0:
                continue
            
            # 토픽 키워드
            topic_words = topic_model.get_topic(topic_id)
            keywords = [word for word, _ in topic_words[:5]] if topic_words else []
            
            # 긍정/부정 비율
            topic_ratings = topic_reviews['rating'].values
            positive_ratio = (topic_ratings >= 4.0).sum() / len(topic_ratings)
            
            # 대표 문서 (높은 확률 상위 3개)
            topic_probs = probs[topic_mask, topic_id] if len(probs.shape) > 1 else probs[topic_mask]
            top_indices = np.argsort(topic_probs)[-3:][::-1]
            representative = topic_reviews.iloc[top_indices]['review_text'].tolist()
            
            topics_data.append({
                'topic_id': int(topic_id),
                'keywords': keywords,
                'count': int(topic_mask.sum()),
                'avg_rating': float(topic_ratings.mean()),
                'positive_ratio': float(positive_ratio),
                'representative_reviews': representative
            })
        
        # 토픽 분포
        distribution = {}
        for topic_data in topics_data:
            distribution[topic_data['topic_id']] = topic_data['count']
        
        return {
            'topics': topics_data,
            'distribution': distribution,
            'representative_docs': {
                t['topic_id']: t['representative_reviews'] 
                for t in topics_data
            }
        }
        
    except Exception as e:
        print(f"토픽 추출 오류: {e}")
        import traceback
        traceback.print_exc()  # 상세 에러 출력
        return None

def analyze_brand_topics(
    df: pd.DataFrame,
    brand: str,
    auto_preprocess: bool = True
) -> Dict:
    """
    특정 브랜드 전체의 토픽 분석 (실시간 분석용)
    """
    
    validate_common_columns(df)
    
    if auto_preprocess:
        df = preprocess_dataframe(df)
    
    brand_df = df[df['brand'] == brand]
    
    if len(brand_df) < 100:
        return {'error': '데이터 부족'}
    
    return extract_topics(brand_df, n_topics=10, min_topic_size=20)