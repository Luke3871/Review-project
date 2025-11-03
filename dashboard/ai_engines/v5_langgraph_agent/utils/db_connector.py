"""
PostgreSQL 데이터베이스 연결 헬퍼

preprocessed_reviews 테이블에 접근하기 위한 유틸리티 함수들을 제공합니다.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Tuple
import sys
import os

# dashboard_config import를 위한 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from dashboard_config import DB_CONFIG


class DBConnector:
    """
    PostgreSQL 연결 관리 클래스

    with문으로 사용하면 자동으로 연결/해제됩니다:
        with DBConnector() as db:
            results = db.execute_query("SELECT * FROM ...")
    """

    def __init__(self):
        self.conn = None
        self.cur = None

    def __enter__(self):
        """with 문 시작 시 자동 연결"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 문 종료 시 자동 연결 해제"""
        self.close()

    def connect(self):
        """PostgreSQL 연결"""
        if not self.conn:
            try:
                self.conn = psycopg2.connect(**DB_CONFIG)
                # RealDictCursor: 결과를 dictionary로 반환 (컬럼명으로 접근 가능)
                self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
            except Exception as e:
                print(f"❌ DB 연결 실패: {e}")
                raise

    def close(self):
        """연결 종료"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        SQL 쿼리 실행

        Args:
            query: SQL 쿼리문
            params: 파라미터 튜플 (parameterized query용)

        Returns:
            결과 리스트 (각 row는 dictionary)
        """
        try:
            self.cur.execute(query, params)
            return self.cur.fetchall()
        except Exception as e:
            print(f"❌ 쿼리 실행 실패: {e}")
            print(f"   Query: {query}")
            print(f"   Params: {params}")
            raise

    def count_reviews(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None
    ) -> int:
        """
        필터 조건에 맞는 리뷰 개수 반환

        Args:
            brands: 브랜드 리스트 (예: ["빌리프", "VT"])
            products: 제품명 리스트 (부분 매치, 예: ["모이스춰라이징밤"])
            channels: 채널 리스트 (예: ["올리브영"])

        Returns:
            리뷰 개수
        """
        where_clause, params = build_filter_conditions(brands, products, channels)

        query = f"""
        SELECT COUNT(*) as count
        FROM preprocessed_reviews
        WHERE {where_clause}
        """

        result = self.execute_query(query, tuple(params))
        return result[0]['count'] if result else 0

    def fetch_reviews(
        self,
        brands: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        필터 조건에 맞는 리뷰 데이터 반환

        Args:
            brands: 브랜드 리스트
            products: 제품명 리스트 (부분 매치)
            channels: 채널 리스트
            limit: 최대 반환 개수

        Returns:
            리뷰 데이터 리스트 (각 row는 dictionary)
        """
        where_clause, params = build_filter_conditions(brands, products, channels)

        query = f"""
        SELECT *
        FROM preprocessed_reviews
        WHERE {where_clause}
        """

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, tuple(params))


# ===== 헬퍼 함수 =====

def build_filter_conditions(
    brands: Optional[List[str]] = None,
    products: Optional[List[str]] = None,
    channels: Optional[List[str]] = None
) -> Tuple[str, List]:
    """
    필터 조건을 SQL WHERE 절로 변환

    Args:
        brands: 브랜드 리스트
        products: 제품명 리스트
        channels: 채널 리스트

    Returns:
        (where_clause, params) 튜플
        예: ("brand = ANY(%s) AND product_name LIKE %s", [['빌리프'], '%모이스춰라이징밤%'])
    """
    conditions = []
    params = []

    # 브랜드 필터
    if brands:
        conditions.append("brand = ANY(%s)")
        params.append(brands)

    # 제품명 필터 (부분 매치 - LIKE)
    if products:
        product_conditions = " OR ".join(["product_name LIKE %s"] * len(products))
        conditions.append(f"({product_conditions})")
        params.extend([f"%{p}%" for p in products])

    # 채널 필터
    if channels:
        conditions.append("channel = ANY(%s)")
        params.append(channels)

    # 조건이 없으면 "1=1" (모든 행 선택)
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    return where_clause, params


# ===== 사용 예시 =====
if __name__ == "__main__":
    # 테스트 코드
    print("=== DB Connector 테스트 ===\n")

    # 1. 전체 리뷰 수
    with DBConnector() as db:
        total_count = db.count_reviews()
        print(f"전체 리뷰 수: {total_count}개")

    # 2. 빌리프 브랜드 리뷰 수
    with DBConnector() as db:
        belief_count = db.count_reviews(brands=["빌리프"])
        print(f"빌리프 리뷰 수: {belief_count}개")

    # 3. 빌리프 + 모이스춰라이징밤 리뷰 수
    with DBConnector() as db:
        specific_count = db.count_reviews(
            brands=["빌리프"],
            products=["모이스춰라이징밤"]
        )
        print(f"빌리프 모이스춰라이징밤 리뷰 수: {specific_count}개")

    # 4. 실제 데이터 가져오기 (3개만)
    with DBConnector() as db:
        reviews = db.fetch_reviews(
            brands=["빌리프"],
            limit=3
        )
        print(f"\n빌리프 리뷰 샘플 ({len(reviews)}개):")
        for i, review in enumerate(reviews, 1):
            print(f"{i}. {review['product_name']} (채널: {review['channel']})")
