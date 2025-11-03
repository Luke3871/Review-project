"""
KeywordSentimentTool - 키워드-감성 연계 분석 툴

회사 요구사항 #8: "키워드와 연계된 주요 감성"

키워드가 핵심표현에서 어떤 맥락으로 언급되었는지 분석:
- 키워드별 긍정/부정 표현
- 키워드가 나온 실제 문장 (핵심표현)
- 같이 나오는 키워드 (공출현)
"""

from typing import List, Dict, Optional
from collections import Counter, defaultdict

from .base_tool import BaseTool


class KeywordSentimentTool(BaseTool):
    """
    키워드-감성 연계 분석 툴

    키워드가 핵심표현에서 어떤 맥락으로 나왔는지 분석
    """

    # 긍정/부정 키워드
    POSITIVE_KEYWORDS = [
        "좋", "훌륭", "완벽", "만족", "추천", "최고",
        "촉촉", "부드럽", "산뜻", "가벼", "효과"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망",
        "건조", "뻑뻑", "끈적", "무거", "자극"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        키워드-감성 연계 분석 실행

        Returns:
            {
                "count": 리뷰 수,
                "키워드별_맥락": {
                    "보습력": {
                        "언급_횟수": 38,
                        "긍정_표현": ["보습력 좋음", ...],
                        "부정_표현": ["보습력 부족", ...],
                        "긍정_비율": "85.2%",
                        "공출현_키워드": {"촉촉": 15, ...}
                    },
                    ...
                },
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "키워드별_맥락": {},
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 키워드별 핵심표현 수집
        키워드별_표현 = defaultdict(list)
        키워드별_공출현 = defaultdict(Counter)

        for review in reviews:
            analysis = review.get('analysis', {})
            키워드들 = analysis.get('키워드', [])
            감정요약 = analysis.get('감정요약', {})
            핵심표현들 = 감정요약.get('핵심표현', [])

            if not isinstance(키워드들, list) or not isinstance(핵심표현들, list):
                continue

            # 각 키워드에 대해
            for 키워드 in 키워드들:
                if not 키워드:
                    continue

                # 이 키워드가 포함된 핵심표현 찾기
                for 표현 in 핵심표현들:
                    if 키워드 in 표현:
                        키워드별_표현[키워드].append(표현)

                # 공출현 키워드 (같은 리뷰에 함께 나온 키워드)
                for 다른_키워드 in 키워드들:
                    if 다른_키워드 != 키워드 and 다른_키워드:
                        키워드별_공출현[키워드][다른_키워드] += 1

        # 3. 키워드별 맥락 분석
        키워드별_맥락 = {}

        for 키워드, 표현_리스트 in 키워드별_표현.items():
            if len(표현_리스트) < 3:  # 최소 3개 이상
                continue

            # 긍정/부정 표현 분류
            긍정_표현 = []
            부정_표현 = []

            for 표현 in 표현_리스트:
                if self._is_positive(표현):
                    긍정_표현.append(표현)
                elif self._is_negative(표현):
                    부정_표현.append(표현)

            긍정_count = len(긍정_표현)
            부정_count = len(부정_표현)
            total = len(표현_리스트)

            # 공출현 키워드 Top 5
            공출현_top5 = dict(키워드별_공출현[키워드].most_common(5))

            키워드별_맥락[키워드] = {
                "언급_횟수": total,
                "긍정_표현": 긍정_표현[:10],  # 샘플 10개
                "부정_표현": 부정_표현[:10],  # 샘플 10개
                "긍정_count": 긍정_count,
                "부정_count": 부정_count,
                "긍정_비율": f"{self._calculate_percentage(긍정_count, total):.1f}%",
                "부정_비율": f"{self._calculate_percentage(부정_count, total):.1f}%",
                "공출현_키워드": 공출현_top5,
                "감성_점수": self._calculate_sentiment_score(긍정_count, 부정_count)
            }

        # 4. 언급 횟수 순으로 정렬
        sorted_키워드별_맥락 = dict(sorted(
            키워드별_맥락.items(),
            key=lambda x: x[1]['언급_횟수'],
            reverse=True
        ))

        # 5. 긍정/부정 키워드 Top 5
        긍정_키워드_순위 = self._get_top_positive_keywords(키워드별_맥락, 5)
        부정_키워드_순위 = self._get_top_negative_keywords(키워드별_맥락, 5)

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            len(sorted_키워드별_맥락),
            긍정_키워드_순위,
            부정_키워드_순위
        )

        return {
            "count": len(reviews),
            "분석된_키워드_수": len(sorted_키워드별_맥락),
            "키워드별_맥락": sorted_키워드별_맥락,
            "긍정_키워드_Top5": 긍정_키워드_순위,
            "부정_키워드_Top5": 부정_키워드_순위,
            "summary": summary
        }

    def _calculate_sentiment_score(
        self,
        긍정_count: int,
        부정_count: int
    ) -> float:
        """
        감성 점수 계산 (-100 ~ +100)

        Args:
            긍정_count: 긍정 개수
            부정_count: 부정 개수

        Returns:
            감성 점수
        """
        total = 긍정_count + 부정_count
        if total == 0:
            return 0.0

        긍정_비율 = 긍정_count / total
        부정_비율 = 부정_count / total

        # -100 (모두 부정) ~ +100 (모두 긍정)
        score = (긍정_비율 - 부정_비율) * 100

        return round(score, 1)

    def _is_positive(self, text: str) -> bool:
        """긍정 판단"""
        if not text:
            return False
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text.lower())
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text.lower())
        return positive_count > negative_count

    def _is_negative(self, text: str) -> bool:
        """부정 판단"""
        if not text:
            return False
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text.lower())
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text.lower())
        return negative_count > positive_count

    def _get_top_positive_keywords(
        self,
        키워드별_맥락: Dict,
        top_n: int
    ) -> List[Dict]:
        """
        가장 긍정적인 키워드 Top N

        Args:
            키워드별_맥락: 키워드별 맥락 dict
            top_n: 상위 N개

        Returns:
            Top N 키워드 리스트
        """
        # 감성 점수 순으로 정렬
        sorted_keywords = sorted(
            키워드별_맥락.items(),
            key=lambda x: x[1]['감성_점수'],
            reverse=True
        )

        return [
            {
                "키워드": 키워드,
                "긍정_비율": data['긍정_비율'],
                "감성_점수": data['감성_점수'],
                "언급_횟수": data['언급_횟수'],
                "긍정_표현_샘플": data['긍정_표현'][:3],
                "공출현_키워드": list(data['공출현_키워드'].keys())[:3]
            }
            for 키워드, data in sorted_keywords[:top_n]
        ]

    def _get_top_negative_keywords(
        self,
        키워드별_맥락: Dict,
        top_n: int
    ) -> List[Dict]:
        """
        가장 부정적인 키워드 Top N

        Args:
            키워드별_맥락: 키워드별 맥락 dict
            top_n: 상위 N개

        Returns:
            Top N 키워드 리스트
        """
        # 감성 점수 역순으로 정렬
        sorted_keywords = sorted(
            키워드별_맥락.items(),
            key=lambda x: x[1]['감성_점수']
        )

        return [
            {
                "키워드": 키워드,
                "부정_비율": data['부정_비율'],
                "감성_점수": data['감성_점수'],
                "언급_횟수": data['언급_횟수'],
                "부정_표현_샘플": data['부정_표현'][:3],
                "공출현_키워드": list(data['공출현_키워드'].keys())[:3]
            }
            for 키워드, data in sorted_keywords[:top_n]
        ]

    def _generate_summary(
        self,
        total_reviews: int,
        키워드_수: int,
        긍정_키워드: List[Dict],
        부정_키워드: List[Dict]
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰에서 {키워드_수}개 키워드 맥락 분석\n"]

        # 긍정 키워드
        if 긍정_키워드:
            summary_parts.append("\n**가장 긍정적으로 언급된 키워드 Top 5:**")
            for i, item in enumerate(긍정_키워드, 1):
                summary_parts.append(
                    f"{i}. {item['키워드']}: 긍정 {item['긍정_비율']} (점수: {item['감성_점수']:+.1f})"
                )
                if item.get('긍정_표현_샘플'):
                    summary_parts.append(f"   예: {item['긍정_표현_샘플'][0]}")

        # 부정 키워드
        if 부정_키워드:
            summary_parts.append("\n**가장 부정적으로 언급된 키워드 Top 5:**")
            for i, item in enumerate(부정_키워드, 1):
                summary_parts.append(
                    f"{i}. {item['키워드']}: 부정 {item['부정_비율']} (점수: {item['감성_점수']:+.1f})"
                )
                if item.get('부정_표현_샘플'):
                    summary_parts.append(f"   예: {item['부정_표현_샘플'][0]}")

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== KeywordSentimentTool 테스트 ===\n")

    tool = KeywordSentimentTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 키워드-감성 연계 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"분석된 키워드: {result['분석된_키워드_수']}개\n")

    print("**가장 긍정적인 키워드 Top 5:**")
    for i, item in enumerate(result['긍정_키워드_Top5'], 1):
        print(f"{i}. {item['키워드']}: 긍정 {item['긍정_비율']} (점수: {item['감성_점수']:+.1f})")

    print("\n**가장 부정적인 키워드 Top 5:**")
    for i, item in enumerate(result['부정_키워드_Top5'], 1):
        print(f"{i}. {item['키워드']}: 부정 {item['부정_비율']} (점수: {item['감성_점수']:+.1f})")

    print(f"\n{result['summary']}")
