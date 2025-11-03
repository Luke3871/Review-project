#//==============================================================================//#
"""
hierarchical_retrieval.py
계층적 검색 및 요약 (Map-Reduce)

수정사항:
- Stage 크기 확대 (10만 → 1만 → 1000)
- 순서 변경 (Dense → BM25 → Hybrid)
- Filter는 LLM이 판단하여 전달

last_updated: 2025.10.16
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
from typing import Dict, List, Optional
from openai import OpenAI

from .bm25_search import BM25SearchTool
from .vector_search import VectorSearchTool
from .hybrid_search import HybridSearchTool

#//==============================================================================//#
# Hierarchical Retrieval Tool
#//==============================================================================//#

class HierarchicalRetrieval:
    """
    계층적 검색 및 요약
    
    Stage 1: Dense (Vector) 의미 검색 (10만개)
    Stage 2: BM25 키워드 재정렬 (1만개)
    Stage 3: Hybrid 최종 선별 (1000개)
    Stage 4: 계층적 요약
    """
    
    def __init__(self, db_config: Dict, api_key: str):
        self.db_config = db_config
        self.api_key = api_key
        
        self.vector_tool = VectorSearchTool(db_config) 
        self.bm25_tool = BM25SearchTool(db_config)
        self.hybrid_tool = HybridSearchTool(db_config)  
        self.llm_client = OpenAI(api_key=api_key)
        
    def retrieve(
        self,
        query: str,
        filters: Optional[Dict] = None,
        stage1_size: int = 100000,
        stage2_size: int = 10000,
        stage3_size: int = 1000,
        enable_summary: bool = True,
        chunk_size: int = 20
    ) -> Dict:
        """
        계층적 검색 실행
        
        Args:
            query: 검색 쿼리
            filters: 필터 조건 (LLM이 판단하여 전달)
                     {brand, channel, category, min_rating, date_from, date_to}
            stage1_size: Stage 1 목표 개수 (Dense)
            stage2_size: Stage 2 목표 개수 (BM25)
            stage3_size: Stage 3 목표 개수 (Hybrid)
            enable_summary: 요약 활성화 여부
            chunk_size: 요약 청크 크기
        
        Returns:
            {
                'stage1_count': int,
                'stage2_count': int,
                'stage3_count': int,
                'final_results': DataFrame,
                'summary': str
            }
        """
        
        # Stage 1: Dense 의미 검색 (가장 넓게)
        stage1_results = self.vector_tool.search(
            query=query,
            top_k=stage1_size,
            filters=filters
        )
        
        if stage1_results.empty:
            return {
                'stage1_count': 0,
                'stage2_count': 0,
                'stage3_count': 0,
                'final_results': pd.DataFrame(),
                'summary': '검색 결과 없음',
                'error': 'Stage 1 검색 결과 없음'
            }
        
        # Stage 2: BM25 키워드 재정렬
        # Stage 1 결과를 임시 DB로 간주하고 BM25 적용
        stage2_results = self._apply_bm25_rerank(
            stage1_results,
            query,
            top_k=min(stage2_size, len(stage1_results))
        )
        
        if stage2_results.empty:
            stage2_results = stage1_results.head(stage2_size)
        
        # Stage 3: Hybrid 최종 선별
        if len(stage2_results) <= stage3_size:
            stage3_results = stage2_results
        else:
            stage3_results = self._apply_hybrid_rerank(
                stage2_results,
                query,
                top_k=stage3_size
            )
        
        result = {
            'stage1_count': len(stage1_results),
            'stage2_count': len(stage2_results),
            'stage3_count': len(stage3_results),
            'final_results': stage3_results
        }
        
        # Stage 4: 계층적 요약
        if enable_summary and not stage3_results.empty:
            summary = self._hierarchical_summarize(
                stage3_results,
                query,
                chunk_size
            )
            result['summary'] = summary
        else:
            result['summary'] = None
        
        return result
    
    def _apply_bm25_rerank(
        self,
        df: pd.DataFrame,
        query: str,
        top_k: int
    ) -> pd.DataFrame:
        """
        BM25로 재정렬
        
        Args:
            df: Stage 1 결과 DataFrame
            query: 검색 쿼리
            top_k: 상위 N개
        
        Returns:
            재정렬된 DataFrame
        """
        
        if df.empty:
            return df
        
        # 토크나이저 준비
        channel = df['channel'].iloc[0] if 'channel' in df.columns else 'OliveYoung'
        
        from rank_bm25 import BM25Okapi
        
        tokenizer_path = os.path.join(analytics_dir, 'utils')
        if tokenizer_path not in sys.path:
            sys.path.insert(0, tokenizer_path)
        
        from utils.tokenizer import get_tokenizer_for_channel
        tokenizer = get_tokenizer_for_channel(channel)
        
        # 토큰화
        texts = df['review_text'].tolist()
        tokenized_corpus = [tokenizer(text) for text in texts]
        
        # BM25 적용
        bm25 = BM25Okapi(tokenized_corpus)
        query_tokens = tokenizer(query)
        scores = bm25.get_scores(query_tokens)
        
        # 상위 결과
        top_indices = scores.argsort()[-top_k:][::-1]
        result_df = df.iloc[top_indices].copy()
        result_df['bm25_score'] = scores[top_indices]
        
        return result_df
    
    def _apply_hybrid_rerank(
        self,
        df: pd.DataFrame,
        query: str,
        top_k: int,
        alpha: float = 0.7
    ) -> pd.DataFrame:
        """
        Hybrid로 최종 재정렬
        
        Args:
            df: Stage 2 결과 DataFrame
            query: 검색 쿼리
            top_k: 상위 N개
            alpha: Vector 가중치 (0.7 = 70% Vector, 30% BM25)
        
        Returns:
            재정렬된 DataFrame
        """
        
        if df.empty:
            return df
        
        # 이미 similarity와 bm25_score가 있다고 가정
        if 'similarity' not in df.columns or 'bm25_score' not in df.columns:
            return df.head(top_k)
        
        # 점수 정규화
        vector_scores = df['similarity'].values
        bm25_scores = df['bm25_score'].values
        
        # BM25 점수 정규화 (0~1)
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()
        
        # Hybrid 점수
        hybrid_scores = alpha * vector_scores + (1 - alpha) * bm25_scores
        
        df = df.copy()
        df['hybrid_score'] = hybrid_scores
        df = df.sort_values('hybrid_score', ascending=False).head(top_k)
        
        return df
    
    def _hierarchical_summarize(
        self,
        df: pd.DataFrame,
        query: str,
        chunk_size: int
    ) -> str:
        """
        계층적 요약 (Map-Reduce 패턴)
        
        Args:
            df: 리뷰 DataFrame
            query: 원본 쿼리
            chunk_size: 청크 크기
        
        Returns:
            최종 요약 텍스트
        """
        
        if df.empty:
            return "데이터 없음"
        
        reviews = df['review_text'].tolist()
        
        # 리뷰가 적으면 바로 요약
        if len(reviews) <= chunk_size:
            return self._summarize_direct(reviews, query)
        
        # 청크로 분할
        chunks = [
            reviews[i:i+chunk_size] 
            for i in range(0, len(reviews), chunk_size)
        ]
        
        # Map: 각 청크 요약
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            summary = self._summarize_chunk(chunk, query, i)
            if summary:
                chunk_summaries.append(summary)
        
        if not chunk_summaries:
            return "요약 생성 실패"
        
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        
        # Reduce: 청크 요약들을 다시 요약
        final_summary = self._reduce_summaries(chunk_summaries, query)
        
        return final_summary
    
    def _summarize_direct(
        self,
        reviews: List[str],
        query: str
    ) -> str:
        """소량 리뷰 직접 요약"""
        
        reviews_text = "\n".join([
            f"{i+1}. {r[:200]}" 
            for i, r in enumerate(reviews[:20])
        ])
        
        prompt = f"""다음 리뷰들을 "{query}"에 대해 분석하여 요약하세요.

