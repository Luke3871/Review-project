"""
V1 Rule-based Report Generator
- 통계 기반 규칙으로 인사이트 생성
- UI 버전(tab1_daiso_section.py)에서 이식
"""

from .report_generator import generate_product_report

__all__ = ['generate_product_report']
