#//==============================================================================//#
"""
orchestrator.py
V4 ReAct Agent Orchestrator

ReAct 패턴으로 전체 워크플로우 조율:
1. QueryHandler: 쿼리 파싱
2. HierarchicalRetrieval: 계층적 검색 + Map-Reduce
3. 자연어 진행상황 메시지

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

from typing import Dict, Optional, Callable
import logging

from .query_handler import QueryHandler
from .hierarchical_retrieval import HierarchicalRetrieval
from .playbooks.strategies import get_playbook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#//==============================================================================//#
# Orchestrator
#//==============================================================================//#

class Orchestrator:
    """
    V4 ReAct Agent Orchestrator

    ReAct 패턴:
    - Thought: 쿼리 분석, Playbook 선택
    - Action: HierarchicalRetrieval 실행
    - Observation: 결과 확인 및 반환
    """

    def __init__(self, api_key: str):
        """
        초기화

        Args:
            api_key: OpenAI API Key
        """
        self.api_key = api_key
        self.query_handler = QueryHandler(api_key)
        self.retrieval = HierarchicalRetrieval(api_key)

        logger.info("Orchestrator initialized")

    def process_query(
        self,
        user_query: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        사용자 질문 처리 (ReAct 패턴)

        Args:
            user_query: 사용자 질문
            progress_callback: 진행상황 콜백 함수

        Returns:
            {
                'answer': str,  # 최종 답변
                'parsed': Dict,  # 파싱된 쿼리
                'stats': Dict,  # 통계 정보
                'playbook': Dict  # 사용된 Playbook
            }
        """

        logger.info(f"Processing query: {user_query}")

        # Thought 1: 쿼리 분석
        if progress_callback:
            progress_callback('query_parsing_start', user_query)

        parsed = self.query_handler.handle(user_query)

        if progress_callback:
            progress_callback('query_parsing_done', parsed)

        # Thought 2: Playbook 선택
        playbook = get_playbook(parsed['query_type'])
        logger.info(f"Selected playbook: {parsed['query_type']}")

        # Action: 계층적 검색 + Map-Reduce
        filters = self._build_filters(parsed)
        search_query = self._build_search_query(parsed, user_query)

        logger.info(f"Search query: '{search_query}' | Filters: {filters}")

        results = self.retrieval.retrieve(
            query=search_query,
            filters=filters,
            stage1_size=10000,  # Vector 검색 (넓게)
            stage2_size=1000,   # BM25 재정렬
            stage3_size=200,    # Hybrid 최종 선별 (속도 개선: 200건으로 고정)
            enable_summary=True,
            progress_callback=progress_callback
        )

        # Observation: 결과 확인
        if 'error' in results:
            logger.error(f"Retrieval error: {results['error']}")
            return {
                'answer': f"죄송합니다. {results['error']}",
                'parsed': parsed,
                'stats': {
                    'stage1': 0,
                    'stage2': 0,
                    'stage3': 0
                },
                'playbook': playbook,
                'error': results['error']
            }

        # 성공
        return {
            'answer': results['summary'],
            'parsed': parsed,
            'stats': {
                'stage1': results['stage1_count'],
                'stage2': results['stage2_count'],
                'stage3': results['stage3_count']
            },
            'playbook': playbook
        }

    def _build_filters(self, parsed: Dict) -> Dict:
        """
        파싱된 쿼리에서 필터 생성

        Args:
            parsed: 파싱된 쿼리

        Returns:
            필터 딕셔너리
        """
        filters = {}

        if parsed.get('brands') and len(parsed['brands']) > 0:
            filters['brand'] = parsed['brands'][0]  # 첫 번째 브랜드

        if parsed.get('channels') and len(parsed['channels']) > 0:
            if len(parsed['channels']) == 1:
                filters['channel'] = parsed['channels'][0]
            else:
                filters['channels'] = parsed['channels']  # 복수 채널

        # 제품명 필터 (keywords가 있으면 product_name LIKE로 사용)
        if parsed.get('keywords') and len(parsed['keywords']) > 0:
            # 첫 번째 키워드를 제품명으로 간주
            product_keyword = parsed['keywords'][0]
            filters['product_name_like'] = f"%{product_keyword}%"
            logger.info(f"Product name filter: {filters['product_name_like']}")

        # 향후 확장: date_from, date_to, min_rating 등

        return filters

    def _build_search_query(self, parsed: Dict, original_query: str) -> str:
        """
        파싱된 쿼리에서 Vector Search용 검색어 재구성

        제품명이 keywords에 있으면 이미 SQL 필터로 처리되므로,
        Vector Search는 브랜드나 속성만 사용하여 랭킹

        Args:
            parsed: 파싱된 쿼리
            original_query: 원본 질문

        Returns:
            재구성된 검색 쿼리
        """
        query_type = parsed.get('query_type', 'general_analysis')
        keywords = parsed.get('keywords', [])
        aspects = parsed.get('aspects', [])
        brands = parsed.get('brands', [])

        # 1. general_analysis: 제품명은 SQL 필터로 처리됨
        #    Vector Search는 브랜드만 사용 (또는 일반 리뷰 표현 매칭)
        if query_type == 'general_analysis':
            if brands:
                # 제품명은 이미 필터링했으니, 브랜드만으로 검색
                return brands[0]
            # 브랜드도 없으면 원본 쿼리
            else:
                return original_query

        # 2. aspect_analysis: aspects를 주요 검색어로 사용
        #    제품명은 SQL 필터로 처리됨
        elif query_type == 'aspect_analysis':
            if aspects:
                # aspects를 주요 검색어로 (제품명은 필터에서 처리)
                return ' '.join(aspects)
            # aspects 없으면 브랜드
            elif brands:
                return brands[0]
            else:
                return original_query

        # 3. comparison_analysis: brands 조합
        elif query_type == 'comparison_analysis':
            if brands:
                return ' '.join(brands)
            else:
                return original_query

        # 4. keyword_extraction: 브랜드 사용
        elif query_type == 'keyword_extraction':
            if brands:
                return brands[0]
            else:
                return original_query

        # 기타: 원본 쿼리
        else:
            return original_query

    def create_intent_message(self, parsed: Dict) -> str:
        """
        파싱된 쿼리를 자연어 메시지로 변환

        Args:
            parsed: 파싱된 쿼리

        Returns:
            자연어 메시지
        """
        parts = []

        if parsed.get('brands'):
            parts.append(f"{parsed['brands'][0]} 브랜드의")

        if parsed.get('channels'):
            if len(parsed['channels']) == 1:
                parts.append(f"{parsed['channels'][0]}에서")
            else:
                channel_str = " / ".join(parsed['channels'])
                parts.append(f"{channel_str}에서")

        if parsed.get('keywords'):
            parts.append(f"{' '.join(parsed['keywords'])}")

        if parsed.get('aspects'):
            parts.append(f"{parsed['aspects'][0]} 관련")

        # 쿼리 타입별 표현
        query_type_desc = {
            'general_analysis': '전반적인 분석을',
            'aspect_analysis': '속성 분석을',
            'comparison_analysis': '비교 분석을',
            'keyword_extraction': '떠오르는 키워드 분석을'
        }

        action = query_type_desc.get(parsed.get('query_type'), '분석을')

        if parts:
            return f"네, {' '.join(parts)} {action} 해드릴게요!"
        else:
            return f"네, 리뷰 {action} 해드릴게요!"

    def close(self):
        """리소스 정리"""
        self.retrieval.close()
