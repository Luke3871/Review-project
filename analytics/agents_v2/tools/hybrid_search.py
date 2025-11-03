#//==============================================================================//#
"""
hybrid_search.py
Vector + BM25 하이브리드 검색

last_updated: 2025.01.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import numpy as np
from typing import Dict, Optional

from .vector_search import VectorSearchTool
from .bm25_search import BM25SearchTool

#//==============================================================================//#
# Hybrid Search Tool
#//==============================================================================//#

class HybridSearchTool:
    """
    Vector + BM25 하이브리드 검색
    """
    
    def __init__(self, db_config: Dict):
        """
        초기화
        
        Args:
            db_config: DB 설정
        """
        self.vector_tool = VectorSearchTool(db_config)
        self.bm25_tool = BM25SearchTool(db_config)
    
    def search(
        self,
        query: str,
        top_k: int = 30,
        filters: Optional[Dict] = None,
        alpha: float = 0.7
    ) -> pd.DataFrame:
        """
        하이브리드 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 개수
            filters: 필터 조건
            alpha: Vector 가중치 (0~1, 기본 0.7)
        
        Returns:
            검색 결과 DataFrame
        """
        
        # Vector 검색
        vector_results = self.vector_tool.search(query, top_k=top_k*2, filters=filters)
        
        # BM25 검색
        bm25_results = self.bm25_tool.search(query, top_k=top_k*2, filters=filters)
        
        if vector_results.empty and bm25_results.empty:
            return pd.DataFrame()
        
        # 점수 정규화 및 결합
        vector_scores = {}
        if not vector_results.empty and 'similarity' in vector_results.columns:
            for _, row in vector_results.iterrows():
                review_id = row['review_id']
                vector_scores[review_id] = row['similarity']
        
        bm25_scores = {}
        if not bm25_results.empty and 'bm25_score' in bm25_results.columns:
            max_bm25 = bm25_results['bm25_score'].max()
            for _, row in bm25_results.iterrows():
                review_id = row['review_id']
                bm25_scores[review_id] = row['bm25_score'] / max_bm25 if max_bm25 > 0 else 0
        
        # 결합 점수 계산
        all_ids = set(vector_scores.keys()) | set(bm25_scores.keys())
        
        combined_scores = {}
        for review_id in all_ids:
            v_score = vector_scores.get(review_id, 0)
            b_score = bm25_scores.get(review_id, 0)
            combined_scores[review_id] = alpha * v_score + (1 - alpha) * b_score
        
        # 상위 결과 선택
        top_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        top_ids = [rid for rid, _ in top_ids]
        
        # 전체 데이터에서 선택
        all_results = pd.concat([vector_results, bm25_results]).drop_duplicates(subset=['review_id'])
        result_df = all_results[all_results['review_id'].isin(top_ids)].copy()
        
        # 점수 추가
        result_df['hybrid_score'] = result_df['review_id'].map(combined_scores)
        result_df = result_df.sort_values('hybrid_score', ascending=False)
        
        return result_df
    
    def close(self):
        """연결 종료"""
        self.vector_tool.close()
        self.bm25_tool.close()