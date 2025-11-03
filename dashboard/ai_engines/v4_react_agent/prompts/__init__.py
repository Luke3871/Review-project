"""
Prompts for V4 ReAct Agent

- domain_guide: 화장품 도메인 지식
- map_prompt: Map 단계 프롬프트 생성
- reduce_prompt: Reduce 단계 프롬프트 생성
"""

from .domain_guide import (
    CATEGORY_ATTRIBUTES,
    COMPLAINT_TYPES,
    PURCHASE_MOTIVES,
    CONDITIONAL_ASPECTS
)

from .map_prompt import create_map_prompt
from .reduce_prompt import create_reduce_prompt

__all__ = [
    'CATEGORY_ATTRIBUTES',
    'COMPLAINT_TYPES',
    'PURCHASE_MOTIVES',
    'CONDITIONAL_ASPECTS',
    'create_map_prompt',
    'create_reduce_prompt'
]
