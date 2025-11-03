"""
BaseTool - 모든 Tool의 추상 기본 클래스

모든 V5 Tool은 이 클래스를 상속받아 구현합니다.
DB 연결, 필터 조건 생성 등 공통 기능을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from ..utils.db_connector import DBConnector, build_filter_conditions


class BaseTool(ABC):
    """
    모든 Tool의 기본 클래스

    각 Tool은:
    1. 이 클래스를 상속
    2. run() 메서드만 구현
    3. DB 연결은 자동 처리
    """

    def __init__(self):
        """Tool 초기화"""
        self.name = self.__class__.__name__  # AttributeTool, SentimentTool 등
        self.db = None

    def run(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        Tool 실행 (자식 클래스에서 구현)

        Args:
            brands: 브랜드 필터 (예: ["빌리프", "VT"])
            products: 제품명 필터 (예: ["모이스춰라이징밤"])
            channels: 채널 필터 (예: ["올리브영"])

        Returns:
            {
                "count": 분석한 리뷰 수,
                "data": 분석 결과 (Tool마다 다름),
                "summary": 요약 텍스트 (선택)
            }
        """
        # DB 연결
        with DBConnector() as db:
            self.db = db
            # 실제 Tool 로직 실행 (자식 클래스가 구현)
            result = self._execute(brands, products, channels)
            self.db = None
            return result

    @abstractmethod
    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        실제 Tool 로직 (자식 클래스에서 반드시 구현)

        이 메서드 안에서:
        - self.db.fetch_reviews() 로 데이터 가져오기
        - analysis JSONB 필드 파싱
        - 통계 계산
        - 결과 반환
        """
        pass

    # ===== 헬퍼 메서드 (자식 클래스에서 사용 가능) =====

    def _fetch_reviews(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        필터 조건에 맞는 리뷰 가져오기

        Returns:
            리뷰 리스트 (각 리뷰는 dict)
        """
        return self.db.fetch_reviews(brands, products, channels)

    def _count_reviews(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> int:
        """
        필터 조건에 맞는 리뷰 개수 반환

        Returns:
            리뷰 개수
        """
        return self.db.count_reviews(brands, products, channels)

    def _extract_field_from_analysis(
        self,
        reviews: List[Dict],
        field_path: str
    ) -> List:
        """
        analysis JSONB에서 특정 필드 추출

        Args:
            reviews: 리뷰 리스트
            field_path: 필드 경로 (예: "제품특성", "감정요약.전반적평가")

        Returns:
            추출된 값 리스트

        Example:
            >>> reviews = [{"analysis": {"제품특성": {"보습력": "좋음"}}}]
            >>> self._extract_field_from_analysis(reviews, "제품특성")
            [{"보습력": "좋음"}]
        """
        results = []

        for review in reviews:
            analysis = review.get('analysis', {})

            # 필드 경로 파싱 (예: "감정요약.전반적평가" → ["감정요약", "전반적평가"])
            keys = field_path.split('.')

            # 중첩된 dict 탐색
            value = analysis
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            if value is not None:
                results.append(value)

        return results

    def _calculate_percentage(self, count: int, total: int) -> float:
        """
        퍼센트 계산 (0으로 나누기 방지)

        Returns:
            퍼센트 (0.0 ~ 100.0)
        """
        if total == 0:
            return 0.0
        return round((count / total) * 100, 1)


# ===== 사용 예시 (실제 Tool 구현 예시) =====

class ExampleTool(BaseTool):
    """
    예시 Tool (실제로는 사용 안 함)

    BaseTool을 상속받아 _execute()만 구현하면 됩니다.
    """

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """예시 Tool 로직"""

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        # 2. 필요한 필드 추출
        sentiments = self._extract_field_from_analysis(reviews, "감정요약.전반적평가")

        # 3. 통계 계산
        positive_count = sum(1 for s in sentiments if "긍정" in s)
        percentage = self._calculate_percentage(positive_count, len(sentiments))

        # 4. 결과 반환
        return {
            "count": len(reviews),
            "data": {
                "positive_percentage": percentage,
                "positive_count": positive_count,
                "total_count": len(sentiments)
            },
            "summary": f"긍정 비율: {percentage}%"
        }


if __name__ == "__main__":
    # 테스트: ExampleTool 실행
    print("=== BaseTool 테스트 ===\n")

    tool = ExampleTool()
    result = tool.run(brands=["빌리프"])

    print(f"Tool 이름: {tool.name}")
    print(f"분석 리뷰 수: {result['count']}개")
    print(f"결과: {result['data']}")
    print(f"요약: {result['summary']}")
