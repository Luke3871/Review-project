#//==============================================================================//#
"""
base_playbook.py
기본 전략 및 규칙

last_updated: 2025.01.16
"""
#//==============================================================================//#

BASE_PLAYBOOK = {
    'version': '1.0',
    'last_updated': '2025-01-16',
    
    # 기본 전략
    'strategies': [
        {
            'id': 'strat-001',
            'type': '검색',
            'content': '대량 리뷰(10만개 이상)는 hierarchical_retrieval 사용',
            'conditions': ['estimated_review_count > 100000'],
            'priority': 1,
            'metadata': {
                'created': '2025-01-16',
                'helpful_count': 0,
                'harmful_count': 0,
                'tags': ['검색', '확장성']
            }
        },
        {
            'id': 'strat-002',
            'type': '검색',
            'content': '소량 리뷰(1천개 이하)는 hybrid_search 사용',
            'conditions': ['estimated_review_count < 1000'],
            'priority': 1,
            'metadata': {
                'created': '2025-01-16',
                'helpful_count': 0,
                'harmful_count': 0,
                'tags': ['검색', '정밀도']
            }
        },
        {
            'id': 'strat-003',
            'type': '분석순서',
            'content': '분석 순서: 감성분석 → ABSA → 키워드 → (선택) 코호트',
            'conditions': [],
            'priority': 1,
            'metadata': {
                'created': '2025-01-16',
                'helpful_count': 0,
                'harmful_count': 0,
                'tags': ['워크플로우']
            }
        }
    ],
    
    # 도구 선택 규칙
    'tool_selection': {
        'hierarchical_retrieval': {
            'description': '대량 데이터 계층적 검색',
            'when': [
                'review_count > 10000',
                'need_summary == true'
            ],
            'default_params': {
                'stage1_size': 100000,
                'stage2_size': 10000,
                'stage3_size': 1000,
                'enable_summary': True
            }
        },
        'hybrid_search': {
            'description': '소량 데이터 정밀 검색',
            'when': [
                'review_count < 1000',
                'need_precision == true'
            ],
            'default_params': {
                'top_k': 100,
                'alpha': 0.7
            }
        },
        'cohort_analysis': {
            'description': '피부타입별 분석 (올리브영 전용)',
            'when': [
                'channel == OliveYoung',
                'query_mentions_skin_type == true'
            ],
            'default_params': {
                'type': 'check',
                'category': 'skincare'
            }
        }
    },
    
    # 일반 규칙
    'rules': [
        {
            'id': 'rule-001',
            'content': '올리브영 채널만 피부타입 데이터 있음',
            'applies_to': ['cohort_analysis']
        },
        {
            'id': 'rule-002',
            'content': 'ABSA 전에 반드시 감성분석 먼저 실행',
            'applies_to': ['absa_analysis']
        },
        {
            'id': 'rule-003',
            'content': '비교 쿼리는 각 브랜드별로 별도 검색 후 통합',
            'applies_to': ['comparison']
        }
    ]
}