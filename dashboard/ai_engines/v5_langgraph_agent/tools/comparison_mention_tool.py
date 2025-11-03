"""
ComparisonMentionTool - 타제품 언급 분석 툴

회사 요구사항 #2: "타제품 언급 여부"

타제품 비교 언급 분석:
- 타제품 언급 비율
- 비교 대상 제품
- 비교 내용 (우위/열위)
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class ComparisonMentionTool(BaseTool):
    """
    타제품 언급 분석 툴

    analysis->타제품비교 필드 분석:
    - 언급 여부
    - 비교 제품명
    - 비교 내용
    """

    # 우위/열위 판단 키워드
    SUPERIORITY_KEYWORDS = [
        "더 좋", "낫", "우수", "뛰어나", "훨씬", "월등", "압도"
    ]

    INFERIORITY_KEYWORDS = [
        "못", "떨어지", "아쉽", "별로", "부족", "안 됨"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        타제품 언급 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "mention_count": 타제품 언급 리뷰 수,
                "mention_ratio": "25.3%",
                "비교_제품_순위": [...],
                "비교_내용_분석": {...},
                "우위_비율": "65.2%",
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "mention_count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 타제품비교 추출
        타제품_언급_리뷰 = []
        비교_제품_리스트 = []
        비교_내용_리스트 = []

        for review in reviews:
            analysis = review.get('analysis', {})
            타제품비교 = analysis.get('타제품비교', {})

            if not 타제품비교:
                continue

            언급여부 = 타제품비교.get('언급여부', False)

            if 언급여부:
                타제품_언급_리뷰.append(타제품비교)

                # 비교 제품
                비교_제품 = 타제품비교.get('제품')
                if 비교_제품:
                    if isinstance(비교_제품, list):
                        비교_제품_리스트.extend(비교_제품)
                    else:
                        비교_제품_리스트.append(비교_제품)

                # 비교 내용
                비교_내용 = 타제품비교.get('내용')
                if 비교_내용:
                    비교_내용_리스트.append(비교_내용)

        mention_count = len(타제품_언급_리뷰)
        mention_ratio = self._calculate_percentage(mention_count, len(reviews))

        # 3. 비교 제품 순위
        비교_제품_카운터 = Counter(비교_제품_리스트)
        비교_제품_순위 = [
            {"제품": 제품, "언급_횟수": 횟수}
            for 제품, 횟수 in 비교_제품_카운터.most_common(10)
        ]

        # 4. 비교 내용 분석 (우위/열위)
        비교_내용_분석 = self._analyze_comparison_content(비교_내용_리스트)

        # 5. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            mention_count,
            mention_ratio,
            비교_제품_순위,
            비교_내용_분석
        )

        return {
            "count": len(reviews),
            "mention_count": mention_count,
            "mention_ratio": f"{mention_ratio:.1f}%",
            "비교_제품_순위": 비교_제품_순위,
            "비교_내용_분석": 비교_내용_분석,
            "summary": summary
        }

    def _analyze_comparison_content(self, 비교_내용_리스트: List[str]) -> Dict:
        """
        비교 내용 분석 (우위/열위 판단)

        Args:
            비교_내용_리스트: 비교 내용 텍스트 리스트

        Returns:
            분석 결과 dict
        """
        if not 비교_내용_리스트:
            return {
                "count": 0,
                "우위": 0,
                "열위": 0,
                "중립": 0,
                "우위_비율": "0.0%",
                "열위_비율": "0.0%"
            }

        우위_count = 0
        열위_count = 0
        중립_count = 0

        우위_샘플 = []
        열위_샘플 = []

        for 내용 in 비교_내용_리스트:
            if not 내용:
                continue

            내용_lower = 내용.lower()

            # 우위 판단
            우위_match = any(kw in 내용_lower for kw in self.SUPERIORITY_KEYWORDS)
            열위_match = any(kw in 내용_lower for kw in self.INFERIORITY_KEYWORDS)

            if 우위_match and not 열위_match:
                우위_count += 1
                if len(우위_샘플) < 3:
                    우위_샘플.append(내용)
            elif 열위_match and not 우위_match:
                열위_count += 1
                if len(열위_샘플) < 3:
                    열위_샘플.append(내용)
            else:
                중립_count += 1

        total = len(비교_내용_리스트)

        return {
            "count": total,
            "우위": 우위_count,
            "열위": 열위_count,
            "중립": 중립_count,
            "우위_비율": f"{self._calculate_percentage(우위_count, total):.1f}%",
            "열위_비율": f"{self._calculate_percentage(열위_count, total):.1f}%",
            "중립_비율": f"{self._calculate_percentage(중립_count, total):.1f}%",
            "우위_샘플": 우위_샘플,
            "열위_샘플": 열위_샘플
        }

    def _generate_summary(
        self,
        total_reviews: int,
        mention_count: int,
        mention_ratio: float,
        비교_제품_순위: List[Dict],
        비교_내용_분석: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {mention_count}개({mention_ratio:.1f}%)에서 타제품 언급\n"]

        # 비교 제품 순위
        if 비교_제품_순위:
            summary_parts.append("\n**자주 비교되는 제품 Top 5:**")
            for i, item in enumerate(비교_제품_순위[:5], 1):
                summary_parts.append(f"{i}. {item['제품']} ({item['언급_횟수']}회)")

        # 비교 내용 분석
        if 비교_내용_분석["count"] > 0:
            summary_parts.append(f"\n**비교 결과:**")
            summary_parts.append(f"- 우위: {비교_내용_분석['우위_비율']} ({비교_내용_분석['우위']}개)")
            summary_parts.append(f"- 열위: {비교_내용_분석['열위_비율']} ({비교_내용_분석['열위']}개)")
            summary_parts.append(f"- 중립: {비교_내용_분석['중립_비율']} ({비교_내용_분석['중립']}개)")

            # 우위/열위 판단
            우위 = 비교_내용_분석['우위']
            열위 = 비교_내용_분석['열위']

            if 우위 > 열위 * 2:
                summary_parts.append("\n→ 타제품 대비 **우위**를 보임")
            elif 열위 > 우위 * 2:
                summary_parts.append("\n→ 타제품 대비 **열위**로 평가됨")
            else:
                summary_parts.append("\n→ 타제품과 **비슷한 수준**")

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== ComparisonMentionTool 테스트 ===\n")

    tool = ComparisonMentionTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 타제품 언급 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"타제품 언급: {result['mention_count']}개 ({result['mention_ratio']})")

    if result['비교_제품_순위']:
        print(f"\n**자주 비교되는 제품:**")
        for i, item in enumerate(result['비교_제품_순위'][:5], 1):
            print(f"  {i}. {item['제품']} ({item['언급_횟수']}회)")

    print(f"\n**비교 내용 분석:**")
    분석 = result['비교_내용_분석']
    print(f"  우위: {분석['우위_비율']} ({분석['우위']}개)")
    print(f"  열위: {분석['열위_비율']} ({분석['열위']}개)")
    print(f"  중립: {분석['중립_비율']} ({분석['중립']}개)")

    print(f"\n{result['summary']}")
