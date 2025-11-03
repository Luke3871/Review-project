#//==============================================================================//#
"""
hierarchical_retrieval.py
계층적 검색 및 요약 (Map-Reduce) for V4 ReAct Agent

Modified from agents_v2:
- Improved data completeness (reviews[:20], r[:300])
- Uses v4_react_agent.tools
- Integrated with domain-specific prompts

Stage 1: Dense (Vector) 의미 검색
Stage 2: BM25 키워드 재정렬
Stage 3: Hybrid 최종 선별
Stage 4: 계층적 요약 (Map-Reduce)

last_updated: 2025.10.26
"""
#//==============================================================================//#

import sys
import os

# Add dashboard to path
current_file = os.path.abspath(__file__)
v4_dir = os.path.dirname(current_file)
ai_engines_dir = os.path.dirname(v4_dir)
dashboard_dir = os.path.dirname(ai_engines_dir)

if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from openai import OpenAI

from .tools import VectorSearchTool, BM25SearchTool, HybridSearchTool
from .prompts.map_prompt import create_map_prompt
from .prompts.reduce_prompt import create_reduce_prompt

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

    def __init__(self, api_key: str):
        self.api_key = api_key

        self.vector_tool = VectorSearchTool()
        self.bm25_tool = BM25SearchTool()
        self.hybrid_tool = HybridSearchTool()
        self.llm_client = OpenAI(api_key=api_key)

    def retrieve(
        self,
        query: str,
        filters: Optional[Dict] = None,
        stage1_size: int = 100000,
        stage2_size: int = 10000,
        stage3_size: int = 1000,
        enable_summary: bool = True,
        chunk_size: int = 20,
        progress_callback=None
    ) -> Dict:
        """
        계층적 검색 실행

        Args:
            query: 검색 쿼리
            filters: 필터 조건 {brand, channels, category, min_rating, date_from, date_to}
            stage1_size: Stage 1 목표 개수 (Dense)
            stage2_size: Stage 2 목표 개수 (BM25)
            stage3_size: Stage 3 목표 개수 (Hybrid)
            enable_summary: 요약 활성화 여부
            chunk_size: 요약 청크 크기
            progress_callback: 진행상황 콜백 함수

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
        if progress_callback:
            progress_callback('stage1_start', query)

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

        if progress_callback:
            progress_callback('stage1_done', len(stage1_results))

        # Stage 2: BM25 키워드 재정렬
        if progress_callback:
            progress_callback('stage2_start', None)

        stage2_results = self._apply_bm25_rerank(
            stage1_results,
            query,
            top_k=min(stage2_size, len(stage1_results))
        )

        if stage2_results.empty:
            stage2_results = stage1_results.head(stage2_size)

        if progress_callback:
            progress_callback('stage2_done', len(stage2_results))

        # Stage 3: Hybrid 최종 선별
        if progress_callback:
            progress_callback('stage3_start', None)

        if len(stage2_results) <= stage3_size:
            stage3_results = stage2_results
        else:
            stage3_results = self._apply_hybrid_rerank(
                stage2_results,
                query,
                top_k=stage3_size
            )

        if progress_callback:
            progress_callback('stage3_done', len(stage3_results))

        result = {
            'stage1_count': len(stage1_results),
            'stage2_count': len(stage2_results),
            'stage3_count': len(stage3_results),
            'final_results': stage3_results
        }

        # Stage 4: 계층적 요약
        if enable_summary and not stage3_results.empty:
            if progress_callback:
                progress_callback('map_reduce_start', len(stage3_results))

            summary = self._hierarchical_summarize(
                stage3_results,
                query,
                chunk_size,
                progress_callback
            )
            result['summary'] = summary

            if progress_callback:
                progress_callback('map_reduce_done', None)
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
        from analyzer.txt_mining.tokenizer import get_tokenizer_for_channel

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
        vector_scores = df['similarity'].astype(float).values
        bm25_scores = df['bm25_score'].astype(float).values

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
        chunk_size: int,
        progress_callback=None
    ) -> str:
        """
        계층적 요약 (Map-Reduce 패턴)

        Args:
            df: 리뷰 DataFrame
            query: 원본 쿼리
            chunk_size: 청크 크기
            progress_callback: 진행상황 콜백

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
        total_chunks = len(chunks)

        for i, chunk in enumerate(chunks, 1):
            if progress_callback:
                progress_callback('map_progress', (i, total_chunks))

            summary = self._summarize_chunk(chunk, query, i)
            if summary:
                chunk_summaries.append(summary)

        if not chunk_summaries:
            return "요약 생성 실패"

        if len(chunk_summaries) == 1:
            return chunk_summaries[0]

        # Reduce: 청크 요약들을 다시 요약
        if progress_callback:
            progress_callback('reduce_start', len(chunk_summaries))

        final_summary = self._reduce_summaries(chunk_summaries, query)

        return final_summary

    def _summarize_direct(
        self,
        reviews: List[str],
        query: str
    ) -> str:
        """소량 리뷰 직접 요약"""

        # 개선: 20개까지 보여주고 300자까지
        reviews_text = "\n".join([
            f"{i+1}. {r[:300]}"
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
        """단일 청크 요약 (개선된 프롬프트 사용)"""

        # 개선된 map_prompt 사용
        prompt = create_map_prompt(reviews, query, chunk_num)

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "화장품 리뷰 분석 전문가"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800  # Map prompt가 구조화된 출력이므로 더 많은 토큰 필요
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return None

    def _reduce_summaries(
        self,
        summaries: List[str],
        query: str
    ) -> str:
        """여러 요약을 하나로 통합 (개선된 프롬프트 사용)"""

        # 개선된 reduce_prompt 사용
        prompt = create_reduce_prompt(summaries, query)

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "화장품 리뷰 분석 전문가이자 마케팅 컨설턴트"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000  # Reduce prompt는 최종 보고서이므로 충분한 토큰 필요
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return "\n\n".join(summaries)

    def close(self):
        """연결 종료"""
        self.vector_tool.close()
        self.bm25_tool.close()
        self.hybrid_tool.close()
