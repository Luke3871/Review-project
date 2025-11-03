"""
AttributeTool - 속성별 만족도 분석 툴

회사 요구사항 #3: "속성별 만족도" 충족

제품 특성(보습력, 발림성, 향 등)별로:
- 언급 빈도
- 긍정/부정 비율
- 주요 표현 추출
"""

from typing import List, Dict, Optional
from collections import defaultdict
import re

from .base_tool import BaseTool


class AttributeTool(BaseTool):
    """
    속성별 만족도 분석 툴

    analysis->제품특성 필드에서 각 속성을 추출하고
    긍정/부정 비율을 계산합니다.
    """

    # 긍정/부정 키워드 사전
    POSITIVE_KEYWORDS = [
        "좋", "훌륭", "완벽", "만족", "추천", "최고", "베스트",
        "촉촉", "부드럽", "산뜻", "가벼", "효과", "탁월",
        "흡수", "빠름", "적당", "은은", "편하", "괜찮",
        "자연스럽", "선명", "예쁘", "맘에", "정말", "너무",
        "잘", "딱", "충분", "풍부", "적절"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망", "최악",
        "건조", "뻑뻑", "끈적", "무거", "자극", "따가",
        "안", "못", "없", "지워지", "번지", "묻", "날림",
        "심하", "과하", "약하", "어렵", "불편", "안됨"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        속성별 만족도 분석 실행

        Returns:
            {
                "count": 분석한 리뷰 수,
                "attributes": {
                    "보습력": {
                        "언급_횟수": 40,
                        "언급_비율": "88.9%",
                        "긍정_비율": "87.5%",
                        "부정_비율": "12.5%",
                        "주요_긍정_표현": [...],
                        "주요_부정_표현": [...]
                    },
                    ...
                }
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "attributes": {},
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 각 리뷰에서 제품특성 추출
        # {속성명: [값1, 값2, ...]}
        attributes_data = defaultdict(list)

        for review in reviews:
            analysis = review.get('analysis', {})
            제품특성 = analysis.get('제품특성', {})

            if not 제품특성:
                continue

            for 속성명, 속성값 in 제품특성.items():
                # null이거나 빈 문자열이면 스킵
                if 속성값 is None or 속성값 == "":
                    continue

                attributes_data[속성명].append(속성값)

        # 3. 속성별 통계 계산
        result = {}

        for 속성명, 값들 in attributes_data.items():
            # 긍정/부정 분류
            긍정_표현 = []
            부정_표현 = []

            for 값 in 값들:
                if self._is_positive(값):
                    긍정_표현.append(값)
                elif self._is_negative(값):
                    부정_표현.append(값)
                # else: 중립 (카운트만 하고 표현은 저장 안 함)

            언급_횟수 = len(값들)
            긍정_count = len(긍정_표현)
            부정_count = len(부정_표현)

            result[속성명] = {
                "언급_횟수": 언급_횟수,
                "언급_비율": f"{self._calculate_percentage(언급_횟수, len(reviews)):.1f}%",
                "긍정_비율": f"{self._calculate_percentage(긍정_count, 언급_횟수):.1f}%" if 언급_횟수 > 0 else "0.0%",
                "부정_비율": f"{self._calculate_percentage(부정_count, 언급_횟수):.1f}%" if 언급_횟수 > 0 else "0.0%",
                "긍정_개수": 긍정_count,
                "부정_개수": 부정_count,
                "주요_긍정_표현": 긍정_표현[:5],  # 샘플 5개
                "주요_부정_표현": 부정_표현[:5]   # 샘플 5개
            }

        # 4. 언급 횟수 순으로 정렬
        sorted_result = dict(sorted(
            result.items(),
            key=lambda x: x[1]['언급_횟수'],
            reverse=True
        ))

        return {
            "count": len(reviews),
            "attributes": sorted_result,
            "summary": self._generate_summary(sorted_result, len(reviews))
        }

    def _is_positive(self, text: str) -> bool:
        """
        텍스트가 긍정적인지 판단

        Args:
            text: 분석할 텍스트

        Returns:
            긍정이면 True
        """
        if not text:
            return False

        text_lower = text.lower()

        # 긍정 키워드 포함 여부
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)

        # 긍정 키워드가 더 많으면 긍정
        return positive_count > negative_count

    def _is_negative(self, text: str) -> bool:
        """
        텍스트가 부정적인지 판단

        Args:
            text: 분석할 텍스트

        Returns:
            부정이면 True
        """
        if not text:
            return False

        text_lower = text.lower()

        # 부정 키워드 포함 여부
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)

        # 부정 키워드가 더 많으면 부정
        return negative_count > positive_count

    def _generate_summary(self, attributes: Dict, total_reviews: int) -> str:
        """
        속성 분석 요약 생성

        Args:
            attributes: 속성별 통계
            total_reviews: 전체 리뷰 수

        Returns:
            요약 텍스트
        """
        if not attributes:
            return "분석된 속성이 없습니다."

        # 가장 많이 언급된 속성 3개
        top3 = list(attributes.items())[:3]

        summary_parts = [f"총 {total_reviews}개 리뷰 분석\n"]

        summary_parts.append("\n**주요 속성 분석:**")
        for 속성명, stats in top3:
            긍정_비율 = stats['긍정_비율']
            언급_횟수 = stats['언급_횟수']
            summary_parts.append(
                f"- {속성명}: {언급_횟수}회 언급, 긍정 {긍정_비율}"
            )

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== AttributeTool 테스트 ===\n")

    tool = AttributeTool()

    # 테스트 1: 빌리프 브랜드 전체
    print("1. 빌리프 브랜드 속성 분석")
    result = tool.run(brands=["빌리프"])

    print(f"분석 리뷰 수: {result['count']}개")
    print(f"\n발견된 속성 수: {len(result['attributes'])}개")

    if result['attributes']:
        print("\n속성별 통계:")
        for 속성명, stats in list(result['attributes'].items())[:5]:  # 상위 5개만
            print(f"\n[{속성명}]")
            print(f"  언급: {stats['언급_횟수']}회 ({stats['언급_비율']})")
            print(f"  긍정: {stats['긍정_비율']} ({stats['긍정_개수']}개)")
            print(f"  부정: {stats['부정_비율']} ({stats['부정_개수']}개)")

            if stats['주요_긍정_표현']:
                print(f"  긍정 표현: {stats['주요_긍정_표현'][0]}")
            if stats['주요_부정_표현']:
                print(f"  부정 표현: {stats['주요_부정_표현'][0]}")

    print(f"\n{result['summary']}")

    # 테스트 2: 특정 제품
    print("\n" + "="*50)
    print("\n2. VT 시카크림 속성 분석")
    result2 = tool.run(brands=["VT"], products=["시카크림"])

    print(f"분석 리뷰 수: {result2['count']}개")
    if result2['attributes']:
        print("\n주요 속성:")
        for 속성명 in list(result2['attributes'].keys())[:3]:
            stats = result2['attributes'][속성명]
            print(f"- {속성명}: 긍정 {stats['긍정_비율']}")
