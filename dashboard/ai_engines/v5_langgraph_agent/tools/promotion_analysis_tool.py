"""
PromotionAnalysisTool - 기획별 반응 분석 툴

회사 요구사항 #5: "기획별 반응 분석"

기획 타입별(1+1, 세트, 한정판 등) 반응 차이:
- 기획 타입 분류
- 타입별 만족도 비교
- 단품 vs 기획 비교
"""

from typing import List, Dict, Optional
from collections import defaultdict, Counter

from .base_tool import BaseTool


class PromotionAnalysisTool(BaseTool):
    """
    기획 타입별 반응 분석 툴

    기획 종류를 분류하고 각 타입별 반응 차이 분석
    """

    # 기획 타입 키워드
    PROMOTION_TYPES = {
        "증정": ["증정", "사은품", "덤"],
        "용량추가": ["+", "ml", "추가", "더"],
        "세트": ["세트", "키트", "패키지"],
        "한정": ["한정", "에디션", "스페셜"],
        "할인": ["할인", "세일", "특가"],
        "리필": ["리필", "리필용"]
    }

    # 긍정/부정 키워드
    POSITIVE_KEYWORDS = [
        "좋", "만족", "추천", "득템", "혜자", "알차", "가성비"
    ]

    NEGATIVE_KEYWORDS = [
        "별로", "아쉽", "부족", "비싸", "속았"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        기획별 반응 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "promotion_reviews": 기획 리뷰 수,
                "regular_reviews": 단품 리뷰 수,
                "타입별_분석": {...},
                "단품_vs_기획": {...},
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 기획 여부로 분류
        기획_리뷰 = []
        단품_리뷰 = []

        for review in reviews:
            analysis = review.get('analysis', {})
            기획여부 = analysis.get('기획여부', False)

            if 기획여부:
                기획_리뷰.append(review)
            else:
                단품_리뷰.append(review)

        # 3. 기획 타입별 분류 및 분석
        타입별_분석 = self._analyze_by_promotion_type(기획_리뷰)

        # 4. 단품 vs 기획 비교
        단품_vs_기획 = self._compare_regular_vs_promotion(단품_리뷰, 기획_리뷰)

        # 5. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            len(기획_리뷰),
            len(단품_리뷰),
            타입별_분석,
            단품_vs_기획
        )

        return {
            "count": len(reviews),
            "promotion_reviews": len(기획_리뷰),
            "regular_reviews": len(단품_리뷰),
            "promotion_ratio": f"{self._calculate_percentage(len(기획_리뷰), len(reviews)):.1f}%",
            "타입별_분석": 타입별_분석,
            "단품_vs_기획": 단품_vs_기획,
            "summary": summary
        }

    def _analyze_by_promotion_type(self, 기획_리뷰: List[Dict]) -> Dict:
        """
        기획 타입별 분석

        Args:
            기획_리뷰: 기획 리뷰 리스트

        Returns:
            타입별 분석 결과
        """
        타입별_데이터 = defaultdict(list)

        # 1. 기획 타입 분류
        for review in 기획_리뷰:
            analysis = review.get('analysis', {})
            기획정보 = analysis.get('기획정보', {})
            제품명 = analysis.get('표준_제품명', '')
            원본_제품명 = analysis.get('원본_제품명', '')

            # 구성만족도, 가성비평가 가져오기
            구성만족도 = 기획정보.get('구성만족도', '')
            가성비평가 = 기획정보.get('가성비평가', '')
            특이사항 = 기획정보.get('특이사항', '')

            # 타입 판별 (제품명, 특이사항에서)
            판별_텍스트 = f"{제품명} {원본_제품명} {특이사항}".lower()

            for 타입, 키워드들 in self.PROMOTION_TYPES.items():
                if any(키워드 in 판별_텍스트 for 키워드 in 키워드들):
                    타입별_데이터[타입].append({
                        "구성만족도": 구성만족도,
                        "가성비평가": 가성비평가,
                        "특이사항": 특이사항
                    })
                    break
            else:
                # 타입 불명
                타입별_데이터["기타"].append({
                    "구성만족도": 구성만족도,
                    "가성비평가": 가성비평가,
                    "특이사항": 특이사항
                })

        # 2. 타입별 긍정/부정 비율 계산
        타입별_통계 = {}

        for 타입, 데이터_리스트 in 타입별_데이터.items():
            # 텍스트 모으기
            전체_텍스트 = []
            for 데이터 in 데이터_리스트:
                if 데이터["구성만족도"]:
                    전체_텍스트.append(데이터["구성만족도"])
                if 데이터["가성비평가"]:
                    전체_텍스트.append(데이터["가성비평가"])

            # 긍정/부정 판단
            긍정_count = sum(1 for text in 전체_텍스트 if self._is_positive(text))
            부정_count = sum(1 for text in 전체_텍스트 if self._is_negative(text))

            타입별_통계[타입] = {
                "리뷰_수": len(데이터_리스트),
                "긍정_비율": f"{self._calculate_percentage(긍정_count, len(전체_텍스트)):.1f}%" if 전체_텍스트 else "0.0%",
                "부정_비율": f"{self._calculate_percentage(부정_count, len(전체_텍스트)):.1f}%" if 전체_텍스트 else "0.0%",
                "긍정_count": 긍정_count,
                "부정_count": 부정_count
            }

        # 리뷰 수 순으로 정렬
        sorted_통계 = dict(sorted(
            타입별_통계.items(),
            key=lambda x: x[1]["리뷰_수"],
            reverse=True
        ))

        return sorted_통계

    def _compare_regular_vs_promotion(self, 단품_리뷰: List[Dict], 기획_리뷰: List[Dict]) -> Dict:
        """
        단품 vs 기획 비교

        Args:
            단품_리뷰: 단품 리뷰
            기획_리뷰: 기획 리뷰

        Returns:
            비교 결과
        """
        # 단품 감성 분석
        단품_감성 = self._analyze_sentiment(단품_리뷰)

        # 기획 감성 분석
        기획_감성 = self._analyze_sentiment(기획_리뷰)

        # 차이 계산
        긍정_차이 = 기획_감성["긍정_비율"] - 단품_감성["긍정_비율"]

        return {
            "단품": {
                "리뷰_수": len(단품_리뷰),
                "긍정_비율": f"{단품_감성['긍정_비율']:.1f}%",
                "부정_비율": f"{단품_감성['부정_비율']:.1f}%"
            },
            "기획": {
                "리뷰_수": len(기획_리뷰),
                "긍정_비율": f"{기획_감성['긍정_비율']:.1f}%",
                "부정_비율": f"{기획_감성['부정_비율']:.1f}%"
            },
            "긍정_차이": f"{긍정_차이:+.1f}%p",
            "우위": "기획" if 긍정_차이 > 5 else "단품" if 긍정_차이 < -5 else "비슷함"
        }

    def _analyze_sentiment(self, reviews: List[Dict]) -> Dict:
        """감성 분석"""
        if not reviews:
            return {"긍정_비율": 0, "부정_비율": 0}

        긍정_count = 0
        부정_count = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            감정요약 = analysis.get('감정요약', {})
            전반적평가 = 감정요약.get('전반적평가', '')

            if "긍정" in 전반적평가:
                긍정_count += 1
            elif "부정" in 전반적평가:
                부정_count += 1

        total = 긍정_count + 부정_count

        return {
            "긍정_비율": self._calculate_percentage(긍정_count, total) if total > 0 else 0,
            "부정_비율": self._calculate_percentage(부정_count, total) if total > 0 else 0
        }

    def _generate_summary(
        self,
        total: int,
        기획_count: int,
        단품_count: int,
        타입별_분석: Dict,
        단품_vs_기획: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total}개 리뷰 분석\n"]

        # 기획 vs 단품 비율
        summary_parts.append(f"**구성:**")
        summary_parts.append(f"- 기획: {기획_count}개 ({self._calculate_percentage(기획_count, total):.1f}%)")
        summary_parts.append(f"- 단품: {단품_count}개 ({self._calculate_percentage(단품_count, total):.1f}%)")

        # 단품 vs 기획 감성 비교
        summary_parts.append(f"\n**단품 vs 기획 감성:**")
        summary_parts.append(f"- 단품: 긍정 {단품_vs_기획['단품']['긍정_비율']}")
        summary_parts.append(f"- 기획: 긍정 {단품_vs_기획['기획']['긍정_비율']}")
        summary_parts.append(f"- 우위: {단품_vs_기획['우위']}")

        # 타입별 분석
        if 타입별_분석:
            summary_parts.append(f"\n**기획 타입별 분석:**")
            for 타입, stats in list(타입별_분석.items())[:3]:
                summary_parts.append(f"- {타입}: {stats['리뷰_수']}개, 긍정 {stats['긍정_비율']}")

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
    print("=== PromotionAnalysisTool 테스트 ===\n")

    tool = PromotionAnalysisTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 기획별 반응 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"기획 리뷰: {result['promotion_reviews']}개 ({result['promotion_ratio']})")
    print(f"단품 리뷰: {result['regular_reviews']}개")

    print(f"\n**단품 vs 기획:**")
    단품_vs_기획 = result['단품_vs_기획']
    print(f"  단품 긍정: {단품_vs_기획['단품']['긍정_비율']}")
    print(f"  기획 긍정: {단품_vs_기획['기획']['긍정_비율']}")
    print(f"  우위: {단품_vs_기획['우위']}")

    print(f"\n**타입별 분석:**")
    for 타입, stats in result['타입별_분석'].items():
        print(f"  {타입}: {stats['리뷰_수']}개, 긍정 {stats['긍정_비율']}")

    print(f"\n{result['summary']}")
