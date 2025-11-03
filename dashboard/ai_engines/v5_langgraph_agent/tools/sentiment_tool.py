"""
SentimentTool - 감정 요약 분석 툴

리뷰의 전반적인 감성 분석:
- 긍정/부정/중립 분포
- 핵심 표현 추출
- 전체 감성 비율
"""

from typing import List, Dict, Optional
from collections import Counter, defaultdict

from .base_tool import BaseTool


class SentimentTool(BaseTool):
    """
    감정 요약 분석 툴

    analysis->감정요약 필드에서:
    - 전반적평가 (매우 긍정적/긍정적/중립/부정적/매우 부정적)
    - 핵심표현 빈도
    """

    # 감성 카테고리 순서 (긍정 → 부정)
    SENTIMENT_ORDER = [
        "매우 긍정적",
        "긍정적",
        "중립",
        "부정적",
        "매우 부정적"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        감정 요약 분석 실행

        Returns:
            {
                "count": 분석한 리뷰 수,
                "sentiment_distribution": {
                    "매우 긍정적": {"count": 20, "percentage": "44.4%"},
                    ...
                },
                "overall_positive_ratio": "84.4%",
                "overall_negative_ratio": "4.4%",
                "핵심표현_빈도": {
                    "표현1": 15,
                    "표현2": 12,
                    ...
                },
                "summary": "요약 텍스트"
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "sentiment_distribution": {},
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 감정요약 추출
        감정평가_리스트 = []
        핵심표현_전체 = []

        for review in reviews:
            analysis = review.get('analysis', {})
            감정요약 = analysis.get('감정요약', {})

            if not 감정요약:
                continue

            # 전반적평가 추출
            전반적평가 = 감정요약.get('전반적평가')
            if 전반적평가:
                감정평가_리스트.append(전반적평가)

            # 핵심표현 추출
            핵심표현 = 감정요약.get('핵심표현', [])
            if isinstance(핵심표현, list):
                핵심표현_전체.extend(핵심표현)

        # 3. 감정 분포 계산
        감정_카운터 = Counter(감정평가_리스트)
        sentiment_distribution = {}

        for 감정 in self.SENTIMENT_ORDER:
            count = 감정_카운터.get(감정, 0)
            percentage = self._calculate_percentage(count, len(감정평가_리스트))

            sentiment_distribution[감정] = {
                "count": count,
                "percentage": f"{percentage:.1f}%"
            }

        # 4. 전체 긍정/부정 비율 계산
        긍정_count = 감정_카운터.get("매우 긍정적", 0) + 감정_카운터.get("긍정적", 0)
        부정_count = 감정_카운터.get("부정적", 0) + 감정_카운터.get("매우 부정적", 0)
        중립_count = 감정_카운터.get("중립", 0)

        overall_positive_ratio = self._calculate_percentage(긍정_count, len(감정평가_리스트))
        overall_negative_ratio = self._calculate_percentage(부정_count, len(감정평가_리스트))
        overall_neutral_ratio = self._calculate_percentage(중립_count, len(감정평가_리스트))

        # 5. 핵심표현 빈도 (상위 20개)
        핵심표현_카운터 = Counter(핵심표현_전체)
        핵심표현_빈도 = dict(핵심표현_카운터.most_common(20))

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            overall_positive_ratio,
            overall_negative_ratio,
            overall_neutral_ratio,
            핵심표현_카운터.most_common(5)
        )

        return {
            "count": len(reviews),
            "analyzed_sentiment_count": len(감정평가_리스트),
            "sentiment_distribution": sentiment_distribution,
            "overall_positive_ratio": f"{overall_positive_ratio:.1f}%",
            "overall_negative_ratio": f"{overall_negative_ratio:.1f}%",
            "overall_neutral_ratio": f"{overall_neutral_ratio:.1f}%",
            "긍정_count": 긍정_count,
            "부정_count": 부정_count,
            "중립_count": 중립_count,
            "핵심표현_빈도": 핵심표현_빈도,
            "summary": summary
        }

    def _generate_summary(
        self,
        total_reviews: int,
        positive_ratio: float,
        negative_ratio: float,
        neutral_ratio: float,
        top_expressions: List[tuple]
    ) -> str:
        """
        감정 분석 요약 생성

        Args:
            total_reviews: 전체 리뷰 수
            positive_ratio: 긍정 비율
            negative_ratio: 부정 비율
            neutral_ratio: 중립 비율
            top_expressions: 상위 핵심표현 [(표현, 빈도), ...]

        Returns:
            요약 텍스트
        """
        summary_parts = [f"총 {total_reviews}개 리뷰 감정 분석\n"]

        # 전체 감성
        summary_parts.append(f"\n**전반적 감성:**")
        summary_parts.append(f"- 긍정: {positive_ratio:.1f}%")
        summary_parts.append(f"- 부정: {negative_ratio:.1f}%")
        summary_parts.append(f"- 중립: {neutral_ratio:.1f}%")

        # 감성 판단
        if positive_ratio >= 70:
            overall = "매우 긍정적"
        elif positive_ratio >= 50:
            overall = "대체로 긍정적"
        elif positive_ratio >= 30:
            overall = "중립적"
        else:
            overall = "부정적"

        summary_parts.append(f"\n전반적으로 **{overall}**인 평가")

        # 핵심 표현
        if top_expressions:
            summary_parts.append(f"\n**주요 핵심 표현:**")
            for 표현, 빈도 in top_expressions[:5]:
                summary_parts.append(f"- {표현} ({빈도}회)")

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== SentimentTool 테스트 ===\n")

    tool = SentimentTool()

    # 테스트 1: 빌리프 브랜드 전체
    print("1. 빌리프 브랜드 감정 분석")
    result = tool.run(brands=["빌리프"])

    print(f"분석 리뷰 수: {result['count']}개")
    print(f"감정 분석된 리뷰: {result['analyzed_sentiment_count']}개\n")

    print("**감정 분포:**")
    for 감정, stats in result['sentiment_distribution'].items():
        print(f"  {감정}: {stats['count']}개 ({stats['percentage']})")

    print(f"\n**전체 감성 비율:**")
    print(f"  긍정: {result['overall_positive_ratio']}")
    print(f"  부정: {result['overall_negative_ratio']}")
    print(f"  중립: {result['overall_neutral_ratio']}")

    if result['핵심표현_빈도']:
        print(f"\n**상위 핵심 표현:**")
        for i, (표현, 빈도) in enumerate(list(result['핵심표현_빈도'].items())[:5], 1):
            print(f"  {i}. {표현} ({빈도}회)")

    print(f"\n{result['summary']}")

    # 테스트 2: VT 시카크림
    print("\n" + "="*50)
    print("\n2. VT 시카크림 감정 분석")
    result2 = tool.run(brands=["VT"], products=["시카크림"])

    print(f"분석 리뷰 수: {result2['count']}개")
    print(f"긍정: {result2['overall_positive_ratio']}, 부정: {result2['overall_negative_ratio']}")

    if result2['핵심표현_빈도']:
        print("\n상위 핵심 표현:")
        for 표현, 빈도 in list(result2['핵심표현_빈도'].items())[:3]:
            print(f"  - {표현} ({빈도}회)")
