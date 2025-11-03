#//==============================================================================//#
"""
orchestrator.py
전체 Agent 조율

수정 사항:
- db_config 파라미터 제거 (ExecutionAgent 내부에서 처리)

last_updated : 2025.10.26
"""
#//==============================================================================//#

from typing import Dict
from .planning_agent import PlanningAgent
from .execution_agent import ExecutionAgent
from .response_agent import ResponseAgent

#//==============================================================================//#
# Orchestrator
#//==============================================================================//#

class Orchestrator:
    """
    전체 Agent 흐름 조율
    """

    def __init__(self, api_key: str):
        """
        Args:
            api_key: OpenAI API 키 (Planning + Response Agent용)
        """
        self.planning_agent = PlanningAgent(api_key)
        self.execution_agent = ExecutionAgent(api_key)  # api_key는 사용 안 하지만 호환성 유지
        self.response_agent = ResponseAgent(api_key)

    def process_query(self, user_query: str) -> Dict:
        """
        사용자 질문 처리
        """

        try:
            # 1. 계획 생성
            plan = self.planning_agent.create_plan(user_query)

            # 2. 계획 실행
            results = self.execution_agent.execute_plan(plan)

            # 3. 답변 생성
            answer = self.response_agent.generate(results, user_query)

            # 4. DB 연결 종료
            self.execution_agent.close()

            return {
                'answer': answer,
                'plan': plan,
                'results': results
            }

        except Exception as e:
            self.execution_agent.close()
            return {
                'answer': f"처리 중 오류: {e}",
                'plan': None,
                'results': None
            }
