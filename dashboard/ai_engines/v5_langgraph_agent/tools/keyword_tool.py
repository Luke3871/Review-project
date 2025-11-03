"""
KeywordTool - 키워드 추출 및 빈도 분석 툴

리뷰에서 자주 언급되는 키워드 추출:
- 키워드 빈도 순위
- 키워드별 등장 비율
- 키워드 공출현 분석 (선택)
"""

from typing import List, Dict, Optional
from collections import Counter
import itertools

from .base_tool import BaseTool


class KeywordTool(BaseTool):
    """
    키워드 추출 및 빈도 분석 툴

    analysis->키워드 필드에서:
    - 키워드 빈도 계산
    - 상위 키워드 순위
    - 키워드별 등장 비율
    """

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        키워드 분석 실행

        Returns:
            {
                "count": 분석한 리뷰 수,
                "total_keywords": 전체 키워드 수,
                "unique_keywords": 고유 키워드 수,
                "keyword_frequency": {
                    "키워드1": {
                        "count": 38,
                        "percentage": "84.4%",
                        "rank": 1
                    },
                    ...
                },
                "top_keywords": ["키워드1", "키워드2", ...],
                "summary": "요약 텍스트"
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "total_keywords": 0,
                "unique_keywords": 0,
                "keyword_frequency": {},
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 키워드 추출
        all_keywords = []
        reviews_with_keywords = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            키워드 = analysis.get('키워드', [])

            if not 키워드 or not isinstance(키워드, list):
                continue

            # 빈 문자열이나 None 제거
            valid_keywords = [k for k in 키워드 if k and isinstance(k, str)]

            if valid_keywords:
                all_keywords.extend(valid_keywords)
                reviews_with_keywords += 1

        # 3. 키워드 빈도 계산
        keyword_counter = Counter(all_keywords)
        total_keywords = len(all_keywords)
        unique_keywords = len(keyword_counter)

        # 4. 키워드별 통계 (상위 50개)
        keyword_frequency = {}

        for rank, (keyword, count) in enumerate(keyword_counter.most_common(50), 1):
            # 리뷰 기준 등장 비율 (몇 개 리뷰에 등장했는지)
            appearance_rate = self._calculate_percentage(count, reviews_with_keywords)

            keyword_frequency[keyword] = {
                "count": count,
                "percentage": f"{appearance_rate:.1f}%",
                "rank": rank
            }

        # 5. 상위 키워드 리스트 (Top 20)
        top_keywords = [kw for kw, _ in keyword_counter.most_common(20)]

        # 6. 키워드 카테고리 분류 (선택)
        keyword_categories = self._categorize_keywords(keyword_frequency)

        # 7. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            reviews_with_keywords,
            total_keywords,
            unique_keywords,
            keyword_counter.most_common(10)
        )

        return {
            "count": len(reviews),
            "reviews_with_keywords": reviews_with_keywords,
            "total_keywords": total_keywords,
            "unique_keywords": unique_keywords,
            "keyword_frequency": keyword_frequency,
            "top_keywords": top_keywords,
            "keyword_categories": keyword_categories,
            "summary": summary
        }

    def _categorize_keywords(self, keyword_frequency: Dict) -> Dict:
        """
        키워드를 카테고리별로 분류

        Args:
            keyword_frequency: 키워드 빈도 dict

        Returns:
            카테고리별 키워드 dict
        """
        # 간단한 카테고리 분류 (키워드 기반)
        categories = {
            "속성": ["보습", "발림", "흡수", "끈적", "산뜻", "가벼", "무거"],
            "효과": ["진정", "재생", "탄력", "미백", "주름", "트러블", "각질"],
            "향": ["무향", "향", "향기", "냄새"],
            "가격": ["가성비", "가격", "비싸", "저렴", "합리적"],
            "제형": ["크림", "로션", "텍스처", "제형", "묽", "질감"],
            "피부타입": ["건성", "지성", "복합성", "민감성", "피부"],
            "사용감": ["촉촉", "건조", "부드럽", "뻑뻑", "편하", "불편"]
        }

        result = {}

        for category, category_keywords in categories.items():
            matched_keywords = {}

            for keyword, stats in keyword_frequency.items():
                # 키워드에 카테고리 키워드가 포함되어 있으면
                if any(ck in keyword for ck in category_keywords):
                    matched_keywords[keyword] = stats

            if matched_keywords:
                result[category] = matched_keywords

        return result

    def _generate_summary(
        self,
        total_reviews: int,
        reviews_with_keywords: int,
        total_keywords: int,
        unique_keywords: int,
        top_keywords: List[tuple]
    ) -> str:
        """
        키워드 분석 요약 생성

        Args:
            total_reviews: 전체 리뷰 수
            reviews_with_keywords: 키워드가 있는 리뷰 수
            total_keywords: 전체 키워드 수
            unique_keywords: 고유 키워드 수
            top_keywords: 상위 키워드 [(키워드, 빈도), ...]

        Returns:
            요약 텍스트
        """
        summary_parts = [f"총 {total_reviews}개 리뷰에서 키워드 분석"]
        summary_parts.append(f"키워드가 있는 리뷰: {reviews_with_keywords}개\n")

        summary_parts.append(f"\n**키워드 통계:**")
        summary_parts.append(f"- 전체 키워드 수: {total_keywords}개")
        summary_parts.append(f"- 고유 키워드 수: {unique_keywords}개")
        summary_parts.append(f"- 리뷰당 평균: {total_keywords / reviews_with_keywords:.1f}개" if reviews_with_keywords > 0 else "- 리뷰당 평균: 0개")

        # 상위 키워드
        if top_keywords:
            summary_parts.append(f"\n**상위 10개 키워드:**")
            for i, (keyword, count) in enumerate(top_keywords[:10], 1):
                percentage = self._calculate_percentage(count, reviews_with_keywords)
                summary_parts.append(f"{i}. {keyword} ({count}회, {percentage:.1f}%)")

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== KeywordTool 테스트 ===\n")

    tool = KeywordTool()

    # 테스트 1: 빌리프 브랜드 전체
    print("1. 빌리프 브랜드 키워드 분석")
    result = tool.run(brands=["빌리프"])

    print(f"분석 리뷰 수: {result['count']}개")
    print(f"키워드가 있는 리뷰: {result['reviews_with_keywords']}개")
    print(f"전체 키워드 수: {result['total_keywords']}개")
    print(f"고유 키워드 수: {result['unique_keywords']}개\n")

    print("**상위 20개 키워드:**")
    for i, keyword in enumerate(result['top_keywords'][:20], 1):
        stats = result['keyword_frequency'][keyword]
        print(f"{i:2d}. {keyword:15s} {stats['count']:3d}회 ({stats['percentage']})")

    # 키워드 카테고리
    if result['keyword_categories']:
        print("\n**키워드 카테고리 분류:**")
        for category, keywords in result['keyword_categories'].items():
            if keywords:
                print(f"\n[{category}]")
                for kw, stats in list(keywords.items())[:5]:  # 카테고리별 상위 5개
                    print(f"  - {kw} ({stats['count']}회)")

    print(f"\n{result['summary']}")

    # 테스트 2: VT 시카크림
    print("\n" + "="*50)
    print("\n2. VT 시카크림 키워드 분석")
    result2 = tool.run(brands=["VT"], products=["시카크림"])

    print(f"분석 리뷰 수: {result2['count']}개")
    print(f"고유 키워드 수: {result2['unique_keywords']}개\n")

    print("상위 10개 키워드:")
    for i, keyword in enumerate(result2['top_keywords'][:10], 1):
        stats = result2['keyword_frequency'][keyword]
        print(f"{i}. {keyword} ({stats['count']}회)")
