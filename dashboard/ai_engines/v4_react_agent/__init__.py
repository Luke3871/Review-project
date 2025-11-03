"""
V4 ReAct Agent
계층적 검색 + Map-Reduce 기반 고품질 인사이트 보고서 생성

Main Components:
- Orchestrator: ReAct 패턴 조율
- QueryHandler: LLM 기반 쿼리 파싱
- HierarchicalRetrieval: 3단계 검색 + Map-Reduce 요약
- Tools: Vector/BM25/Hybrid 검색

last_updated: 2025.10.26
"""

from .orchestrator import Orchestrator

__all__ = ['Orchestrator']
