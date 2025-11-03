#//==============================================================================//#
"""
planner.py
실행 계획 수립

QueryHandler 결과 + PlaybookManager 전략
→ 단계별 실행 계획 생성

last_updated: 2025.01.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
agents_v2_dir = os.path.dirname(current_file)
analytics_dir = os.path.dirname(agents_v2_dir)

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from typing import Dict, List, Optional
import logging
from copy import deepcopy

from agents_v2.playbook_manager import PlaybookManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#//==============================================================================//#
# Planner
#//==============================================================================//#

class Planner:
    """
    실행 계획 수립
    
    규칙 기반으로 Pattern + Strategy 적용
    """
    
    def __init__(self, playbook_manager: PlaybookManager):
        """
        초기화
        
        Args:
            playbook_manager: PlaybookManager 인스턴스
        """
        self.playbook = playbook_manager
        
        logger.info("Planner initialized")
    
    def create_plan(self, query_info: Dict) -> Dict:
        """
        실행 계획 생성
        
        Args:
            query_info: QueryHandler 결과
        
        Returns:
            실행 계획 Dict
        """
        
        logger.info(f"Creating plan for query_type: {query_info.get('query_type')}")
        
        # 1. Pattern 매칭
        pattern = self.playbook.match_pattern(query_info)
        
        if not pattern:
            logger.warning("No pattern matched, using fallback")
            pattern = self._create_fallback_pattern()
        
        logger.info(f"Using pattern: {pattern.get('name')}")
        
        # 2. Context 생성
        context = self._create_context(query_info)
        
        # 3. Strategy 가져오기
        strategies = self.playbook.get_strategies_for_context(context)
        logger.info(f"Applied {len(strategies)} strategies")
        
        # 4. Steps 생성
        steps = self._generate_steps(pattern, query_info, strategies)
        
        # 5. 검증
        is_valid = self._validate_plan(steps)
        
        # 6. 예상 시간 계산
        estimated_time = self._estimate_time(steps)
        
        # 7. 최종 Plan
        plan = {
            'steps': steps,
            'pattern_used': pattern.get('name'),
            'strategies_applied': [s['id'] for s in strategies],
            'total_steps': len(steps),
            'estimated_time': estimated_time,
            'is_valid': is_valid
        }
        
        logger.info(f"Plan created: {len(steps)} steps, ~{estimated_time}s")
        
        return plan
    
    def _create_context(self, query_info: Dict) -> Dict:
        """
        Context 생성 (Strategy 적용용)
        
        Args:
            query_info: 쿼리 정보
        
        Returns:
            Context Dict
        """
        
        brands = query_info.get('brands', [])
        
        return {
            'brand': brands[0] if brands else None,
            'brands': brands,
            'channel': query_info.get('channel'),
            'estimated_review_count': query_info.get('estimated_review_count', 0),
            'query_type': query_info.get('query_type'),
            'needs_comparison': query_info.get('needs_comparison', False),
            'needs_skin_type': query_info.get('needs_skin_type', False)
        }
    
    def _generate_steps(
        self, 
        pattern: Dict, 
        query_info: Dict, 
        strategies: List[Dict]
    ) -> List[Dict]:
        """
        Steps 생성
        
        Args:
            pattern: 매칭된 패턴
            query_info: 쿼리 정보
            strategies: 적용할 전략들
        
        Returns:
            Step 리스트
        """
        
        steps = []
        step_num = 1
        
        pattern_steps = pattern.get('steps', [])
        
        # 비교 쿼리 특수 처리
        if query_info.get('needs_comparison') and len(query_info.get('brands', [])) > 1:
            steps = self._generate_comparison_steps(
                query_info, 
                strategies, 
                step_num
            )
        else:
            # 일반 패턴 steps 처리
            for pattern_step in pattern_steps:
                step = self._fill_step_parameters(
                    pattern_step, 
                    query_info, 
                    strategies, 
                    step_num
                )
                steps.append(step)
                step_num += 1
        
        return steps
    
    def _generate_comparison_steps(
        self, 
        query_info: Dict, 
        strategies: List[Dict],
        start_step: int
    ) -> List[Dict]:
        """
        비교 쿼리 Steps 생성 (동적)
        
        각 브랜드별로 search + analyze 반복
        
        Args:
            query_info: 쿼리 정보
            strategies: 전략들
            start_step: 시작 step 번호
        
        Returns:
            Step 리스트
        """
        
        steps = []
        step_num = start_step
        brands = query_info.get('brands', [])
        
        logger.info(f"Generating comparison steps for {len(brands)} brands")
        
        for idx, brand in enumerate(brands):
            # Search step
            search_step = {
                'step': step_num,
                'action': 'search',
                'tool': self._select_search_tool(query_info, strategies),
                'params': self._get_search_params(brand, query_info, strategies),
                'reason': f"{brand} - 브랜드 리뷰 수집 ({idx+1}/{len(brands)})",
                'expected_output': f'brand_{idx+1}_reviews'
            }
            steps.append(search_step)
            step_num += 1
            
            # Analyze step (sentiment)
            analyze_step = {
                'step': step_num,
                'action': 'analyze',
                'tool': 'sentiment_analysis',
                'params': {},
                'reason': f"{brand} - 감성 분석",
                'expected_output': f'brand_{idx+1}_sentiment'
            }
            steps.append(analyze_step)
            step_num += 1
            
            # Keyword step
            keyword_step = {
                'step': step_num,
                'action': 'analyze',
                'tool': 'keyword_extraction',
                'params': {
                    'type': 'brand',
                    'target': brand,
                    'with_sentiment': True
                },
                'reason': f"{brand} - 키워드 추출",
                'expected_output': f'brand_{idx+1}_keywords'
            }
            steps.append(keyword_step)
            step_num += 1
        
        # 최종 비교 step
        compare_step = {
            'step': step_num,
            'action': 'compare',
            'tool': 'comparison_aggregator',
            'params': {
                'brands': brands,
                'compare_on': ['sentiment', 'keywords']
            },
            'reason': '브랜드 간 비교 결과 집계',
            'expected_output': 'comparison_result'
        }
        steps.append(compare_step)
        
        return steps
    
    def _fill_step_parameters(
        self, 
        pattern_step: Dict, 
        query_info: Dict, 
        strategies: List[Dict],
        step_num: int
    ) -> Dict:
        """
        Pattern step의 파라미터 채우기
        
        Args:
            pattern_step: 패턴의 step
            query_info: 쿼리 정보
            strategies: 전략들
            step_num: step 번호
        
        Returns:
            완성된 step
        """
        
        step = deepcopy(pattern_step)
        step['step'] = step_num
        
        # tool이 없으면 기본값 설정
        if 'tool' not in step:
            step['tool'] = None
        
        # action별 처리
        if step['action'] == 'search':
            brands = query_info.get('brands', [])
            brand = brands[0] if brands else None
            
            step['tool'] = self._select_search_tool(query_info, strategies)
            step['params'] = self._get_search_params(brand, query_info, strategies)
        
        elif step['action'] == 'extract':
            # extract는 query_parser 사용
            if not step.get('tool'):
                step['tool'] = 'query_parser'
        
        elif step['action'] == 'analyze':
            tool = step.get('tool')
            
            if tool == 'absa_analysis':
                step['params'] = {
                    'category': 'skincare'
                }
            
            elif tool == 'keyword_extraction':
                brands = query_info.get('brands', [])
                brand = brands[0] if brands else None
                
                step['params'] = {
                    'type': 'brand' if brand else 'general',
                    'target': brand,
                    'with_sentiment': True
                }
            
            elif tool == 'cohort_analysis':
                step['params'] = {
                    'type': step.get('params', {}).get('type', 'analyze'),
                    'category': 'skincare'
                }
        
        elif step['action'] == 'analyze_batch':
            # analyze_batch는 tools (복수)
            if 'tool' not in step or not step['tool']:
                step['tool'] = 'batch_analyzer'
        
        elif step['action'] == 'compare':
            # compare는 aggregator
            if not step.get('tool'):
                step['tool'] = 'comparison_aggregator'
        
        elif step['action'] == 'check':
            # check는 validator
            if not step.get('tool'):
                step['tool'] = 'validator'
        
        # from_query 치환
        params = step.get('params', {})
        self._replace_from_query(params, query_info)
        
        # expected_output 추가
        if 'expected_output' not in step:
            step['expected_output'] = self._infer_expected_output(step)
        
        return step
    
    def _select_search_tool(
        self, 
        query_info: Dict, 
        strategies: List[Dict]
    ) -> str:
        """
        검색 도구 선택
        
        Args:
            query_info: 쿼리 정보
            strategies: 전략들
        
        Returns:
            도구명
        """
        
        review_count = query_info.get('estimated_review_count', 0)
        
        # Strategy 기반 선택
        for strategy in strategies:
            if strategy.get('type') == '검색':
                conditions = strategy.get('conditions', [])
                
                for condition in conditions:
                    if '>' in condition and review_count > 100000:
                        return 'hierarchical_retrieval'
                    elif '<' in condition and review_count < 1000:
                        return 'hybrid_search'
        
        # 기본값
        if review_count > 10000:
            return 'hierarchical_retrieval'
        else:
            return 'hybrid_search'
    
    def _get_search_params(
        self, 
        brand: Optional[str],
        query_info: Dict, 
        strategies: List[Dict]
    ) -> Dict:
        """
        검색 파라미터 생성
        
        Args:
            brand: 브랜드명
            query_info: 쿼리 정보
            strategies: 전략들
        
        Returns:
            파라미터 Dict
        """
        
        # 쿼리 문자열 생성
        if brand:
            query_str = brand
        else:
            # 브랜드 없으면 키워드 사용
            keywords = query_info.get('keywords', [])
            if keywords:
                query_str = ' '.join(keywords)
            else:
                query_str = query_info.get('original_query', '')
        
        params = {
            'query': query_str,
            'filters': {}
        }
        
        # 브랜드 필터
        if brand:
            params['filters']['brand'] = brand
        
        # 채널 필터
        if query_info.get('channel'):
            params['filters']['channel'] = query_info['channel']
        
        # Tool selection 규칙에서 default_params 가져오기
        tool_rules = self.playbook.get_tool_selection_rules()
        
        review_count = query_info.get('estimated_review_count', 0)
        
        if review_count > 10000:
            tool_name = 'hierarchical_retrieval'
        else:
            tool_name = 'hybrid_search'
        
        if tool_name in tool_rules:
            default_params = tool_rules[tool_name].get('default_params', {})
            params.update(default_params)
        
        return params
    
    def _replace_from_query(self, params: Dict, query_info: Dict):
        """
        파라미터의 'from_query' 값 치환 (in-place)
        
        Args:
            params: 파라미터 Dict
            query_info: 쿼리 정보
        """
        
        for key, value in list(params.items()):
            if isinstance(value, str) and value == 'from_query':
                # brand 추출
                if key == 'brand':
                    brands = query_info.get('brands', [])
                    params[key] = brands[0] if brands else None
                elif key == 'channel':
                    params[key] = query_info.get('channel')
            
            elif isinstance(value, dict):
                self._replace_from_query(value, query_info)
    
    def _infer_expected_output(self, step: Dict) -> str:
        """
        예상 출력 추론
        
        Args:
            step: Step Dict
        
        Returns:
            출력 타입
        """
        
        action = step.get('action')
        tool = step.get('tool')
        
        if action == 'search':
            return 'reviews_dataframe'
        elif tool == 'sentiment_analysis':
            return 'sentiment_labels'
        elif tool == 'absa_analysis':
            return 'aspect_sentiments'
        elif tool == 'keyword_extraction':
            return 'keywords_list'
        elif tool == 'cohort_analysis':
            return 'cohort_analysis_result'
        elif tool == 'comparison_aggregator':
            return 'comparison_result'
        else:
            return 'unknown'
    
    def _validate_plan(self, steps: List[Dict]) -> bool:
        """
        계획 검증
        
        Args:
            steps: Step 리스트
        
        Returns:
            검증 통과 여부
        """
        
        if not steps:
            logger.error("No steps in plan")
            return False
        
        # 첫 step은 search여야 함 (일반적으로)
        if steps[0]['action'] not in ['search', 'extract']:
            logger.warning("First step should typically be 'search' or 'extract'")
        
        # sentiment_analysis가 absa_analysis 전에 와야 함
        sentiment_idx = None
        absa_idx = None
        
        for idx, step in enumerate(steps):
            if step.get('tool') == 'sentiment_analysis':
                sentiment_idx = idx
            elif step.get('tool') == 'absa_analysis':
                absa_idx = idx
        
        if absa_idx is not None and sentiment_idx is not None:
            if sentiment_idx > absa_idx:
                logger.warning("sentiment_analysis should come before absa_analysis")
                return False
        
        logger.info("Plan validation passed")
        return True
    
    def _estimate_time(self, steps: List[Dict]) -> int:
        """
        예상 실행 시간 계산 (초)
        
        Args:
            steps: Step 리스트
        
        Returns:
            예상 시간 (초)
        """
        
        time_estimates = {
            'hierarchical_retrieval': 60,
            'hybrid_search': 20,
            'sentiment_analysis': 30,
            'absa_analysis': 40,
            'keyword_extraction': 20,
            'cohort_analysis': 30,
            'comparison_aggregator': 10,
            'query_parser': 5
        }
        
        total_time = 0
        
        for step in steps:
            tool = step.get('tool')
            if tool and tool in time_estimates:
                total_time += time_estimates[tool]
            else:
                total_time += 10  # 기본값
        
        return total_time
    
    def _create_fallback_pattern(self) -> Dict:
        """
        Fallback 패턴 생성
        
        Returns:
            최소한의 패턴
        """
        
        return {
            'name': 'fallback',
            'steps': [
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {},
                    'reason': '리뷰 검색'
                },
                {
                    'action': 'analyze',
                    'tool': 'sentiment_analysis',
                    'params': {},
                    'reason': '감성 분석'
                },
                {
                    'action': 'analyze',
                    'tool': 'keyword_extraction',
                    'params': {},
                    'reason': '키워드 추출'
                }
            ]
        }

