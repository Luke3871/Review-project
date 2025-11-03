"""
ProsTool - 장점 분석 툴

회사 요구사항 지원: 제품 장점 분석

장점 데이터 분석:
- 장점 빈도 순위
- 장점 카테고리 분류
- 대표 장점 추출
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class ProsTool(BaseTool):
    """
    장점 분석 툴

    analysis->장점 필드 분석:
    - 장점 빈도 통계
    - 카테고리별 분류
    - 대표 장점 추출
    """

    # 장점 카테고리 키워드
    PROS_CATEGORIES = {
        "효과": ["효과", "개선", "좋아짐", "나아짐", "변화"],
        "사용감": ["촉촉", "부드럽", "산뜻", "가벼", "흡수", "발림"],
        "향": ["향", "냄새", "무향", "은은"],
        "가격": ["가격", "가성비", "저렴", "합리적", "혜자"],
        "디자인": ["디자인", "패키지", "용기", "예쁨"],
        "용량": ["용량", "많", "넉넉", "충분"],
        "품질": ["품질", "순하", "자극없", "안전", "믿음"],
        "브랜드": ["유명", "브랜드", "인기", "유튜버", "추천"]
    }

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        장점 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "pros_count": 장점이 있는 리뷰 수,
                "장점_순위": [...],
                "카테고리별_장점": {...},
                "대표_장점_Top5": [...],
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "pros_count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 장점 추출
        all_pros = []
        pros_reviews_count = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            장점 = analysis.get('장점', [])

            if not isinstance(장점, list):
                continue

            if 장점:
                pros_reviews_count += 1
                all_pros.extend(장점)

        # 3. 장점 빈도 통계
        pros_counter = Counter(all_pros)
        장점_순위 = [
            {"장점": 장점, "언급_횟수": 횟수}
            for 장점, 횟수 in pros_counter.most_common(20)
        ]

        # 4. 카테고리별 분류
        카테고리별_장점 = self._categorize_pros(all_pros)

        # 5. 대표 장점 Top 5
        대표_장점_Top5 = [
            {
                "장점": item["장점"],
                "언급_횟수": item["언급_횟수"],
                "비율": f"{self._calculate_percentage(item['언급_횟수'], pros_reviews_count):.1f}%"
            }
            for item in 장점_순위[:5]
        ]

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            pros_reviews_count,
            대표_장점_Top5,
            카테고리별_장점
        )

        return {
            "count": len(reviews),
            "pros_count": pros_reviews_count,
            "pros_ratio": f"{self._calculate_percentage(pros_reviews_count, len(reviews)):.1f}%",
            "장점_순위": 장점_순위,
            "카테고리별_장점": 카테고리별_장점,
            "대표_장점_Top5": 대표_장점_Top5,
            "summary": summary
        }

    def _categorize_pros(self, all_pros: List[str]) -> Dict:
        """
        장점을 카테고리별로 분류

        Args:
            all_pros: 모든 장점 리스트

        Returns:
            카테고리별 장점 dict
        """
        카테고리별_카운터 = {category: Counter() for category in self.PROS_CATEGORIES.keys()}
        카테고리별_카운터["기타"] = Counter()

        for 장점 in all_pros:
            if not 장점:
                continue

            장점_lower = 장점.lower()
            categorized = False

            # 카테고리 매칭
            for category, keywords in self.PROS_CATEGORIES.items():
                if any(kw in 장점_lower for kw in keywords):
                    카테고리별_카운터[category][장점] += 1
                    categorized = True
                    break

            if not categorized:
                카테고리별_카운터["기타"][장점] += 1

        # 카테고리별 상위 5개 장점
        result = {}
        for category, counter in 카테고리별_카운터.items():
            if counter:
                result[category] = {
                    "count": sum(counter.values()),
                    "top_pros": [
                        {"장점": pros, "횟수": count}
                        for pros, count in counter.most_common(5)
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
        pros_reviews_count: int,
        대표_장점_Top5: List[Dict],
        카테고리별_장점: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {pros_reviews_count}개에서 장점 언급\n"]

        # 대표 장점 Top 5
        if 대표_장점_Top5:
            summary_parts.append("\n**가장 많이 언급된 장점 Top 5:**")
            for i, item in enumerate(대표_장점_Top5, 1):
                summary_parts.append(
                    f"{i}. {item['장점']}: {item['언급_횟수']}회 ({item['비율']})"
                )

        # 카테고리별 주요 장점
        if 카테고리별_장점:
            summary_parts.append("\n**카테고리별 주요 장점:**")
            for category, data in list(카테고리별_장점.items())[:3]:
                top_pros = data["top_pros"]
                if top_pros:
                    summary_parts.append(
                        f"- {category}: {top_pros[0]['장점']} ({top_pros[0]['횟수']}회)"
                    )

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== ProsTool 테스트 ===\n")

    tool = ProsTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 장점 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"장점 언급: {result['pros_count']}개 ({result['pros_ratio']})")

    print("\n**대표 장점 Top 5:**")
    for i, item in enumerate(result['대표_장점_Top5'], 1):
        print(f"  {i}. {item['장점']}: {item['언급_횟수']}회 ({item['비율']})")

    print("\n**카테고리별 장점:**")
    for category, data in list(result['카테고리별_장점'].items())[:5]:
        print(f"  {category}: {data['count']}개")
        for pros_item in data['top_pros'][:3]:
            print(f"    - {pros_item['장점']} ({pros_item['횟수']}회)")

    print(f"\n{result['summary']}")
