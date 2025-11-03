"""
ConsTool - 단점 분석 툴

회사 요구사항 지원: 제품 단점 분석

단점 데이터 분석:
- 단점 빈도 순위
- 단점 카테고리 분류
- 주요 단점 추출
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class ConsTool(BaseTool):
    """
    단점 분석 툴

    analysis->단점 필드 분석:
    - 단점 빈도 통계
    - 카테고리별 분류
    - 주요 단점 추출
    """

    # 단점 카테고리 키워드
    CONS_CATEGORIES = {
        "효과": ["효과없", "변화없", "개선안됨", "소용없"],
        "사용감": ["건조", "뻑뻑", "끈적", "무거", "느끼", "번들"],
        "향": ["향", "냄새", "역함", "독함"],
        "가격": ["가격", "비싸", "비쌈", "부담", "거품"],
        "디자인": ["디자인", "패키지", "용기", "불편"],
        "용량": ["용량", "적", "부족", "금방"],
        "자극": ["자극", "따가", "알러지", "트러블", "예민"],
        "품질": ["품질", "변질", "이상", "불량"]
    }

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        단점 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "cons_count": 단점이 있는 리뷰 수,
                "단점_순위": [...],
                "카테고리별_단점": {...},
                "주요_단점_Top5": [...],
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "cons_count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 단점 추출
        all_cons = []
        cons_reviews_count = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            단점 = analysis.get('단점', [])

            if not isinstance(단점, list):
                continue

            if 단점:
                cons_reviews_count += 1
                all_cons.extend(단점)

        # 3. 단점 빈도 통계
        cons_counter = Counter(all_cons)
        단점_순위 = [
            {"단점": 단점, "언급_횟수": 횟수}
            for 단점, 횟수 in cons_counter.most_common(20)
        ]

        # 4. 카테고리별 분류
        카테고리별_단점 = self._categorize_cons(all_cons)

        # 5. 주요 단점 Top 5
        주요_단점_Top5 = [
            {
                "단점": item["단점"],
                "언급_횟수": item["언급_횟수"],
                "비율": f"{self._calculate_percentage(item['언급_횟수'], cons_reviews_count):.1f}%"
            }
            for item in 단점_순위[:5]
        ]

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            cons_reviews_count,
            주요_단점_Top5,
            카테고리별_단점
        )

        return {
            "count": len(reviews),
            "cons_count": cons_reviews_count,
            "cons_ratio": f"{self._calculate_percentage(cons_reviews_count, len(reviews)):.1f}%",
            "단점_순위": 단점_순위,
            "카테고리별_단점": 카테고리별_단점,
            "주요_단점_Top5": 주요_단점_Top5,
            "summary": summary
        }

    def _categorize_cons(self, all_cons: List[str]) -> Dict:
        """
        단점을 카테고리별로 분류

        Args:
            all_cons: 모든 단점 리스트

        Returns:
            카테고리별 단점 dict
        """
        카테고리별_카운터 = {category: Counter() for category in self.CONS_CATEGORIES.keys()}
        카테고리별_카운터["기타"] = Counter()

        for 단점 in all_cons:
            if not 단점:
                continue

            단점_lower = 단점.lower()
            categorized = False

            # 카테고리 매칭
            for category, keywords in self.CONS_CATEGORIES.items():
                if any(kw in 단점_lower for kw in keywords):
                    카테고리별_카운터[category][단점] += 1
                    categorized = True
                    break

            if not categorized:
                카테고리별_카운터["기타"][단점] += 1

        # 카테고리별 상위 5개 단점
        result = {}
        for category, counter in 카테고리별_카운터.items():
            if counter:
                result[category] = {
                    "count": sum(counter.values()),
                    "top_cons": [
                        {"단점": cons, "횟수": count}
                        for cons, count in counter.most_common(5)
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
        cons_reviews_count: int,
        주요_단점_Top5: List[Dict],
        카테고리별_단점: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {cons_reviews_count}개에서 단점 언급\n"]

        # 주요 단점 Top 5
        if 주요_단점_Top5:
            summary_parts.append("\n**가장 많이 언급된 단점 Top 5:**")
            for i, item in enumerate(주요_단점_Top5, 1):
                summary_parts.append(
                    f"{i}. {item['단점']}: {item['언급_횟수']}회 ({item['비율']})"
                )

        # 카테고리별 주요 단점
        if 카테고리별_단점:
            summary_parts.append("\n**카테고리별 주요 단점:**")
            for category, data in list(카테고리별_단점.items())[:3]:
                top_cons = data["top_cons"]
                if top_cons:
                    summary_parts.append(
                        f"- {category}: {top_cons[0]['단점']} ({top_cons[0]['횟수']}회)"
                    )

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== ConsTool 테스트 ===\n")

    tool = ConsTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 단점 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"단점 언급: {result['cons_count']}개 ({result['cons_ratio']})")

    print("\n**주요 단점 Top 5:**")
    for i, item in enumerate(result['주요_단점_Top5'], 1):
        print(f"  {i}. {item['단점']}: {item['언급_횟수']}회 ({item['비율']})")

    print("\n**카테고리별 단점:**")
    for category, data in list(result['카테고리별_단점'].items())[:5]:
        print(f"  {category}: {data['count']}개")
        for cons_item in data['top_cons'][:3]:
            print(f"    - {cons_item['단점']} ({cons_item['횟수']}회)")

    print(f"\n{result['summary']}")
