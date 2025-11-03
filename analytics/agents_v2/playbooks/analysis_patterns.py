#//==============================================================================//#
"""
analysis_patterns.py
쿼리 타입별 분석 패턴

last_updated: 2025.01.16
"""
#//==============================================================================//#

ANALYSIS_PATTERNS = {
    'version': '1.0',
    'last_updated': '2025-01-16',
    
    # 분석 패턴들
    'patterns': [
        # 패턴 1: 속성 분석
        {
            'id': 'pattern-001',
            'name': 'aspect_analysis',
            'description': '특정 속성(보습, 향 등) 분석',
            'triggers': {
                'keywords': [
                    '보습', '향', '발림성', 
                    '흡수', '지속력', '커버력'
                ],
                'query_patterns': [
                    '어때', '평가', '좋', '나쁨'
                ]
            },
            'steps': [
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {
                        'filters': {
                            'brand': 'from_query'
                        }
                    },
                    'reason': '브랜드 리뷰 수집'
                },
                {
                    'action': 'analyze',
                    'tool': 'sentiment_analysis',
                    'params': {},
                    'reason': '전체 감성 파악'
                },
                {
                    'action': 'analyze',
                    'tool': 'absa_analysis',
                    'params': {
                        'category': 'skincare'
                    },
                    'reason': '속성별 분석'
                },
                {
                    'action': 'analyze',
                    'tool': 'keyword_extraction',
                    'params': {
                        'type': 'brand',
                        'with_sentiment': True
                    },
                    'reason': '구체적 표현 추출'
                }
            ],
            'expected_output': [
                'overall_positive_ratio',
                'aspect_sentiment_breakdown',
                'top_keywords_with_sentiment'
            ],
            'metadata': {
                'frequency': 'high',
                'complexity': 'medium'
            }
        },
        
        # 패턴 2: 비교 분석
        {
            'id': 'pattern-002',
            'name': 'comparison_analysis',
            'description': '브랜드 간 비교 분석',
            'triggers': {
                'keywords': [
                    'vs', '비교', '차이',
                    '더 좋', '어느게'
                ],
                'query_patterns': [
                    'vs', '비교', '차이'
                ]
            },
            'steps': [
                {
                    'action': 'extract',
                    'tool': 'query_parser',
                    'params': {
                        'extract': ['brands']
                    },
                    'reason': '비교 대상 브랜드 추출'
                },
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {
                        'filters': {
                            'brand': 'brand_1'
                        }
                    },
                    'reason': '첫 번째 브랜드 검색'
                },
                {
                    'action': 'analyze_batch',
                    'tools': [
                        'sentiment_analysis',
                        'keyword_extraction'
                    ],
                    'reason': '첫 번째 브랜드 분석'
                },
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {
                        'filters': {
                            'brand': 'brand_2'
                        }
                    },
                    'reason': '두 번째 브랜드 검색'
                },
                {
                    'action': 'analyze_batch',
                    'tools': [
                        'sentiment_analysis',
                        'keyword_extraction'
                    ],
                    'reason': '두 번째 브랜드 분석'
                },
                {
                    'action': 'compare',
                    'tool': 'comparison_aggregator',
                    'params': {
                        'compare_on': [
                            'sentiment',
                            'keywords',
                            'aspects'
                        ]
                    },
                    'reason': '결과 통합 비교'
                }
            ],
            'expected_output': [
                'brand_sentiment_comparison',
                'differentiating_keywords',
                'strengths_weaknesses'
            ],
            'metadata': {
                'frequency': 'medium',
                'complexity': 'high'
            }
        },
        
        # 패턴 3: 피부타입별 분석
        {
            'id': 'pattern-003',
            'name': 'skin_type_analysis',
            'description': '피부타입별 분석 (올리브영 전용)',
            'triggers': {
                'keywords': [
                    '피부타입', '지성', '건성',
                    '민감성', '복합성'
                ],
                'query_patterns': [
                    '피부', '타입'
                ],
                'required_channel': 'OliveYoung'
            },
            'steps': [
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {
                        'filters': {
                            'brand': 'from_query',
                            'channel': 'OliveYoung'
                        }
                    },
                    'reason': '올리브영 리뷰만 수집'
                },
                {
                    'action': 'check',
                    'tool': 'cohort_analysis',
                    'params': {
                        'type': 'check'
                    },
                    'reason': '피부타입 데이터 가용성 확인'
                },
                {
                    'action': 'analyze',
                    'tool': 'cohort_analysis',
                    'params': {
                        'type': 'analyze',
                        'category': 'skincare'
                    },
                    'reason': '피부타입별 분석'
                },
                {
                    'action': 'analyze',
                    'tool': 'sentiment_analysis',
                    'params': {},
                    'reason': '전체 감성 비교 기준'
                }
            ],
            'expected_output': [
                'satisfaction_by_skin_type',
                'keywords_by_skin_type',
                'differences_between_types'
            ],
            'metadata': {
                'frequency': 'low',
                'complexity': 'medium',
                'channel_specific': 'OliveYoung'
            }
        },
        
        # 패턴 4: 트렌드 분석
        {
            'id': 'pattern-004',
            'name': 'trend_analysis',
            'description': '시간에 따른 변화 분석',
            'triggers': {
                'keywords': [
                    '트렌드', '요즘', '최근',
                    '변화', '전보다'
                ],
                'query_patterns': [
                    '요즘', '최근', '트렌드'
                ]
            },
            'steps': [
                {
                    'action': 'search',
                    'tool': 'hierarchical_retrieval',
                    'params': {
                        'filters': {
                            'brand': 'from_query'
                        },
                        'time_windows': [
                            'recent_3months',
                            'previous_3months'
                        ]
                    },
                    'reason': '시기별 리뷰 수집'
                },
                {
                    'action': 'analyze',
                    'tool': 'sentiment_analysis',
                    'params': {
                        'group_by': 'time_period'
                    },
                    'reason': '시기별 감성 변화'
                },
                {
                    'action': 'analyze',
                    'tool': 'keyword_extraction',
                    'params': {
                        'compare_periods': True
                    },
                    'reason': '키워드 변화 탐지'
                }
            ],
            'expected_output': [
                'sentiment_trend',
                'emerging_declining_keywords',
                'change_analysis'
            ],
            'metadata': {
                'frequency': 'low',
                'complexity': 'high'
            }
        }
    ],
    
    # 패턴 매칭 우선순위
    'matching_priority': [
        'skin_type_analysis',
        'comparison_analysis',
        'trend_analysis',
        'aspect_analysis'
    ],
    
    # 기본 패턴 (매칭 실패 시)
    'default_pattern': {
        'name': 'general_analysis',
        'description': '일반 분석',
        'steps': [
            {
                'action': 'search',
                'tool': 'hierarchical_retrieval'
            },
            {
                'action': 'analyze',
                'tool': 'sentiment_analysis'
            },
            {
                'action': 'analyze',
                'tool': 'keyword_extraction'
            }
        ]
    }
}