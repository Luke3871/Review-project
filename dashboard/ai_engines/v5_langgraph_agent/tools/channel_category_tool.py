"""
ChannelCategoryTool - 채널별 카테고리 중요 반응 분석 툴

회사 요구사항 #6: "채널별 카테고리 중요 반응"

채널별로 중요하게 여기는 속성/키워드 차이 분석:
- 채널별 주요 키워드
- 채널별 속성 만족도
- 채널 간 차이점
"""

from typing import List, Dict, Optional
from collections import Counter, defaultdict

from .base_tool import BaseTool


class ChannelCategoryTool(BaseTool):
    """
    채널별 카테고리 중요 반응 분석 툴

    각 채널에서 어떤 속성/키워드가 중요하게 여겨지는지 분석
    """

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        채널별 카테고리 중요 반응 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "채널별_분석": {
                    "올리브영": {
                        "리뷰_수": 1500,
                        "주요_키워드": [...],
                        "주요_속성": [...],
                        "특징": "..."
                    },
                    ...
                },
                "채널_간_차이": {...},
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

        # 2. 채널별로 리뷰 분류
        채널별_리뷰 = defaultdict(list)

        for review in reviews:
            채널 = review.get('channel')
            if 채널:
                채널별_리뷰[채널].append(review)

        if not 채널별_리뷰:
            return {
                "count": len(reviews),
                "message": "채널 정보가 없는 리뷰입니다."
            }

        # 3. 채널별 분석
        채널별_분석 = {}

        for 채널, 리뷰들 in 채널별_리뷰.items():
            채널별_분석[채널] = self._analyze_channel(채널, 리뷰들)

        # 4. 채널 간 차이 분석
        채널_간_차이 = self._compare_channels(채널별_분석)

        # 5. 요약 생성
        summary = self._generate_summary(len(reviews), 채널별_분석, 채널_간_차이)

        return {
            "count": len(reviews),
            "채널_수": len(채널별_리뷰),
            "채널별_분석": 채널별_분석,
            "채널_간_차이": 채널_간_차이,
            "summary": summary
        }

    def _analyze_channel(self, 채널: str, 리뷰들: List[Dict]) -> Dict:
        """
        단일 채널 분석

        Args:
            채널: 채널명
            리뷰들: 해당 채널의 리뷰 리스트

        Returns:
            채널 분석 결과
        """
        # 1. 키워드 추출
        all_keywords = []
        for review in 리뷰들:
            analysis = review.get('analysis', {})
            키워드 = analysis.get('키워드', [])
            if isinstance(키워드, list):
                all_keywords.extend(키워드)

        keyword_counter = Counter(all_keywords)
        주요_키워드 = [
            {"키워드": kw, "횟수": count}
            for kw, count in keyword_counter.most_common(10)
        ]

        # 2. 속성별 만족도
        속성별_평가 = defaultdict(lambda: {"긍정": 0, "부정": 0})

        for review in 리뷰들:
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
        주요_속성 = []
        for 속성명, 평가 in 속성별_평가.items():
            총합 = 평가["긍정"] + 평가["부정"]
            if 총합 >= 5:  # 최소 5개 이상
                긍정_비율 = self._calculate_percentage(평가["긍정"], 총합)
                주요_속성.append({
                    "속성": 속성명,
                    "긍정_비율": 긍정_비율,
                    "언급_횟수": 총합
                })

        # 긍정 비율 순으로 정렬
        주요_속성.sort(key=lambda x: x["긍정_비율"], reverse=True)

        # 3. 감성 분석
        긍정_count = 0
        부정_count = 0

        for review in 리뷰들:
            analysis = review.get('analysis', {})
            감정요약 = analysis.get('감정요약', {})
            전반적평가 = 감정요약.get('전반적평가', '')

            if "긍정" in 전반적평가:
                긍정_count += 1
            elif "부정" in 전반적평가:
                부정_count += 1

        total_sentiment = 긍정_count + 부정_count
        긍정_비율 = self._calculate_percentage(긍정_count, total_sentiment) if total_sentiment > 0 else 0

        # 4. 특징 추출
        특징 = self._extract_channel_feature(주요_키워드, 주요_속성, 긍정_비율)

        return {
            "리뷰_수": len(리뷰들),
            "주요_키워드": 주요_키워드[:5],
            "주요_속성": 주요_속성[:5],
            "긍정_비율": f"{긍정_비율:.1f}%",
            "특징": 특징
        }

    def _extract_channel_feature(
        self,
        주요_키워드: List[Dict],
        주요_속성: List[Dict],
        긍정_비율: float
    ) -> str:
        """채널 특징 추출"""
        특징_parts = []

        # 키워드 특징
        if 주요_키워드:
            top_keywords = [item["키워드"] for item in 주요_키워드[:3]]
            특징_parts.append(f"주요 관심: {', '.join(top_keywords)}")

        # 속성 특징
        if 주요_속성:
            top_attr = 주요_속성[0]
            특징_parts.append(f"중요 속성: {top_attr['속성']} ({top_attr['긍정_비율']:.1f}%)")

        # 감성 특징
        if 긍정_비율 >= 70:
            특징_parts.append("전반적으로 긍정적")
        elif 긍정_비율 <= 50:
            특징_parts.append("개선 필요")

        return " | ".join(특징_parts) if 특징_parts else "데이터 부족"

    def _compare_channels(self, 채널별_분석: Dict) -> Dict:
        """
        채널 간 차이 분석

        Args:
            채널별_분석: 채널별 분석 결과

        Returns:
            채널 간 차이점
        """
        if len(채널별_분석) < 2:
            return {"message": "비교할 채널이 부족합니다."}

        # 1. 리뷰 수 비교
        리뷰_수_순위 = sorted(
            채널별_분석.items(),
            key=lambda x: x[1]["리뷰_수"],
            reverse=True
        )

        # 2. 긍정 비율 비교
        긍정_비율_순위 = sorted(
            [(채널, float(data["긍정_비율"].rstrip('%'))) for 채널, data in 채널별_분석.items()],
            key=lambda x: x[1],
            reverse=True
        )

        # 3. 고유 키워드 (각 채널에만 있는 키워드)
        채널별_키워드_set = {
            채널: set(item["키워드"] for item in data["주요_키워드"])
            for 채널, data in 채널별_분석.items()
        }

        고유_키워드 = {}
        for 채널, 키워드_set in 채널별_키워드_set.items():
            다른_채널_키워드 = set()
            for 다른_채널, 다른_키워드_set in 채널별_키워드_set.items():
                if 다른_채널 != 채널:
                    다른_채널_키워드.update(다른_키워드_set)

            고유 = 키워드_set - 다른_채널_키워드
            if 고유:
                고유_키워드[채널] = list(고유)[:3]

        return {
            "리뷰_수_순위": [
                {"채널": 채널, "리뷰_수": data["리뷰_수"]}
                for 채널, data in 리뷰_수_순위
            ],
            "긍정_비율_순위": [
                {"채널": 채널, "긍정_비율": f"{비율:.1f}%"}
                for 채널, 비율 in 긍정_비율_순위
            ],
            "채널별_고유_키워드": 고유_키워드
        }

    def _generate_summary(
        self,
        total_reviews: int,
        채널별_분석: Dict,
        채널_간_차이: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰를 {len(채널별_분석)}개 채널별로 분석\n"]

        # 채널별 특징
        summary_parts.append("\n**채널별 주요 특징:**")
        for 채널, data in 채널별_분석.items():
            summary_parts.append(f"- {채널} ({data['리뷰_수']}개): {data['특징']}")

        # 리뷰 수 순위
        if "리뷰_수_순위" in 채널_간_차이:
            summary_parts.append("\n**리뷰 수 순위:**")
            for i, item in enumerate(채널_간_차이["리뷰_수_순위"][:3], 1):
                summary_parts.append(f"{i}. {item['채널']}: {item['리뷰_수']}개")

        # 긍정 비율 순위
        if "긍정_비율_순위" in 채널_간_차이:
            summary_parts.append("\n**긍정 평가 순위:**")
            for i, item in enumerate(채널_간_차이["긍정_비율_순위"][:3], 1):
                summary_parts.append(f"{i}. {item['채널']}: {item['긍정_비율']}")

        return "\n".join(summary_parts)

    # 긍정/부정 판단 헬퍼 메서드
    POSITIVE_KEYWORDS = [
        "좋", "훌륭", "완벽", "만족", "추천", "최고",
        "촉촉", "부드럽", "산뜻", "가벼", "효과"
    ]

    NEGATIVE_KEYWORDS = [
        "나쁨", "별로", "아쉽", "부족", "실망",
        "건조", "뻑뻑", "끈적", "무거", "자극"
    ]

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
    print("=== ChannelCategoryTool 테스트 ===\n")

    tool = ChannelCategoryTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 채널별 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"분석 채널 수: {result['채널_수']}개")

    print("\n**채널별 분석:**")
    for 채널, data in result['채널별_분석'].items():
        print(f"\n{채널} ({data['리뷰_수']}개):")
        print(f"  긍정 비율: {data['긍정_비율']}")
        print(f"  특징: {data['특징']}")
        print(f"  주요 키워드: {', '.join([item['키워드'] for item in data['주요_키워드'][:3]])}")

    print(f"\n{result['summary']}")
