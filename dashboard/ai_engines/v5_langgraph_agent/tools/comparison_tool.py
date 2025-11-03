"""
ProductComparisonTool - 제품 비교 분석 툴

회사 요구사항 #9: "2개 제품 비교 분석" 충족

두 제품을 다양한 관점에서 비교:
- 속성별 만족도 비교
- 감성 비교 (긍정/부정 비율)
- 키워드 비교
- 장단점 비교
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class ProductComparisonTool(BaseTool):
    """
    제품 비교 분석 툴

    두 제품의 리뷰를 비교 분석합니다.
    사용자는 2개의 제품명을 제공해야 합니다.
    """

    # 긍정/부정 키워드
    POSITIVE_KEYWORDS = [
        "좋", "훌륭", "완벽", "만족", "추천", "최고", "베스트",
        "촉촉", "부드럽", "산뜻", "가벼", "효과", "탁월",
        "흡수", "빠름", "적당", "은은", "편하", "괜찮"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망", "최악",
        "건조", "뻑뻑", "끈적", "무거", "자극", "따가"
    ]

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        제품 비교 분석 실행

        Args:
            brands: 브랜드 리스트 (2개여야 함, 같을 수도 있음)
            products: 제품명 리스트 (2개여야 함)
            channels: 채널 리스트 (선택)

        Returns:
            {
                "product_a": {...},
                "product_b": {...},
                "comparison": {...},
                "summary": "..."
            }
        """

        # 제품이 2개인지 확인
        if not products or len(products) < 2:
            return {
                "error": "제품 비교를 위해서는 2개의 제품명이 필요합니다.",
                "message": "예: ['VT 시카크림', '라로슈포제 시카플라스트']"
            }

        # 제품 A, B 분리
        product_a_name = products[0]
        product_b_name = products[1]

        # 브랜드도 2개면 분리
        brand_a = brands[0] if brands and len(brands) > 0 else None
        brand_b = brands[1] if brands and len(brands) > 1 else brands[0] if brands else None

        # 1. 제품 A 분석
        product_a_data = self._analyze_single_product(
            brand=brand_a,
            product=product_a_name,
            channels=channels
        )

        # 2. 제품 B 분석
        product_b_data = self._analyze_single_product(
            brand=brand_b,
            product=product_b_name,
            channels=channels
        )

        # 3. 비교 분석
        comparison = self._compare_products(product_a_data, product_b_data)

        # 4. 요약 생성
        summary = self._generate_comparison_summary(
            product_a_name,
            product_b_name,
            product_a_data,
            product_b_data,
            comparison
        )

        return {
            "product_a": {
                "name": product_a_name,
                "brand": brand_a,
                "data": product_a_data
            },
            "product_b": {
                "name": product_b_name,
                "brand": brand_b,
                "data": product_b_data
            },
            "comparison": comparison,
            "summary": summary
        }

    def _analyze_single_product(
        self,
        brand: Optional[str],
        product: str,
        channels: Optional[List[str]]
    ) -> Dict:
        """
        단일 제품 분석

        Args:
            brand: 브랜드명
            product: 제품명
            channels: 채널 리스트

        Returns:
            제품 분석 결과 dict
        """
        # 리뷰 가져오기
        reviews = self._fetch_reviews(
            brands=[brand] if brand else None,
            products=[product],
            channels=channels
        )

        if not reviews:
            return {
                "review_count": 0,
                "sentiment": {},
                "attributes": {},
                "keywords": [],
                "pros": [],
                "cons": []
            }

        # 1. 감성 분석
        sentiment = self._analyze_sentiment(reviews)

        # 2. 속성 분석
        attributes = self._analyze_attributes(reviews)

        # 3. 키워드 추출
        keywords = self._extract_keywords(reviews)

        # 4. 장단점
        pros = self._extract_pros(reviews)
        cons = self._extract_cons(reviews)

        return {
            "review_count": len(reviews),
            "sentiment": sentiment,
            "attributes": attributes,
            "keywords": keywords,
            "pros": pros,
            "cons": cons
        }

    def _analyze_sentiment(self, reviews: List[Dict]) -> Dict:
        """감성 분석"""
        감정_카운터 = Counter()

        for review in reviews:
            analysis = review.get('analysis', {})
            감정요약 = analysis.get('감정요약', {})
            전반적평가 = 감정요약.get('전반적평가')

            if 전반적평가:
                감정_카운터[전반적평가] += 1

        # 긍정/부정 비율
        긍정_count = 감정_카운터.get("매우 긍정적", 0) + 감정_카운터.get("긍정적", 0)
        부정_count = 감정_카운터.get("부정적", 0) + 감정_카운터.get("매우 부정적", 0)
        total = sum(감정_카운터.values())

        return {
            "긍정_비율": self._calculate_percentage(긍정_count, total) if total > 0 else 0,
            "부정_비율": self._calculate_percentage(부정_count, total) if total > 0 else 0,
            "긍정_count": 긍정_count,
            "부정_count": 부정_count,
            "분포": dict(감정_카운터)
        }

    def _analyze_attributes(self, reviews: List[Dict]) -> Dict:
        """속성별 만족도 분석 (간단 버전)"""
        from collections import defaultdict
        속성별_평가 = defaultdict(lambda: {"긍정": 0, "부정": 0})

        for review in reviews:
            analysis = review.get('analysis', {})
            제품특성 = analysis.get('제품특성', {})

            for 속성명, 속성값 in 제품특성.items():
                if not 속성값:
                    continue

                if self._is_positive(속성값):
                    속성별_평가[속성명]["긍정"] += 1
                elif self._is_negative(속성값):
                    속성별_평가[속성명]["부정"] += 1

        # 긍정 비율 계산
        result = {}
        for 속성명, 평가 in 속성별_평가.items():
            총합 = 평가["긍정"] + 평가["부정"]
            if 총합 >= 3:  # 최소 3개 이상
                긍정_비율 = self._calculate_percentage(평가["긍정"], 총합)
                result[속성명] = {
                    "긍정_비율": 긍정_비율,
                    "긍정_count": 평가["긍정"],
                    "부정_count": 평가["부정"]
                }

        return result

    def _extract_keywords(self, reviews: List[Dict]) -> List[str]:
        """키워드 추출 (상위 10개)"""
        all_keywords = []

        for review in reviews:
            analysis = review.get('analysis', {})
            키워드 = analysis.get('키워드', [])
            if isinstance(키워드, list):
                all_keywords.extend(키워드)

        keyword_counter = Counter(all_keywords)
        return [kw for kw, _ in keyword_counter.most_common(10)]

    def _extract_pros(self, reviews: List[Dict]) -> List[str]:
        """장점 추출 (상위 5개)"""
        all_pros = []

        for review in reviews:
            analysis = review.get('analysis', {})
            장점 = analysis.get('장점', [])
            if isinstance(장점, list):
                all_pros.extend(장점)

        # 빈도수 기반 상위 5개
        pros_counter = Counter(all_pros)
        return [pros for pros, _ in pros_counter.most_common(5)]

    def _extract_cons(self, reviews: List[Dict]) -> List[str]:
        """단점 추출 (상위 5개)"""
        all_cons = []

        for review in reviews:
            analysis = review.get('analysis', {})
            단점 = analysis.get('단점', [])
            if isinstance(단점, list):
                all_cons.extend(단점)

        cons_counter = Counter(all_cons)
        return [cons for cons, _ in cons_counter.most_common(5)]

    def _compare_products(self, product_a: Dict, product_b: Dict) -> Dict:
        """
        두 제품 비교

        Args:
            product_a: 제품 A 데이터
            product_b: 제품 B 데이터

        Returns:
            비교 결과 dict
        """
        comparison = {}

        # 1. 리뷰 수 비교
        comparison["리뷰_수"] = {
            "A": product_a["review_count"],
            "B": product_b["review_count"]
        }

        # 2. 감성 비교
        comparison["감성"] = {
            "A_긍정_비율": product_a["sentiment"].get("긍정_비율", 0),
            "B_긍정_비율": product_b["sentiment"].get("긍정_비율", 0),
            "차이": product_a["sentiment"].get("긍정_비율", 0) - product_b["sentiment"].get("긍정_비율", 0)
        }

        # 3. 공통 속성 비교
        common_attributes = set(product_a["attributes"].keys()) & set(product_b["attributes"].keys())
        속성_비교 = {}

        for 속성 in common_attributes:
            a_비율 = product_a["attributes"][속성]["긍정_비율"]
            b_비율 = product_b["attributes"][속성]["긍정_비율"]
            속성_비교[속성] = {
                "A": a_비율,
                "B": b_비율,
                "차이": a_비율 - b_비율,
                "우위": "A" if a_비율 > b_비율 else "B" if b_비율 > a_비율 else "동등"
            }

        comparison["속성_비교"] = 속성_비교

        # 4. 고유 키워드 (A에만 있거나 B에만 있는)
        a_keywords_set = set(product_a["keywords"])
        b_keywords_set = set(product_b["keywords"])

        comparison["고유_키워드"] = {
            "A만_있는_키워드": list(a_keywords_set - b_keywords_set),
            "B만_있는_키워드": list(b_keywords_set - a_keywords_set),
            "공통_키워드": list(a_keywords_set & b_keywords_set)
        }

        return comparison

    def _generate_comparison_summary(
        self,
        product_a_name: str,
        product_b_name: str,
        product_a_data: Dict,
        product_b_data: Dict,
        comparison: Dict
    ) -> str:
        """비교 요약 생성"""
        summary_parts = [f"**{product_a_name} vs {product_b_name} 비교**\n"]

        # 리뷰 수
        summary_parts.append(f"\n**리뷰 수:**")
        summary_parts.append(f"- {product_a_name}: {product_a_data['review_count']}개")
        summary_parts.append(f"- {product_b_name}: {product_b_data['review_count']}개")

        # 감성 비교
        a_긍정 = comparison["감성"]["A_긍정_비율"]
        b_긍정 = comparison["감성"]["B_긍정_비율"]

        summary_parts.append(f"\n**전반적 감성:**")
        summary_parts.append(f"- {product_a_name}: 긍정 {a_긍정:.1f}%")
        summary_parts.append(f"- {product_b_name}: 긍정 {b_긍정:.1f}%")

        if abs(a_긍정 - b_긍정) > 5:
            winner = product_a_name if a_긍정 > b_긍정 else product_b_name
            summary_parts.append(f"→ **{winner}**이 더 긍정적")

        # 속성 비교 (상위 3개)
        if comparison["속성_비교"]:
            summary_parts.append(f"\n**주요 속성 비교:**")
            for 속성, data in list(comparison["속성_비교"].items())[:3]:
                summary_parts.append(
                    f"- {속성}: A {data['A']:.1f}% vs B {data['B']:.1f}% (우위: {data['우위']})"
                )

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
    print("=== ProductComparisonTool 테스트 ===\n")

    tool = ProductComparisonTool()

    # 테스트: VT 시카크림 vs 라로슈포제
    print("1. VT 시카크림 vs 라로슈포제 시카플라스트 비교")
    result = tool.run(
        brands=["VT", "라로슈포제"],
        products=["시카크림", "시카플라스트"]
    )

    if "error" in result:
        print(f"에러: {result['error']}")
    else:
        print(f"\n**제품 A: {result['product_a']['name']}**")
        print(f"  리뷰 수: {result['product_a']['data']['review_count']}개")
        print(f"  긍정 비율: {result['product_a']['data']['sentiment'].get('긍정_비율', 0):.1f}%")
        print(f"  주요 키워드: {', '.join(result['product_a']['data']['keywords'][:5])}")

        print(f"\n**제품 B: {result['product_b']['name']}**")
        print(f"  리뷰 수: {result['product_b']['data']['review_count']}개")
        print(f"  긍정 비율: {result['product_b']['data']['sentiment'].get('긍정_비율', 0):.1f}%")
        print(f"  주요 키워드: {', '.join(result['product_b']['data']['keywords'][:5])}")

        print(f"\n**비교 결과:**")
        print(f"  감성 차이: {result['comparison']['감성']['차이']:.1f}%p")

        if result['comparison']['속성_비교']:
            print(f"\n  속성 비교:")
            for 속성, data in list(result['comparison']['속성_비교'].items())[:3]:
                print(f"    {속성}: A {data['A']:.1f}% vs B {data['B']:.1f}% (우위: {data['우위']})")

        print(f"\n{result['summary']}")
