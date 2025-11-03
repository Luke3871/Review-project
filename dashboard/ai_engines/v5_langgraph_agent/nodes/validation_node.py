"""
Validation Node - STEP 2: 데이터 검증 및 Fallback 처리

파싱된 필터 조건(브랜드/제품/채널)으로 DB에서 리뷰 개수를 확인:
- 리뷰 수 >= MIN_REVIEW_COUNT: 정상 진행
- 리뷰 수 < MIN_REVIEW_COUNT: Fallback 모드 설정

Fallback 모드:
- 데이터가 부족하여 통계적 신뢰도가 낮다는 경고
- 사용자에게 데이터 부족 안내
- 대안 제시 (필터 완화, 다른 제품 추천 등)
"""

from typing import Dict, Optional, List

from ..state import AgentState
from ..config import MIN_REVIEW_COUNT
from ..utils.db_connector import DBConnector


class ValidationNode:
    """데이터 검증 및 Fallback 처리 노드"""

    def __init__(self):
        """초기화"""
        pass

    def __call__(self, state: AgentState) -> Dict:
        """
        Validation Node 실행

        Args:
            state: 현재 Agent 상태

        Returns:
            업데이트할 상태 dict
        """
        parsed_query = state.get("parsed_query", {})
        brands = parsed_query.get("brands", [])
        products = parsed_query.get("products", [])
        channels = parsed_query.get("channels", [])

        # 노드 시작 메시지
        messages = state.get("messages", [])

        # 검색 조건 표시
        filter_parts = []
        if brands:
            filter_parts.append(f"브랜드({', '.join(brands)})")
        if products:
            filter_parts.append(f"제품({', '.join(products)})")
        if channels:
            filter_parts.append(f"채널({', '.join(channels)})")

        filter_text = " + ".join(filter_parts) if filter_parts else "전체"

        messages.append({
            "node": "Validation",
            "status": "processing",
            "content": f"데이터 검증 중... [필터: {filter_text}]"
        })

        try:
            # DB에서 리뷰 개수 확인
            review_count = self._count_reviews(brands, products, channels)

            # 데이터 0개인 경우 재질문 처리 (드롭다운 선택)
            if review_count == 0:
                # DB에서 사용 가능한 채널/브랜드/제품 리스트 가져오기
                available_channels = self._get_all_channels()
                available_brands = self._get_all_brands()
                available_products = self._get_all_products()

                # 재질문 메시지
                clarification_msg = "데이터를 찾을 수 없습니다.\n"
                clarification_msg += "채널, 브랜드, 제품을 선택해주세요."

                messages.append({
                    "node": "Validation",
                    "status": "info",
                    "content": clarification_msg
                })

                return {
                    "data_validation": {
                        "review_count": 0,
                        "min_required": MIN_REVIEW_COUNT,
                        "is_sufficient": False
                    },
                    "is_fallback": False,  # Fallback이 아닌 재질문
                    "fallback_reason": "",
                    "needs_clarification": True,
                    "suggestions": None,
                    "clarification_type": "dropdown",
                    "available_channels": available_channels,
                    "available_brands": available_brands,
                    "available_products": available_products,
                    "messages": messages
                }

            # Fallback 여부 결정
            is_fallback = review_count < MIN_REVIEW_COUNT
            fallback_reason = ""

            if is_fallback:
                fallback_reason = self._generate_fallback_reason(
                    review_count, brands, products, channels
                )

                # Fallback 경고 메시지
                messages.append({
                    "node": "Validation",
                    "status": "warning",
                    "content": fallback_reason
                })
            else:
                # 정상 메시지
                messages.append({
                    "node": "Validation",
                    "status": "success",
                    "content": f"검증 완료: {review_count}개 리뷰 발견 [필터: {filter_text}]"
                })

            return {
                "data_validation": {
                    "review_count": review_count,
                    "min_required": MIN_REVIEW_COUNT,
                    "is_sufficient": not is_fallback
                },
                "is_fallback": is_fallback,
                "fallback_reason": fallback_reason,
                "needs_clarification": False,
                "suggestions": None,
                "clarification_type": "none",
                "messages": messages
            }

        except Exception as e:
            # 에러 발생 시 Fallback 모드
            error_msg = f"데이터 검증 실패: {str(e)}"
            messages.append({
                "node": "Validation",
                "status": "error",
                "content": error_msg
            })

            return {
                "data_validation": {
                    "review_count": 0,
                    "min_required": MIN_REVIEW_COUNT,
                    "is_sufficient": False,
                    "error": str(e)
                },
                "is_fallback": True,
                "fallback_reason": error_msg,
                "messages": messages
            }

    def _count_reviews(
        self,
        brands: list,
        products: list,
        channels: list
    ) -> int:
        """
        DB에서 필터 조건에 맞는 리뷰 개수 확인

        Args:
            brands: 브랜드 리스트
            products: 제품 리스트
            channels: 채널 리스트

        Returns:
            리뷰 개수
        """
        with DBConnector() as db:
            count = db.count_reviews(
                brands=brands if brands else None,
                products=products if products else None,
                channels=channels if channels else None
            )
        return count

    def _find_similar_products(
        self,
        brands: list,
        channels: list
    ) -> List[Dict]:
        """
        브랜드로만 검색하여 유사 제품 찾기

        Args:
            brands: 브랜드 리스트
            channels: 채널 리스트

        Returns:
            유사 제품 리스트 (상위 5개)
            [
                {
                    "product_name": "...",
                    "brand": "...",
                    "channel": "...",
                    "review_count": 120
                },
                ...
            ]
        """
        with DBConnector() as db:
            # 브랜드로만 검색 쿼리 구성
            query = """
                SELECT product_name, brand, channel, COUNT(*) as review_count
                FROM preprocessed_reviews
                WHERE brand = ANY(%s)
            """
            params = [brands]

            # 채널 필터 추가 (있는 경우)
            if channels:
                query += " AND channel = ANY(%s)"
                params.append(channels)

            # 그룹화 및 정렬
            query += """
                GROUP BY product_name, brand, channel
                ORDER BY review_count DESC
                LIMIT 5
            """

            results = db.execute_query(query, tuple(params))

            # Dict 리스트로 변환
            return [dict(row) for row in results]

    def _get_all_channels(self) -> List[str]:
        """
        DB에 있는 모든 채널 리스트 가져오기

        Returns:
            채널명 리스트
        """
        with DBConnector() as db:
            query = """
                SELECT DISTINCT channel
                FROM preprocessed_reviews
                ORDER BY channel
            """
            results = db.execute_query(query)
            return [row['channel'] for row in results]

    def _get_all_brands(self) -> List[str]:
        """
        DB에 있는 모든 브랜드 리스트 가져오기

        Returns:
            브랜드명 리스트
        """
        with DBConnector() as db:
            query = """
                SELECT DISTINCT brand
                FROM preprocessed_reviews
                ORDER BY brand
            """
            results = db.execute_query(query)
            return [row['brand'] for row in results]

    def _get_all_products(self) -> List[str]:
        """
        DB에 있는 모든 제품 리스트 가져오기

        Returns:
            제품명 리스트
        """
        with DBConnector() as db:
            query = """
                SELECT DISTINCT product_name
                FROM preprocessed_reviews
                ORDER BY product_name
            """
            results = db.execute_query(query)
            return [row['product_name'] for row in results]

    def _generate_fallback_reason(
        self,
        review_count: int,
        brands: list,
        products: list,
        channels: list
    ) -> str:
        """
        Fallback 이유 생성

        Args:
            review_count: 리뷰 개수
            brands: 브랜드 리스트
            products: 제품 리스트
            channels: 채널 리스트

        Returns:
            Fallback 이유 문자열
        """
        parts = [
            f"⚠️ 데이터 부족 경고: {review_count}개 리뷰만 발견 (최소 요구: {MIN_REVIEW_COUNT}개)\n"
        ]

        # 필터 조건 표시
        filters = []
        if brands:
            filters.append(f"브랜드({', '.join(brands)})")
        if products:
            filters.append(f"제품({', '.join(products)})")
        if channels:
            filters.append(f"채널({', '.join(channels)})")

        if filters:
            parts.append(f"현재 필터: {' + '.join(filters)}")
            parts.append("\n**권장 사항:**")
            parts.append("  1. 필터 조건 완화 (예: 특정 제품명 대신 브랜드만 지정)")
            parts.append("  2. 다른 제품 선택")
            parts.append("  3. 전체 데이터로 분석")
        else:
            parts.append("전체 데이터에서도 리뷰가 부족합니다.")
            parts.append("\n**가능한 원인:**")
            parts.append("  - 데이터베이스에 리뷰가 충분히 적재되지 않음")
            parts.append("  - 전처리 과정에서 대부분의 리뷰가 필터링됨")

        parts.append("\n⚠️ 분석 결과의 통계적 신뢰도가 낮을 수 있습니다.")

        return "\n".join(parts)


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Validation Node 테스트 ===\n")

    validation = ValidationNode()

    # 테스트 케이스들
    test_cases = [
        {
            "name": "충분한 데이터",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": [],
                "channels": [],
                "intent": "attribute_analysis"
            }
        },
        {
            "name": "데이터 부족 (특정 제품)",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": ["존재하지않는제품"],
                "channels": [],
                "intent": "attribute_analysis"
            }
        },
        {
            "name": "데이터 부족 (필터 과다)",
            "parsed_query": {
                "brands": ["빌리프"],
                "products": ["모이스춰라이징밤"],
                "channels": ["올리브영"],
                "intent": "attribute_analysis"
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {test_case['name']}")
        print("=" * 80)

        # 초기 상태
        state = {
            "parsed_query": test_case["parsed_query"],
            "messages": []
        }

        # Validation Node 실행
        result = validation(state)

        # 결과 출력
        for msg in result["messages"]:
            print(f"\n[{msg['node']}] {msg['status']}:")
            print(msg["content"])

        print(f"\nFallback 모드: {result['is_fallback']}")
        print(f"리뷰 개수: {result['data_validation']['review_count']}")
