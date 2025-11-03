#//==============================================================================//#
"""
executor.py
실행 계획 실행

Plan을 받아서 Step별로 Tool 호출
- Tool Registry 패턴
- ExecutionMemory로 데이터 관리
- 재시도 로직
- 진행상황 Callback

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

from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime
import time
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#//==============================================================================//#
# ExecutionMemory
#//==============================================================================//#

class ExecutionMemory:
    """
    Step 간 데이터 공유 메모리
    
    실행 중 생성된 데이터를 저장하고 관리
    """
    
    def __init__(self):
        """초기화"""
        self.data = {}
        self.metadata = {}
        
        logger.info("ExecutionMemory initialized")
    
    def store(self, key: str, value: Any, metadata: Dict = None):
        """
        데이터 저장
        
        Args:
            key: 저장 키 (예: 'reviews', 'sentiment')
            value: 저장 값
            metadata: 메타정보 (크기, 시간 등)
        """
        self.data[key] = value
        
        if metadata:
            self.metadata[key] = metadata
        else:
            # 자동으로 메타정보 생성
            self.metadata[key] = {
                'timestamp': datetime.now().isoformat(),
                'type': type(value).__name__,
                'size': self._get_size(value)
            }
        
        logger.debug(f"Stored '{key}' in memory")
    
    def get(self, key: str, default=None) -> Any:
        """
        데이터 조회
        
        Args:
            key: 조회 키
            default: 기본값
        
        Returns:
            저장된 값 또는 기본값
        """
        return self.data.get(key, default)
    
    def has(self, key: str) -> bool:
        """
        데이터 존재 확인
        
        Args:
            key: 확인할 키
        
        Returns:
            존재 여부
        """
        return key in self.data
    
    def get_metadata(self, key: str) -> Dict:
        """
        메타정보 조회
        
        Args:
            key: 메타정보 키
        
        Returns:
            메타정보 Dict
        """
        return self.metadata.get(key, {})
    
    def keys(self) -> List[str]:
        """
        모든 키 반환
        
        Returns:
            키 리스트
        """
        return list(self.data.keys())
    
    def clear(self):
        """메모리 초기화"""
        self.data.clear()
        self.metadata.clear()
        logger.info("Memory cleared")
    
    def summary(self) -> Dict:
        """
        메모리 상태 요약
        
        Returns:
            요약 정보
        """
        return {
            'total_keys': len(self.data),
            'keys': list(self.data.keys()),
            'metadata': self.metadata
        }
    
    def _get_size(self, value):
        """
        데이터 크기 추정
        
        Args:
            value: 값
        
        Returns:
            크기 정보
        """
        if hasattr(value, 'shape'):  # DataFrame, Array
            return value.shape
        elif isinstance(value, (list, dict)):
            return len(value)
        else:
            return None


#//==============================================================================//#
# Executor
#//==============================================================================//#

class Executor:
    """
    실행 계획 실행
    
    Tool Registry 패턴으로 동적 Tool 호출
    """
    
    def __init__(self, db_config: Dict, api_key: str):
        """
        초기화
        
        Args:
            db_config: DB 설정
            api_key: OpenAI API Key (LLM용)
        """
        self.db_config = db_config
        self.api_key = api_key
        self.memory = ExecutionMemory()
        
        logger.info("Executor initialized")
    
    def execute_plan(
        self, 
        plan: Dict, 
        callback: Optional[Callable] = None
    ) -> Dict:
        """
        실행 계획 실행
        
        Args:
            plan: Planner 결과
            callback: 진행상황 콜백 함수
                      callback(step_num, total_steps, message)
        
        Returns:
            실행 결과 Dict
        """
        
        logger.info(f"Executing plan with {plan['total_steps']} steps")
        
        start_time = time.time()
        steps = plan['steps']
        
        # 메모리 초기화
        self.memory.clear()
        
        # Step별 실행
        for step in steps:
            step_num = step['step']
            total_steps = len(steps)
            
            logger.info(f"Step {step_num}/{total_steps}: {step['action']} - {step['tool']}")
            
            # 진행상황 콜백
            if callback:
                callback(step_num, total_steps, step['reason'])
            
            try:
                # Step 실행 (재시도 포함)
                result = self._execute_step_with_retry(step)
                
                # 결과 저장
                output_key = step.get('expected_output', f"step_{step_num}_result")
                self.memory.store(output_key, result)
                
                logger.info(f"Step {step_num} completed: {output_key}")
                
            except Exception as e:
                logger.error(f"Step {step_num} failed: {e}")
                
                # Critical step이면 중단
                if step.get('critical', True):
                    raise Exception(f"Critical step {step_num} failed: {e}")
                else:
                    logger.warning(f"Non-critical step {step_num} failed, continuing...")
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"Plan execution completed in {elapsed_time:.2f}s")
        
        return {
            'success': True,
            'elapsed_time': elapsed_time,
            'results': self.memory.data,
            'metadata': self.memory.metadata
        }
    
    def _execute_step_with_retry(
        self, 
        step: Dict, 
        max_retry: int = 3
    ) -> Any:
        """
        재시도 로직 포함 Step 실행
        
        Args:
            step: Step Dict
            max_retry: 최대 재시도 횟수
        
        Returns:
            실행 결과
        """
        
        for attempt in range(max_retry):
            try:
                return self._execute_step(step)
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retry} failed: {e}")
                
                if attempt == max_retry - 1:
                    # 마지막 시도 실패
                    raise
                
                # 재시도 전 대기
                time.sleep(1)
    
    def _execute_step(self, step: Dict) -> Any:
        """
        실제 Step 실행
        
        Args:
            step: Step Dict
        
        Returns:
            실행 결과
        """
        
        action = step['action']
        tool_name = step['tool']
        params = step.get('params', {})
        
        # Action별 처리
        if action == 'search':
            return self._execute_search(tool_name, params)
        
        elif action == 'analyze':
            return self._execute_analyze(tool_name, params)
        
        elif action == 'compare':
            return self._execute_compare(tool_name, params)
        
        elif action == 'check':
            return self._execute_check(tool_name, params)
        
        elif action == 'extract':
            return self._execute_extract(tool_name, params)
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _execute_search(self, tool_name: str, params: Dict) -> Any:
        """
        검색 Tool 실행
        
        Args:
            tool_name: Tool 이름
            params: 파라미터
        
        Returns:
            검색 결과 (DataFrame)
        """
        
        if tool_name == 'hierarchical_retrieval':
            from tools.hierarchical_retrieval import HierarchicalRetrieval
            
            tool = HierarchicalRetrieval(
                db_config=self.db_config,
                api_key=self.api_key
            )
            
            result = tool.retrieve(
                query=params.get('query', ''),
                filters=params.get('filters', {}),
                stage1_size=params.get('stage1_size', 100000),
                stage2_size=params.get('stage2_size', 10000),
                stage3_size=params.get('stage3_size', 1000),
                enable_summary=params.get('enable_summary', True)
            )
            
            # retrieve()는 Dict 반환 {'final_results': DataFrame, ...}
            return result.get('final_results', pd.DataFrame())
        
        elif tool_name == 'hybrid_search':
            from tools.hybrid_search import HybridSearchTool
            
            tool = HybridSearchTool(db_config=self.db_config)
            
            result = tool.search(
                query=params.get('query', ''),
                filters=params.get('filters', {}),
                top_k=params.get('top_k', 100),
                alpha=params.get('alpha', 0.7)
            )
            
            return result
        
        else:
            raise ValueError(f"Unknown search tool: {tool_name}")
    
    def _execute_analyze(self, tool_name: str, params: Dict) -> Any:
        """
        분석 Tool 실행
        
        Args:
            tool_name: Tool 이름
            params: 파라미터
        
        Returns:
            분석 결과
        """
        
        if tool_name == 'sentiment_analysis':
            from core_v2.sentiment_analysis import SentimentAnalyzer
            
            # Memory에서 리뷰 데이터 가져오기
            reviews = self.memory.get('reviews_dataframe')
            if reviews is None or reviews.empty:
                raise ValueError("Reviews data not found in memory")
            
            tool = SentimentAnalyzer()
            result = tool.analyze(reviews)
            
            return result
        
        elif tool_name == 'absa_analysis':
            from core_v2.sentiment_analysis import ABSAAnalyzer
            
            reviews = self.memory.get('reviews_dataframe')
            if reviews is None or reviews.empty:
                raise ValueError("Reviews data not found in memory")
            
            tool = ABSAAnalyzer()
            result = tool.analyze(
                reviews,
                category=params.get('category', 'skincare')
            )
            
            return result
        
        elif tool_name == 'keyword_extraction':
            from core_v2.keyword_analysis import KeywordAnalyzer
            
            reviews = self.memory.get('reviews_dataframe')
            if reviews is None or reviews.empty:
                raise ValueError("Reviews data not found in memory")
            
            tool = KeywordAnalyzer()
            result = tool.extract_keywords(
                reviews,
                keyword_type=params.get('type', 'general'),
                target=params.get('target'),
                with_sentiment=params.get('with_sentiment', False)
            )
            
            return result
        
        elif tool_name == 'cohort_analysis':
            from core_v2.cohort_analysis import CohortAnalyzer
            
            reviews = self.memory.get('reviews_dataframe')
            if reviews is None or reviews.empty:
                raise ValueError("Reviews data not found in memory")
            
            tool = CohortAnalyzer()
            
            analysis_type = params.get('type', 'analyze')
            
            if analysis_type == 'check':
                result = tool.check_availability(reviews)
            else:
                result = tool.analyze_by_skin_type(
                    reviews,
                    category=params.get('category', 'skincare')
                )
            
            return result
        
        else:
            raise ValueError(f"Unknown analyze tool: {tool_name}")
    
    def _execute_compare(self, tool_name: str, params: Dict) -> Any:
        """
        비교 Tool 실행
        
        Args:
            tool_name: Tool 이름
            params: 파라미터
        
        Returns:
            비교 결과
        """
        
        if tool_name == 'comparison_aggregator':
            # Memory에서 브랜드별 결과 수집
            brands = params.get('brands', [])
            compare_on = params.get('compare_on', ['sentiment', 'keywords'])
            
            comparison_data = {}
            
            for idx, brand in enumerate(brands):
                brand_data = {}
                
                # 각 브랜드별 결과 가져오기
                if 'sentiment' in compare_on:
                    sentiment_key = f'brand_{idx+1}_sentiment'
                    brand_data['sentiment'] = self.memory.get(sentiment_key)
                
                if 'keywords' in compare_on:
                    keywords_key = f'brand_{idx+1}_keywords'
                    brand_data['keywords'] = self.memory.get(keywords_key)
                
                comparison_data[brand] = brand_data
            
            # 간단한 비교 결과 생성
            result = {
                'brands': brands,
                'comparison': comparison_data,
                'summary': self._create_comparison_summary(comparison_data)
            }
            
            return result
        
        else:
            raise ValueError(f"Unknown compare tool: {tool_name}")
    
    def _execute_check(self, tool_name: str, params: Dict) -> Any:
        """
        체크 Tool 실행
        
        Args:
            tool_name: Tool 이름
            params: 파라미터
        
        Returns:
            체크 결과
        """
        
        # cohort_analysis의 check는 _execute_analyze에서 처리
        return self._execute_analyze(tool_name, params)
    
    def _execute_extract(self, tool_name: str, params: Dict) -> Any:
        """
        추출 Tool 실행
        
        Args:
            tool_name: Tool 이름
            params: 파라미터
        
        Returns:
            추출 결과
        """
        
        if tool_name == 'query_parser':
            # 간단한 쿼리 파싱 (이미 QueryHandler에서 했으므로 스킵 가능)
            logger.info("Query parsing already done by QueryHandler")
            return {'status': 'skipped'}
        
        else:
            raise ValueError(f"Unknown extract tool: {tool_name}")
    
    def _create_comparison_summary(self, comparison_data: Dict) -> Dict:
        """
        비교 요약 생성
        
        Args:
            comparison_data: 브랜드별 데이터
        
        Returns:
            요약 Dict
        """
        
        summary = {}
        
        # 간단한 요약 (나중에 개선)
        for brand, data in comparison_data.items():
            summary[brand] = {
                'has_sentiment': data.get('sentiment') is not None,
                'has_keywords': data.get('keywords') is not None
            }
        
        return summary


#//==============================================================================//#
# 테스트
#//==============================================================================//#

if __name__ == '__main__':
    # 테스트용 설정
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'cosmetic_reviews',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Callback 함수
    def progress_callback(step_num, total_steps, message):
        print(f"[{step_num}/{total_steps}] {message}")
    
    try:
        # Executor 초기화
        executor = Executor(db_config, api_key)
        
        # 테스트 Plan (간단한 속성 분석)
        test_plan = {
            'steps': [
                {
                    'step': 1,
                    'action': 'search',
                    'tool': 'hybrid_search',
                    'params': {
                        'query': 'VT',
                        'filters': {'brand': 'VT'},
                        'top_k': 100
                    },
                    'reason': 'VT 브랜드 리뷰 검색',
                    'expected_output': 'reviews_dataframe',
                    'critical': True
                },
                {
                    'step': 2,
                    'action': 'analyze',
                    'tool': 'sentiment_analysis',
                    'params': {},
                    'reason': '감성 분석',
                    'expected_output': 'sentiment_labels',
                    'critical': True
                }
            ],
            'total_steps': 2,
            'pattern_used': 'test',
            'strategies_applied': []
        }
        
        print("="*60)
        print("Testing Executor")
        print("="*60)
        
        # Plan 실행
        result = executor.execute_plan(test_plan, callback=progress_callback)
        
        print(f"\n{'='*60}")
        print("Execution Result")
        print("="*60)
        print(f"Success: {result['success']}")
        print(f"Elapsed Time: {result['elapsed_time']:.2f}s")
        print(f"Results Keys: {list(result['results'].keys())}")
        
        print(f"\n{'='*60}")
        print("Memory Summary")
        print("="*60)
        summary = executor.memory.summary()
        print(f"Total Keys: {summary['total_keys']}")
        for key in summary['keys']:
            meta = summary['metadata'].get(key, {})
            print(f"  - {key}: {meta.get('type')} (size: {meta.get('size')})")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()