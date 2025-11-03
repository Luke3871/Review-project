"""
PositioningTool - 제품 포지셔닝 분석 툴

회사 요구사항 #4: "제품 키 포지셔닝" 충족

제품의 차별점과 시장 포지션 분석:
- 강점 (긍정 평가 많은 속성)
- 약점 (부정 평가 많은 속성)
- 차별점 키워드
- 주요 키워드
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class PositioningTool(BaseTool):
    """
    제품 포지셔닝 분석 툴

    전처리 데이터의 여러 필드를 종합 분석:
    - 제품특성 → 강점/약점
    - 장점 → 차별점
    - 키워드 → 주요 특징
    """

    # 긍정/부정 키워드 (AttributeTool과 동일)
    POSITIVE_KEYWORDS = [
        "좋", "훌륭", "완벽", "만족", "추천", "최고", "베스트",
        "촉촉", "부드럽", "산뜻", "가벼", "효과", "탁월",
        "흡수", "빠름", "적당", "은은", "편하", "괜찮",
        "자연스럽", "선명", "예쁘", "맘에", "정말", "너무",
        "잘", "딱", "충분", "풍부", "적절", "뛰어나"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망", "최악",
        "건조", "뻑뻑", "끈적", "무거", "자극", "따가",
        "안", "못", "없", "지워지", "번지", "묻", "날림",
        "심하", "과하", "약하", "어렵", "불편", "비싸"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        포지셔닝 분석 실행

        Returns:
            {
                "count": 분석 리뷰 수,
                "강점": [...],
                "약점": [...],
                "차별점_키워드": [...],
                "주요_키워드": [...],
                "포지셔닝_요약": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "강점": [],
                "약점": [],
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 제품특성 분석 → 강점/약점
        강점, 약점 = self._analyze_strengths_weaknesses(reviews)

        # 3. 장점에서 차별점 키워드 추출
        차별점_키워드 = self._extract_differentiation_keywords(reviews)

        # 4. 키워드 분석 → 주요 특징
        주요_키워드 = self._extract_main_keywords(reviews)

        # 5. 포지셔닝 한 줄 요약
        포지셔닝_요약 = self._generate_positioning_summary(
            강점, 약점, 차별점_키워드
        )

        return {
            "count": len(reviews),
            "강점": 강점,
            "약점": 약점,
            "차별점_키워드": 차별점_키워드,
            "주요_키워드": 주요_키워드,
            "포지셔닝_요약": 포지셔닝_요약,
            "summary": self._generate_summary(강점, 약점, 차별점_키워드)
        }

    def _analyze_strengths_weaknesses(self, reviews: List[Dict]) -> tuple:
        """
        제품특성에서 강점/약점 추출

        Args:
            reviews: 리뷰 리스트

        Returns:
            (강점 리스트, 약점 리스트)
        """
        # 속성별로 긍정/부정 카운트
        from collections import defaultdict
        속성별_평가 = defaultdict(lambda: {"긍정": 0, "부정": 0, "중립": 0, "표현": []})

        for review in reviews:
            analysis = review.get('analysis', {})
            제품특성 = analysis.get('제품특성', {})

            for 속성명, 속성값 in 제품특성.items():
                if not 속성값 or 속성값 is None:
                    continue

                # 긍정/부정 판단
                if self._is_positive(속성값):
                    속성별_평가[속성명]["긍정"] += 1
                    속성별_평가[속성명]["표현"].append(속성값)
                elif self._is_negative(속성값):
                    속성별_평가[속성명]["부정"] += 1
                    속성별_평가[속성명]["표현"].append(속성값)
                else:
                    속성별_평가[속성명]["중립"] += 1

        # 강점: 긍정 비율 70% 이상
        강점 = []
        약점 = []

        for 속성명, 평가 in 속성별_평가.items():
            총합 = 평가["긍정"] + 평가["부정"] + 평가["중립"]
            if 총합 < 5:  # 샘플 수 너무 적으면 스킵
                continue

            긍정_비율 = self._calculate_percentage(평가["긍정"], 총합)
            부정_비율 = self._calculate_percentage(평가["부정"], 총합)

            if 긍정_비율 >= 70:
                강점.append({
                    "속성": 속성명,
                    "긍정_비율": f"{긍정_비율:.1f}%",
                    "긍정_개수": 평가["긍정"],
                    "샘플_표현": 평가["표현"][:3]
                })

            if 부정_비율 >= 25:  # 부정 25% 이상이면 약점
                약점.append({
                    "속성": 속성명,
                    "부정_비율": f"{부정_비율:.1f}%",
                    "부정_개수": 평가["부정"],
                    "샘플_표현": 평가["표현"][:3]
                })

        # 긍정 비율 순으로 정렬
        강점.sort(key=lambda x: float(x["긍정_비율"].rstrip('%')), reverse=True)
        약점.sort(key=lambda x: float(x["부정_비율"].rstrip('%')), reverse=True)

        return 강점[:5], 약점[:3]  # 상위만

    def _extract_differentiation_keywords(self, reviews: List[Dict]) -> List[str]:
        """
        장점에서 차별점 키워드 추출

        Args:
            reviews: 리뷰 리스트

        Returns:
            차별점 키워드 리스트
        """
        장점_전체 = []

        for review in reviews:
            analysis = review.get('analysis', {})
            장점 = analysis.get('장점', [])

            if isinstance(장점, list):
                장점_전체.extend(장점)

        # 자주 나오는 단어 추출 (간단 버전)
        # 실제로는 형태소 분석이 더 정확하지만, 여기서는 키워드 매칭
        차별점_후보 = [
            "무향", "저자극", "순함", "민감", "보습", "촉촉", "산뜻",
            "가벼", "흡수", "진정", "재생", "미백", "탄력", "주름",
            "가성비", "용량", "패키지", "디자인"
        ]

        차별점_카운터 = Counter()

        for 장점 in 장점_전체:
            if not 장점:
                continue
            for 키워드 in 차별점_후보:
                if 키워드 in 장점:
                    차별점_카운터[키워드] += 1

        # 상위 5개
        return [kw for kw, _ in 차별점_카운터.most_common(5)]

    def _extract_main_keywords(self, reviews: List[Dict]) -> List[str]:
        """
        주요 키워드 추출 (상위 10개)

        Args:
            reviews: 리뷰 리스트

        Returns:
            주요 키워드 리스트
        """
        all_keywords = []

        for review in reviews:
            analysis = review.get('analysis', {})
            키워드 = analysis.get('키워드', [])

            if isinstance(키워드, list):
                all_keywords.extend(키워드)

        keyword_counter = Counter(all_keywords)
        return [kw for kw, _ in keyword_counter.most_common(10)]


    def _generate_positioning_summary(
        self,
        강점: List[Dict],
        약점: List[Dict],
        차별점_키워드: List[str]
    ) -> str:
        """
        포지셔닝 한 줄 요약 생성

        Returns:
            포지셔닝 요약 문장
        """
        parts = []

        # 차별점 키워드
        if 차별점_키워드:
            parts.append(" ".join(차별점_키워드[:3]))

        # 제품 타입 (강점 속성에서 추출)
        if 강점:
            제품_타입 = 강점[0]["속성"]  # 가장 강한 속성
            parts.append(f"{제품_타입} 강점")

        return " | ".join(parts) if parts else "포지셔닝 분석 중"

    def _generate_summary(
        self,
        강점: List[Dict],
        약점: List[Dict],
        차별점_키워드: List[str]
    ) -> str:
        """
        상세 요약 생성

        Returns:
            요약 텍스트
        """
        summary_parts = ["**제품 포지셔닝 분석**\n"]

        # 강점
        if 강점:
            summary_parts.append("\n**강점:**")
            for item in 강점[:3]:
                summary_parts.append(
                    f"- {item['속성']}: 긍정 {item['긍정_비율']} ({item['긍정_개수']}개)"
                )

        # 약점
        if 약점:
            summary_parts.append("\n**약점:**")
            for item in 약점:
                summary_parts.append(
                    f"- {item['속성']}: 부정 {item['부정_비율']} ({item['부정_개수']}개)"
                )

        # 차별점
        if 차별점_키워드:
            summary_parts.append(f"\n**차별점 키워드:** {', '.join(차별점_키워드)}")

        return "\n".join(summary_parts)

    def _is_positive(self, text: str) -> bool:
        """긍정 판단"""
        if not text:
            return False
        text_lower = text.lower()
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        return positive_count > negative_count

    def _is_negative(self, text: str) -> bool:
        """부정 판단"""
        if not text:
            return False
        text_lower = text.lower()
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text_lower)
        return negative_count > positive_count


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== PositioningTool 테스트 ===\n")

    tool = PositioningTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 포지셔닝 분석")
    result = tool.run(brands=["빌리프"])

    print(f"분석 리뷰 수: {result['count']}개\n")

    print("**강점:**")
    for item in result['강점']:
        print(f"  - {item['속성']}: {item['긍정_비율']} ({item['긍정_개수']}개)")
        if item['샘플_표현']:
            print(f"    예: {item['샘플_표현'][0]}")

    print("\n**약점:**")
    for item in result['약점']:
        print(f"  - {item['속성']}: {item['부정_비율']} ({item['부정_개수']}개)")

    print(f"\n**차별점 키워드:** {', '.join(result['차별점_키워드'])}")
    print(f"**주요 키워드:** {', '.join(result['주요_키워드'][:5])}")

    print(f"\n**포지셔닝 요약:**")
    print(f"  {result['포지셔닝_요약']}")

    print(f"\n{result['summary']}")
