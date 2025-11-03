"""
PurchaseMotivationTool - 구매동기 분석 툴

회사 요구사항 지원: 구매동기 분석

구매동기 데이터 분석:
- 구매동기 빈도 순위
- 구매동기 유형 분류
- 채널별 구매동기 차이
"""

from typing import List, Dict, Optional
from collections import Counter, defaultdict

from .base_tool import BaseTool


class PurchaseMotivationTool(BaseTool):
    """
    구매동기 분석 툴

    analysis->구매동기 필드 분석:
    - 구매동기 빈도 통계
    - 유형별 분류
    - 주요 구매동기 추출
    """

    # 구매동기 유형 키워드
    MOTIVATION_TYPES = {
        "재구매": ["재구매", "리필", "또", "다시", "계속"],
        "추천": ["추천", "입소문", "지인", "친구", "가족"],
        "광고_마케팅": ["광고", "유튜버", "인플루언서", "SNS", "인스타"],
        "리뷰": ["리뷰", "후기", "평가", "별점"],
        "브랜드": ["브랜드", "유명", "믿음", "신뢰"],
        "가격": ["가격", "저렴", "할인", "세일", "특가", "이벤트"],
        "기획": ["기획", "증정", "덤", "사은품", "세트"],
        "성분": ["성분", "순하", "무첨가", "천연", "유기농"],
        "효과": ["효과", "개선", "치료", "문제", "고민"],
        "호기심": ["궁금", "호기심", "새로", "신제품", "출시"]
    }

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        구매동기 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "motivation_count": 구매동기가 있는 리뷰 수,
                "구매동기_순위": [...],
                "유형별_구매동기": {...},
                "주요_구매동기_Top5": [...],
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "motivation_count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 구매동기 추출
        all_motivations = []
        motivation_reviews_count = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            구매동기 = analysis.get('구매동기', [])

            if not isinstance(구매동기, list):
                continue

            if 구매동기:
                motivation_reviews_count += 1
                all_motivations.extend(구매동기)

        # 3. 구매동기 빈도 통계
        motivation_counter = Counter(all_motivations)
        구매동기_순위 = [
            {"구매동기": 동기, "언급_횟수": 횟수}
            for 동기, 횟수 in motivation_counter.most_common(20)
        ]

        # 4. 유형별 분류
        유형별_구매동기 = self._categorize_motivations(all_motivations)

        # 5. 주요 구매동기 Top 5
        주요_구매동기_Top5 = [
            {
                "구매동기": item["구매동기"],
                "언급_횟수": item["언급_횟수"],
                "비율": f"{self._calculate_percentage(item['언급_횟수'], motivation_reviews_count):.1f}%"
            }
            for item in 구매동기_순위[:5]
        ]

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            motivation_reviews_count,
            주요_구매동기_Top5,
            유형별_구매동기
        )

        return {
            "count": len(reviews),
            "motivation_count": motivation_reviews_count,
            "motivation_ratio": f"{self._calculate_percentage(motivation_reviews_count, len(reviews)):.1f}%",
            "구매동기_순위": 구매동기_순위,
            "유형별_구매동기": 유형별_구매동기,
            "주요_구매동기_Top5": 주요_구매동기_Top5,
            "summary": summary
        }

    def _categorize_motivations(self, all_motivations: List[str]) -> Dict:
        """
        구매동기를 유형별로 분류

        Args:
            all_motivations: 모든 구매동기 리스트

        Returns:
            유형별 구매동기 dict
        """
        유형별_카운터 = {motivation_type: Counter() for motivation_type in self.MOTIVATION_TYPES.keys()}
        유형별_카운터["기타"] = Counter()

        for 동기 in all_motivations:
            if not 동기:
                continue

            동기_lower = 동기.lower()
            categorized = False

            # 유형 매칭
            for motivation_type, keywords in self.MOTIVATION_TYPES.items():
                if any(kw in 동기_lower for kw in keywords):
                    유형별_카운터[motivation_type][동기] += 1
                    categorized = True
                    break

            if not categorized:
                유형별_카운터["기타"][동기] += 1

        # 유형별 상위 5개 구매동기
        result = {}
        for motivation_type, counter in 유형별_카운터.items():
            if counter:
                result[motivation_type] = {
                    "count": sum(counter.values()),
                    "top_motivations": [
                        {"구매동기": motivation, "횟수": count}
                        for motivation, count in counter.most_common(5)
                    ]
                }

        # 카운트 순으로 정렬
        sorted_result = dict(sorted(
            result.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        ))

        return sorted_result

    def _generate_summary(
        self,
        total_reviews: int,
        motivation_reviews_count: int,
        주요_구매동기_Top5: List[Dict],
        유형별_구매동기: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {motivation_reviews_count}개에서 구매동기 언급\n"]

        # 주요 구매동기 Top 5
        if 주요_구매동기_Top5:
            summary_parts.append("\n**가장 많이 언급된 구매동기 Top 5:**")
            for i, item in enumerate(주요_구매동기_Top5, 1):
                summary_parts.append(
                    f"{i}. {item['구매동기']}: {item['언급_횟수']}회 ({item['비율']})"
                )

        # 유형별 주요 구매동기
        if 유형별_구매동기:
            summary_parts.append("\n**유형별 주요 구매동기:**")
            for motivation_type, data in list(유형별_구매동기.items())[:5]:
                top_motivations = data["top_motivations"]
                if top_motivations:
                    summary_parts.append(
                        f"- {motivation_type}: {top_motivations[0]['구매동기']} ({top_motivations[0]['횟수']}회)"
                    )

        # 주요 유형 인사이트
        if 유형별_구매동기:
            top_type = list(유형별_구매동기.keys())[0]
            summary_parts.append(f"\n→ **{top_type}**이 가장 주요한 구매동기")

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== PurchaseMotivationTool 테스트 ===\n")

    tool = PurchaseMotivationTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 구매동기 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"구매동기 언급: {result['motivation_count']}개 ({result['motivation_ratio']})")

    print("\n**주요 구매동기 Top 5:**")
    for i, item in enumerate(result['주요_구매동기_Top5'], 1):
        print(f"  {i}. {item['구매동기']}: {item['언급_횟수']}회 ({item['비율']})")

    print("\n**유형별 구매동기:**")
    for motivation_type, data in list(result['유형별_구매동기'].items())[:5]:
        print(f"  {motivation_type}: {data['count']}개")
        for motivation_item in data['top_motivations'][:3]:
            print(f"    - {motivation_item['구매동기']} ({motivation_item['횟수']}회)")

    print(f"\n{result['summary']}")
