#//==============================================================================//#
"""
visualization_tool.py
데이터 시각화 Tool

쿼리 결과를 차트 이미지로 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

from langchain_core.tools import tool
from typing import Dict, Any, List
import sys
from pathlib import Path

# V7 core 모듈 import
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.image_generator import ImageGenerator
from state import AgentState


@tool
def generate_visualization(state: Any) -> str:
    """
    쿼리 결과를 시각화하여 차트 이미지 생성

    **사용자가 명시적으로 요청했을 때만 사용:**
    - "그래프로 보여줘"
    - "차트 그려줘"
    - "시각화해줘"
    - "비교 차트 만들어줘"

    **생성되는 차트:**

    1. 라인 차트 (시계열 데이터):
       - 월별/일별 평점 추이
       - 리뷰 수 변화 트렌드
       - 예: "최근 3개월 빌리프 평점 추이"

    2. 바 차트 (비교 데이터):
       - 브랜드 간 평점 비교
       - 제품 간 속성 비교
       - 예: "빌리프와 마몽드 평점 비교"

    **생성 조건:**

    - query_results에 데이터 있어야 함
    - data_characteristics에서 시계열/비교 데이터 확인
    - 사용자가 시각화 요청했을 때만 (user_query에 "그래프", "차트", "시각화" 포함)

    **State 읽기:**
    - user_query: 사용자 질문 (시각화 요청 확인용)
    - query_results: execute_sql 도구의 실행 결과

    **State 쓰기:**
    - generated_images: 생성된 이미지 경로 리스트

    **사용 예시:**

    질문: "빌리프 최근 3개월 평점 추이를 그래프로 보여줘"
    → generate_visualization 실행
    → 라인 차트 생성: "dashboard/generated_images/v7_charts/line_chart_20251102_143022.png"

    질문: "빌리프와 마몽드 평점 비교 차트 그려줘"
    → generate_visualization 실행
    → 바 차트 생성: "dashboard/generated_images/v7_charts/bar_chart_20251102_143045.png"

    질문: "빌리프 평점 어때?" (시각화 요청 없음)
    → generate_visualization 실행 안 함 (Agent가 선택 안 함)

    **사용 시점:**
    - execute_sql 실행 후
    - generate_output 실행 전 또는 후 (선택적)

    **주의사항:**
    - 사용자가 명시적으로 요청했을 때만 사용
    - 데이터가 없으면 이미지 생성 안 됨
    - 한글 폰트 필요 (Windows: Malgun Gothic, macOS: AppleGothic, Linux: NanumGothic)

    Args:
        state: Agent 상태 (user_query, query_results 포함)

    Returns:
        실행 완료 메시지 (generated_images는 State에 저장됨)
    """
    # State에서 데이터 읽기
    user_query = state["user_query"]
    query_results = state.get("query_results")

    if not query_results:
        return "오류: 쿼리 결과가 없습니다. execute_sql을 먼저 실행하세요."

    # 시각화 키워드 확인 (사용자가 명시적으로 요청했는지)
    viz_keywords = ["그래프", "차트", "시각화", "plot", "graph", "chart"]
    if not any(keyword in user_query for keyword in viz_keywords):
        return "사용자가 시각화를 요청하지 않았습니다."

    # ImageGenerator 인스턴스 생성
    generator = ImageGenerator()

    # 이미지 생성
    image_paths = generator.generate_images(query_results, user_query)

    if not image_paths:
        return "시각화 가능한 데이터가 없습니다."

    # State에 저장
    state["generated_images"] = image_paths

    # 완료 메시지 반환
    return f"이미지 생성 완료: {len(image_paths)}개 ({', '.join([Path(p).name for p in image_paths])})"
