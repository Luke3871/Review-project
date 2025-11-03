#//==============================================================================//#
"""
hybrid_search.py
Vector + BM25 하이브리드 검색 for V4 ReAct Agent

Modified from agents_v2:
- Uses v4_react_agent's VectorSearchTool and BM25SearchTool

last_updated: 2025.10.26
"""
#//==============================================================================//#

import pandas as pd
import numpy as np
from typing import Dict, Optional

from .vector_search import VectorSearchTool
from .bm25_search import BM25SearchTool

#//==============================================================================//#
# Hybrid Search Tool
#//==============================================================================//#

class HybridSearchTool:
    """Vector + BM25 하이브리드 검색"""

    def __init__(self):
        self.vector_tool = VectorSearchTool()
        self.bm25_tool = BM25SearchTool()

    def search(
        self,
        query: str,
        top_k: int = 1000,
        filters: Optional[Dict] = None,
        alpha: float = 0.7
    ) -> pd.DataFrame:
        """
        하이브리드 검색 (Vector 70% + BM25 30%)

        Args:
            query: 검색 쿼리
            top_k: 반환할 개수 (기본 1000 for Stage 3)
            filters: 필터 조건
            alpha: Vector 가중치 (0~1, 기본 0.7)

        Returns:
            검색 결과 DataFrame
        """

        # Vector 검색 (넓게)
        vector_results = self.vector_tool.search(query, top_k=top_k*2, filters=filters)

        # BM25 검색 (넓게)
        bm25_results = self.bm25_tool.search(query, top_k=top_k*2, filters=filters)

        if vector_results.empty and bm25_results.empty:
            return pd.DataFrame()

        # 점수 정규화
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

        # Hybrid 점수 계산
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
