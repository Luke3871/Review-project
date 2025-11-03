#//==============================================================================//#
"""
playbook_manager.py
Playbook 관리 (ACE 원칙)

Phase 1: Python Dict 로드 + 조회
Phase 2: Delta update (나중에)

last_updated: 2025.01.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#//==============================================================================//#
# PlaybookManager
#//==============================================================================//#

class PlaybookManager:
    """
    Playbook 관리
    
    ACE 원칙:
    - Context as Playbook
    - Structured bullets
    - Incremental updates (Phase 2)
    """
    
    def __init__(self):
        """
        초기화
        Python Dict 기반 Playbook 로드
        """
        self.playbooks = {}
        self._load_all_playbooks()
        
        logger.info(f"PlaybookManager initialized with {len(self.playbooks)} playbooks")
    
    def _load_all_playbooks(self):
        """Playbook 모듈 import"""
        
        try:
            # base_playbook import
            from playbooks.base_playbook import BASE_PLAYBOOK
            self.playbooks['base_playbook'] = BASE_PLAYBOOK
            logger.info("✓ Loaded base_playbook")
            
            # analysis_patterns import
            from playbooks.analysis_patterns import ANALYSIS_PATTERNS
            self.playbooks['analysis_patterns'] = ANALYSIS_PATTERNS
            logger.info("✓ Loaded analysis_patterns")
            
        except Exception as e:
            logger.error(f"Failed to load playbooks: {e}")
            import traceback
            traceback.print_exc()
    
    def get_base_strategies(self) -> List[Dict]:
        """
        기본 전략 반환
        
        Returns:
            [
                {'id': 'strat-001', 'type': '검색', 'content': '...'},
                ...
            ]
        """
        
        if 'base_playbook' not in self.playbooks:
            logger.warning("base_playbook not found")
            return []
        
        strategies = self.playbooks['base_playbook'].get('strategies', [])
        logger.info(f"Retrieved {len(strategies)} base strategies")
        
        return strategies
    
    def get_tool_selection_rules(self) -> Dict:
        """
        도구 선택 규칙 반환
        
        Returns:
            {
                'hierarchical_retrieval': {
                    'when': [...],
                    'default_params': {...}
                },
                ...
            }
        """
        
        if 'base_playbook' not in self.playbooks:
            return {}
        
        return self.playbooks['base_playbook'].get('tool_selection', {})
    
    def get_rules(self) -> List[Dict]:
        """
        일반 규칙 반환
        
        Returns:
            [
                {'id': 'rule-001', 'content': '...', 'applies_to': [...]},
                ...
            ]
        """
        
        if 'base_playbook' not in self.playbooks:
            return []
        
        return self.playbooks['base_playbook'].get('rules', [])
    
    def get_analysis_patterns(self) -> List[Dict]:
        """
        분석 패턴 반환
        
        Returns:
            [
                {
                    'id': 'pattern-001',
                    'name': 'aspect_analysis',
                    'triggers': {...},
                    'steps': [...]
                },
                ...
            ]
        """
        
        if 'analysis_patterns' not in self.playbooks:
            logger.warning("analysis_patterns not found")
            return []
        
        patterns = self.playbooks['analysis_patterns'].get('patterns', [])
        logger.info(f"Retrieved {len(patterns)} analysis patterns")
        
        return patterns
    
    def match_pattern(self, query_info: Dict) -> Optional[Dict]:
        """
        쿼리 정보에 맞는 패턴 찾기
        
        Args:
            query_info: {
                'query_type': 'aspect_analysis',
                'keywords': ['보습', '향'],
                'channel': 'OliveYoung',
                ...
            }
        
        Returns:
            매칭된 패턴 Dict 또는 None
        """
        
        patterns = self.get_analysis_patterns()
        
        if not patterns:
            return None
        
        # 우선순위 순서로 매칭
        if 'analysis_patterns' in self.playbooks:
            priority = self.playbooks['analysis_patterns'].get('matching_priority', [])
        else:
            priority = []
        
        # 우선순위 순서대로 체크
        for pattern_name in priority:
            for pattern in patterns:
                if pattern.get('name') == pattern_name:
                    if self._pattern_matches(pattern, query_info):
                        logger.info(f"Matched pattern: {pattern_name}")
                        return pattern
        
        # 우선순위에 없는 패턴들도 체크
        for pattern in patterns:
            if pattern.get('name') not in priority:
                if self._pattern_matches(pattern, query_info):
                    logger.info(f"Matched pattern: {pattern.get('name')}")
                    return pattern
        
        # 매칭 실패 시 기본 패턴
        logger.info("No pattern matched, using default")
        return self._get_default_pattern()
    
    def _pattern_matches(self, pattern: Dict, query_info: Dict) -> bool:
        """
        패턴이 쿼리 정보와 매칭되는지 확인
        
        Args:
            pattern: 패턴 Dict
            query_info: 쿼리 정보 Dict
        
        Returns:
            매칭 여부
        """
        
        triggers = pattern.get('triggers', {})
        
        # 1. Channel 체크 (required_channel 있으면)
        required_channel = triggers.get('required_channel')
        if required_channel:
            if query_info.get('channel') != required_channel:
                return False
        
        # 2. Query type 체크
        if query_info.get('query_type') == pattern.get('name'):
            return True
        
        # 3. Keywords 체크
        pattern_keywords = triggers.get('keywords', [])
        query_keywords = query_info.get('keywords', [])
        
        if pattern_keywords and query_keywords:
            # 하나라도 겹치면 매칭
            for pk in pattern_keywords:
                for qk in query_keywords:
                    if pk.lower() in qk.lower() or qk.lower() in pk.lower():
                        return True
        
        return False
    
    def _get_default_pattern(self) -> Dict:
        """
        기본 패턴 반환
        
        Returns:
            기본 패턴 Dict
        """
        
        if 'analysis_patterns' not in self.playbooks:
            return self._create_fallback_pattern()
        
        default = self.playbooks['analysis_patterns'].get('default_pattern', {})
        
        if not default:
            return self._create_fallback_pattern()
        
        return default
    
    def _create_fallback_pattern(self) -> Dict:
        """
        Fallback 패턴 생성 (Playbook 없을 때)
        
        Returns:
            최소한의 패턴
        """
        
        return {
            'name': 'fallback',
            'description': 'Fallback 패턴',
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
    
    def get_strategies_for_context(self, context: Dict) -> List[Dict]:
        """
        컨텍스트에 맞는 전략들 반환
        
        Args:
            context: {
                'brand': 'VT',
                'channel': 'OliveYoung',
                'estimated_review_count': 50000,
                ...
            }
        
        Returns:
            적용 가능한 전략 리스트
        """
        
        strategies = self.get_base_strategies()
        applicable = []
        
        for strategy in strategies:
            conditions = strategy.get('conditions', [])
            
            # 조건 없으면 항상 적용
            if not conditions:
                applicable.append(strategy)
                continue
            
            # 조건 체크
            if self._check_conditions(conditions, context):
                applicable.append(strategy)
        
        logger.info(f"Found {len(applicable)} applicable strategies")
        
        return applicable
    
    def _check_conditions(self, conditions: List[str], context: Dict) -> bool:
        """
        조건 체크
        
        Args:
            conditions: ['estimated_review_count > 100000', ...]
            context: 컨텍스트 Dict
        
        Returns:
            조건 만족 여부
        """
        
        for condition in conditions:
            try:
                # 간단한 조건 평가
                if '>' in condition:
                    key, value = condition.split('>')
                    key = key.strip()
                    value = int(value.strip())
                    
                    if context.get(key, 0) > value:
                        return True
                
                elif '<' in condition:
                    key, value = condition.split('<')
                    key = key.strip()
                    value = int(value.strip())
                    
                    if context.get(key, float('inf')) < value:
                        return True
                
                elif '==' in condition:
                    key, value = condition.split('==')
                    key = key.strip()
                    value = value.strip()
                    
                    if str(context.get(key, '')) == value:
                        return True
                
            except Exception as e:
                logger.warning(f"Failed to evaluate condition '{condition}': {e}")
                continue
        
        return False
    
    def reload(self):
        """Playbook 다시 로드 (수동 수정 후)"""
        
        logger.info("Reloading playbooks...")
        self.playbooks = {}
        self._load_all_playbooks()
        logger.info("Playbooks reloaded")
    
    def get_playbook_info(self) -> Dict:
        """
        Playbook 정보 반환
        
        Returns:
            {
                'loaded_playbooks': ['base_playbook', 'analysis_patterns'],
                'total_strategies': 10,
                'total_patterns': 4,
                'total_rules': 3
            }
        """
        
        base_strategies = self.get_base_strategies()
        patterns = self.get_analysis_patterns()
        rules = self.get_rules()
        
        return {
            'loaded_playbooks': list(self.playbooks.keys()),
            'total_strategies': len(base_strategies),
            'total_patterns': len(patterns),
            'total_rules': len(rules)
        }
