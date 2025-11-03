#//==============================================================================//#
"""
strategies.py
쿼리 타입별 분석 전략 (Playbook) for V4 ReAct Agent

현재는 기본 전략만 제공하며, 향후 확장 가능
"""
#//==============================================================================//#

PLAYBOOKS = {
    'general_analysis': {
        'description': '전반적인 제품 분석',
        'focus': ['모든 속성', '불만사항', '구매동기', '조건부 패턴'],
        'depth': 'comprehensive'
    },

    'aspect_analysis': {
        'description': '특정 속성 집중 분석',
        'focus': ['특정 속성', '조건부 평가'],
        'depth': 'focused'
    },

    'comparison_analysis': {
        'description': '브랜드 비교 분석',
        'focus': ['브랜드별 속성', '강점/약점 대비'],
        'depth': 'comprehensive'
    },

    'keyword_extraction': {
        'description': '떠오르는 키워드/트렌드 분석',
        'focus': ['키워드 빈도', '시계열 변화'],
        'depth': 'focused'
    }
}

def get_playbook(query_type: str) -> dict:
    """
    쿼리 타입에 맞는 Playbook 반환

    Args:
        query_type: 쿼리 타입

    Returns:
        Playbook 딕셔너리
    """
    return PLAYBOOKS.get(query_type, PLAYBOOKS['general_analysis'])
