"""
ComplaintTool - 불만사항 분석 툴

회사 요구사항 지원: 제품 불만사항 분석

불만사항 데이터 분석:
- 불만사항 빈도 순위
- 불만사항 유형 분류
- 심각도 분석
"""

from typing import List, Dict, Optional
from collections import Counter

from .base_tool import BaseTool


class ComplaintTool(BaseTool):
    """
    불만사항 분석 툴

    analysis->불만사항 필드 분석:
    - 불만사항 빈도 통계
    - 유형별 분류
    - 주요 불만사항 추출
    """

    # 불만사항 유형 키워드
    COMPLAINT_TYPES = {
        "품질_문제": ["불량", "변질", "이상", "오염", "곰팡이", "변색", "분리"],
        "배송_문제": ["배송", "파손", "누수", "포장", "택배", "지연"],
        "가격_불만": ["가격", "비싸", "비쌈", "부담", "거품", "바가지"],
        "효과_불만": ["효과없", "변화없", "소용없", "개선안됨", "실망"],
        "사용감_불만": ["자극", "따가", "건조", "끈적", "뻑뻑", "무거"],
        "용량_불만": ["용량", "적", "부족", "금방", "아까"],
        "향_불만": ["향", "냄새", "역함", "독함", "쩔"],
        "서비스_불만": ["고객센터", "응대", "환불", "교환", "반품", "불친절"]
    }

    def _execute(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> Dict:
        """
        불만사항 분석 실행

        Returns:
            {
                "count": 전체 리뷰 수,
                "complaint_count": 불만사항이 있는 리뷰 수,
                "불만사항_순위": [...],
                "유형별_불만사항": {...},
                "주요_불만사항_Top5": [...],
                "summary": "..."
            }
        """

        # 1. 리뷰 가져오기
        reviews = self._fetch_reviews(brands, products, channels)

        if not reviews:
            return {
                "count": 0,
                "complaint_count": 0,
                "message": "분석할 리뷰가 없습니다."
            }

        # 2. 불만사항 추출
        all_complaints = []
        complaint_reviews_count = 0

        for review in reviews:
            analysis = review.get('analysis', {})
            불만사항 = analysis.get('불만사항', [])

            if not isinstance(불만사항, list):
                continue

            if 불만사항:
                complaint_reviews_count += 1
                all_complaints.extend(불만사항)

        # 3. 불만사항 빈도 통계
        complaint_counter = Counter(all_complaints)
        불만사항_순위 = [
            {"불만사항": 불만, "언급_횟수": 횟수}
            for 불만, 횟수 in complaint_counter.most_common(20)
        ]

        # 4. 유형별 분류
        유형별_불만사항 = self._categorize_complaints(all_complaints)

        # 5. 주요 불만사항 Top 5
        주요_불만사항_Top5 = [
            {
                "불만사항": item["불만사항"],
                "언급_횟수": item["언급_횟수"],
                "비율": f"{self._calculate_percentage(item['언급_횟수'], complaint_reviews_count):.1f}%"
            }
            for item in 불만사항_순위[:5]
        ]

        # 6. 요약 생성
        summary = self._generate_summary(
            len(reviews),
            complaint_reviews_count,
            주요_불만사항_Top5,
            유형별_불만사항
        )

        return {
            "count": len(reviews),
            "complaint_count": complaint_reviews_count,
            "complaint_ratio": f"{self._calculate_percentage(complaint_reviews_count, len(reviews)):.1f}%",
            "불만사항_순위": 불만사항_순위,
            "유형별_불만사항": 유형별_불만사항,
            "주요_불만사항_Top5": 주요_불만사항_Top5,
            "summary": summary
        }

    def _categorize_complaints(self, all_complaints: List[str]) -> Dict:
        """
        불만사항을 유형별로 분류

        Args:
            all_complaints: 모든 불만사항 리스트

        Returns:
            유형별 불만사항 dict
        """
        유형별_카운터 = {complaint_type: Counter() for complaint_type in self.COMPLAINT_TYPES.keys()}
        유형별_카운터["기타"] = Counter()

        for 불만 in all_complaints:
            if not 불만:
                continue

            불만_lower = 불만.lower()
            categorized = False

            # 유형 매칭
            for complaint_type, keywords in self.COMPLAINT_TYPES.items():
                if any(kw in 불만_lower for kw in keywords):
                    유형별_카운터[complaint_type][불만] += 1
                    categorized = True
                    break

            if not categorized:
                유형별_카운터["기타"][불만] += 1

        # 유형별 상위 5개 불만사항
        result = {}
        for complaint_type, counter in 유형별_카운터.items():
            if counter:
                result[complaint_type] = {
                    "count": sum(counter.values()),
                    "top_complaints": [
                        {"불만사항": complaint, "횟수": count}
                        for complaint, count in counter.most_common(5)
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
        complaint_reviews_count: int,
        주요_불만사항_Top5: List[Dict],
        유형별_불만사항: Dict
    ) -> str:
        """요약 생성"""
        summary_parts = [f"총 {total_reviews}개 리뷰 중 {complaint_reviews_count}개에서 불만사항 언급\n"]

        complaint_ratio = self._calculate_percentage(complaint_reviews_count, total_reviews)

        # 불만 비율 해석
        if complaint_ratio < 10:
            summary_parts.append(f"→ 불만 비율 {complaint_ratio:.1f}%로 **매우 낮음** (양호)")
        elif complaint_ratio < 20:
            summary_parts.append(f"→ 불만 비율 {complaint_ratio:.1f}%로 **낮음** (양호)")
        elif complaint_ratio < 30:
            summary_parts.append(f"→ 불만 비율 {complaint_ratio:.1f}%로 **보통**")
        else:
            summary_parts.append(f"→ 불만 비율 {complaint_ratio:.1f}%로 **높음** (개선 필요)")

        # 주요 불만사항 Top 5
        if 주요_불만사항_Top5:
            summary_parts.append("\n**가장 많이 언급된 불만사항 Top 5:**")
            for i, item in enumerate(주요_불만사항_Top5, 1):
                summary_parts.append(
                    f"{i}. {item['불만사항']}: {item['언급_횟수']}회 ({item['비율']})"
                )

        # 유형별 주요 불만사항
        if 유형별_불만사항:
            summary_parts.append("\n**유형별 주요 불만사항:**")
            for complaint_type, data in list(유형별_불만사항.items())[:3]:
                top_complaints = data["top_complaints"]
                if top_complaints:
                    summary_parts.append(
                        f"- {complaint_type}: {top_complaints[0]['불만사항']} ({top_complaints[0]['횟수']}회)"
                    )

        return "\n".join(summary_parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== ComplaintTool 테스트 ===\n")

    tool = ComplaintTool()

    # 테스트: 빌리프 브랜드
    print("1. 빌리프 브랜드 불만사항 분석")
    result = tool.run(brands=["빌리프"])

    print(f"전체 리뷰: {result['count']}개")
    print(f"불만사항 언급: {result['complaint_count']}개 ({result['complaint_ratio']})")

    print("\n**주요 불만사항 Top 5:**")
    for i, item in enumerate(result['주요_불만사항_Top5'], 1):
        print(f"  {i}. {item['불만사항']}: {item['언급_횟수']}회 ({item['비율']})")

    print("\n**유형별 불만사항:**")
    for complaint_type, data in list(result['유형별_불만사항'].items())[:5]:
        print(f"  {complaint_type}: {data['count']}개")
        for complaint_item in data['top_complaints'][:3]:
            print(f"    - {complaint_item['불만사항']} ({complaint_item['횟수']}회)")

    print(f"\n{result['summary']}")
