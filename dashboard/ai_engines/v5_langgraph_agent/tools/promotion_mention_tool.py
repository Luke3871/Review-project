"""
PromotionMentionTool - 기획/프로모션 언급 분석 툴

회사 요구사항 #1, #5: "기획 언급 여부 + 긍부정 평가", "기획별 반응 분석"

기획(1+1, 세트, 한정판 등)에 대한 언급 분석:
- 기획 언급 비율
- 구성만족도 통계
- 가성비평가 통계
- 긍정/부정 비율
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class PromotionMentionTool(BaseTool):
    """
    기획/프로모션 언급 분석 툴

    analysis->기획정보 필드 분석:
    - 언급 여부
    - 구성만족도
    - 가성비평가
    - 특이사항
    """

    # 긍정/부정 키워드
    POSITIVE_KEYWORDS = [
        "좋", "만족", "추천", "훌륭", "완벽", "최고", "가성비",
        "알차", "풍성", "득템", "혜자", "저렴", "합리적"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망", "비싸", "과대",
        "속았", "거품", "손해"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        기획 언급 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "mention_count": 기획 언급 리뷰 수,
                "mention_ratio": "45.2%",
                "구성만족도_분석": {...},
                "가성비평가_분석": {...},
                "긍정_비율": "78.5%",
                "부정_비율": "12.3%",
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

        # 2. 기획정보 추출
        기획_언급_리뷰 = []
        구성만족도_리스트 = []
        가성비평가_리스트 = []
        특이사항_리스트 = []

        for review in reviews:
            analysis = review.get('analysis', {})
            기획정보 = analysis.get('기획정보', {})

            if not 기획정보:
                continue

            언급여부 = 기획정보.get('언급여부', False)

            if 언급여부:
                기획_언급_리뷰.append(기획정보)

                # 구성만족도
                구성만족도 = 기획정보.get('구성만족도')
                if 구성만족도:
                    구성만족도_리스트.append(구성만족도)

                # 가성비평가
                가성비평가 = 기획정보.get('가성비평가')
                if 가성비평가:
                    가성비평가_리스트.append(가성비평가)

                # 특이사항
                특이사항 = 기획정보.get('특이사항')
                if 특이사항:
                    특이사항_리스트.append(특이사항)

        mention_count = len(기획_언급_리뷰)
        mention_ratio = self._calculate_percentage(mention_count, len(reviews))

        # 3. 구성만족도 분석 (긍정/부정)
        구성만족도_분석 = self._analyze_satisfaction(구성만족도_리스트, "구성만족도")

        # 4. 가성비평가 분석 (긍정/부정)
        가성비평가_분석 = self._analyze_satisfaction(가성비평가_리스트, "가성비평가")

        # 5. 전체 긍정/부정 비율
        전체_텍스트 = 구성만족도_리스트 + 가성비평가_리스트 + 특이사항_리스트
        긍정_count = sum(1 for text in 전체_텍스트 if self._is_positive(text))
        부정_count = sum(1 for text in 전체_텍스트 if self._is_negative(text))

        전체_긍정_비율 = self._calculate_percentage(긍정_count, len(전체_텍스트)) if 전체_텍스트 else 0
        전체_부정_비율 = self._calculate_percentage(부정_count, len(전체_텍스트)) if 전체_텍스트 else 0

        # 6. 특이사항 빈도 분석
        특이사항_분석 = self._analyze_특이사항(특이사항_리스트)

        # 7. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            mention_count,
            mention_ratio,
            전체_긍정_비율,
            전체_부정_비율,
            구성만족도_분석,
            가성비평가_분석
        )

        return {
            "count": len(reviews),
            "mention_count": mention_count,
            "mention_ratio": f"{mention_ratio:.1f}%",
            "구성만족도_분석": 구성만족도_분석,
            "가성비평가_분석": 가성비평가_분석,
            "특이사항_분석": 특이사항_분석,
            "전체_긍정_비율": f"{전체_긍정_비율:.1f}%",
            "전체_부정_비율": f"{전체_부정_비율:.1f}%",
            "긍정_count": 긍정_count,
            "부정_count": 부정_count,
            "summary": summary
        }

    def _analyze_satisfaction(self, text_list: List[str], label: str) -> Dict:
        """
        만족도/평가 텍스트 분석

        Args:
            text_list: 텍스트 리스트
            label: 레이블 (구성만족도, 가성비평가 등)

        Returns:
            분석 결과 dict
        """
        if not text_list:
            return {
                "count": 0,
                "긍정_count": 0,
                "부정_count": 0,
                "긍정_비율": "0.0%",
                "부정_비율": "0.0%",
                "샘플": []
            }

        긍정_텍스트 = []
        부정_텍스트 = []

        for text in text_list:
            if self._is_positive(text):
                긍정_텍스트.append(text)
            elif self._is_negative(text):
                부정_텍스트.append(text)

        긍정_count = len(긍정_텍스트)
        부정_count = len(부정_텍스트)

        return {
            "count": len(text_list),
            "긍정_count": 긍정_count,
            "부정_count": 부정_count,
            "긍정_비율": f"{self._calculate_percentage(긍정_count, len(text_list)):.1f}%",
            "부정_비율": f"{self._calculate_percentage(부정_count, len(text_list)):.1f}%",
            "긍정_샘플": 긍정_텍스트[:3],
            "부정_샘플": 부정_텍스트[:3]
        }

    def _analyze_특이사항(self, 특이사항_리스트: List[str]) -> Dict:
        """특이사항 빈도 분석"""
        if not 특이사항_리스트:
            return {"count": 0, "주요_특이사항": []}

        # 키워드 추출 (간단 버전)
        키워드_후보 = ["증정", "사은품", "한정", "리필", "세트", "패키지", "디자인", "용량"]
        키워드_카운터 = Counter()

        for 특이사항 in 특이사항_리스트:
            for 키워드 in 키워드_후보:
                if 키워드 in 특이사항:
                    키워드_카운터[키워드] += 1

        return {
            "count": len(특이사항_리스트),
            "주요_특이사항": [kw for kw, _ in 키워드_카운터.most_common(5)],
            "샘플": 특이사항_리스트[:5]
        }

    def _generate_summary(
        self,
        total_reviews: int,
        mention_count: int,
        mention_ratio: float,
        긍정_비율: float,
        부정_비율: float,
        구성만족도_분석: Dict,
        가성비평가_분석: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {mention_count}개({mention_ratio:.1f}%)에서 기획 언급\n"]

        # 전체 감성
        summary_parts.append(f"\n**기획 관련 전체 감성:**")
        summary_parts.append(f"- 긍정: {긍정_비율:.1f}%")
        summary_parts.append(f"- 부정: {부정_비율:.1f}%")

        # 구성만족도
        if 구성만족도_분석["count"] > 0:
            summary_parts.append(f"\n**구성만족도:**")
            summary_parts.append(f"- 긍정: {구성만족도_분석['긍정_비율']} ({구성만족도_분석['긍정_count']}개)")
            summary_parts.append(f"- 부정: {구성만족도_분석['부정_비율']} ({구성만족도_분석['부정_count']}개)")

        # 가성비평가
        if 가성비평가_분석["count"] > 0:
            summary_parts.append(f"\n**가성비평가:**")
            summary_parts.append(f"- 긍정: {가성비평가_분석['긍정_비율']} ({가성비평가_분석['긍정_count']}개)")
            summary_parts.append(f"- 부정: {가성비평가_분석['부정_비율']} ({가성비평가_분석['부정_count']}개)")

        return "\n".join(summary_parts)

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


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== PromotionMentionTool 테스트 ===\n")

    tool = PromotionMentionTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 기획 언급 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"기획 언급: {result['mention_count']}개 ({result['mention_ratio']})")
    print(f"\n전체 긍정 비율: {result['전체_긍정_비율']}")
    print(f"전체 부정 비율: {result['전체_부정_비율']}")

    print(f"\n**구성만족도:**")
    구성 = result['구성만족도_분석']
    print(f"  긍정: {구성['긍정_비율']} ({구성['긍정_count']}개)")
    print(f"  부정: {구성['부정_비율']} ({구성['부정_count']}개)")

    print(f"\n**가성비평가:**")
    가성비 = result['가성비평가_분석']
    print(f"  긍정: {가성비['긍정_비율']} ({가성비['긍정_count']}개)")
    print(f"  부정: {가성비['부정_비율']} ({가성비['부정_count']}개)")

    print(f"\n{result['summary']}")