리뷰 ({len(reviews)}개):
{reviews_text}

다음 형식으로 요약하세요:
1. 핵심 내용 (2-3문장)
2. 주요 긍정 의견
3. 주요 부정 의견
4. 전반적 평가
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "리뷰 분석 전문가"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"리뷰 {len(reviews)}개 분석 완료"
    
    def _summarize_chunk(
        self,
        reviews: List[str],
        query: str,
        chunk_num: int
    ) -> Optional[str]:
        """단일 청크 요약"""
        
        reviews_text = "\n".join([
            f"- {r[:150]}" 
            for r in reviews[:10]
        ])
        
        prompt = f"""다음은 "{query}"에 대한 리뷰 그룹 {chunk_num}입니다 (총 {len(reviews)}개).

리뷰 샘플:
{reviews_text}

이 그룹의 핵심 내용을 3-4문장으로 요약하세요:
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "리뷰 요약 전문가"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return None
    
    def _reduce_summaries(
        self,
        summaries: List[str],
        query: str
    ) -> str:
        """여러 요약을 하나로 통합"""
        
        summaries_text = "\n\n".join([
            f"[그룹 {i+1}]\n{s}" 
            for i, s in enumerate(summaries)
        ])
        
        prompt = f"""다음은 "{query}"에 대한 {len(summaries)}개 리뷰 그룹의 요약들입니다.

{summaries_text}

이를 종합하여 최종 분석 보고서를 작성하세요:

1. 전체 핵심 요약 (2-3문장)
2. 공통적인 긍정 평가
3. 공통적인 부정 평가
4. 그룹 간 차이점 (있다면)
5. 최종 결론
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "리뷰 분석 전문가"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "\n\n".join(summaries)
    
    def close(self):
        """연결 종료"""
        self.vector_tool.close()
        self.bm25_tool.close()
        self.hybrid_tool.close()