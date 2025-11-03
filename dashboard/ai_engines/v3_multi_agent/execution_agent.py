#//==============================================================================//#
"""
execution_agent.py
실행 계획을 받아서 실제로 실행

수정 사항:
- DB Config: dashboard_config.DB_CONFIG 사용
- 임베딩 모델: OpenAI → BGE-M3 (로컬)
- 컬럼명: dashboard reviews 테이블에 맞게 조정

last_updated : 2025.10.26
"""
#//==============================================================================//#

import sys
import os

# dashboard 경로 추가
dashboard_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import pandas as pd
import psycopg2
from typing import Dict, Optional
from datetime import datetime, timedelta

# dashboard DB config 사용
from dashboard_config import DB_CONFIG

#//==============================================================================//#
# Execution Agent
#//==============================================================================//#

class ExecutionAgent:
    """
    계획을 받아서 실행
    """

    # 클래스 변수: BGE-M3 모델 (한 번만 로드)
    _embedding_model = None

    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: OpenAI API 키 (사용 안 함, 호환성 유지)
        """
        self.conn = None
        # Keras 백엔드 설정
        os.environ['KERAS_BACKEND'] = 'tensorflow'

    def connect_db(self):
        """DB 연결"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**DB_CONFIG)

    def execute_plan(self, plan: Dict) -> Dict:
        """
        계획 실행
        """

        self.connect_db()
        results = {
            'plan': plan,
            'reviews': None,
            'stats': None,
            'error': None
        }

        # answerable 체크
        if not plan.get('answerable', True):
            results['error'] = 'not_answerable'
            return results

        try:
            for step in plan.get('steps', []):
                action = step.get('action')

                if action == 'reject':
                    results['error'] = step.get('reason', '답변 불가')
                    return results

                elif action == 'retrieve_similar_reviews':
                    results['reviews'] = self.retrieve_similar_reviews(
                        step.get('query'),
                        step.get('filters', {}),
                        step.get('top_k', 30)
                    )

                elif action == 'filter_reviews':
                    results['reviews'] = self.filter_reviews(
                        step.get('filters', {})
                    )

                elif action == 'calculate_stats':
                    # 리뷰가 없으면 먼저 로드
                    if results.get('reviews') is None or results['reviews'].empty:
                        results['reviews'] = self.filter_reviews(
                            step.get('filters', {})
                        )

                    results['stats'] = self.calculate_stats(
                        results['reviews'],
                        step.get('metric', 'rating'),
                        step.get('group_by')
                    )

        except Exception as e:
            results['error'] = str(e)

        return results

    def retrieve_similar_reviews(
        self,
        query: str,
        filters: Dict,
        top_k: int
    ) -> pd.DataFrame:
        """
        벡터 검색으로 유사 리뷰 검색 (BGE-M3 사용)
        """

        try:
            # BGE-M3 모델 로드 (첫 호출 시에만)
            if ExecutionAgent._embedding_model is None:
                print("BGE-M3 모델 로딩 중...")
                from sentence_transformers import SentenceTransformer
                ExecutionAgent._embedding_model = SentenceTransformer('BAAI/bge-m3')
                print("BGE-M3 모델 로딩 완료!")

            # 쿼리 임베딩
            query_embedding = ExecutionAgent._embedding_model.encode(query).tolist()

            # pgvector 검색
            sql = """
            SELECT
                review_id,
                product_name,
                brand,
                channel,
                category,
                rating,
                review_date,
                review_text,
                reviewer_skin_features,
                1 - (embedding <=> %s::vector) as similarity
            FROM reviews
            WHERE LENGTH(review_text) > 10
            """

            params = [str(query_embedding)]

            # 필터 추가
            if filters.get('channel'):
                sql += " AND channel = %s"
                params.append(filters['channel'])

            if filters.get('brand'):
                sql += " AND brand = %s"
                params.append(filters['brand'])

            if filters.get('category'):
                sql += " AND category = %s"
                params.append(filters['category'])

            if filters.get('min_rating'):
                sql += " AND rating >= %s"
                params.append(filters['min_rating'])

            if filters.get('date_from'):
                sql += " AND review_date >= %s"
                params.append(filters['date_from'])

            if filters.get('date_to'):
                sql += " AND review_date <= %s"
                params.append(filters['date_to'])

            if filters.get('skin_features'):
                sql += " AND reviewer_skin_features LIKE %s"
                params.append(f"%{filters['skin_features']}%")

            sql += f" ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([str(query_embedding), top_k])

            # 실행
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()

            df = pd.DataFrame(data, columns=columns)
            print(f"벡터 검색 완료: {len(df)}개 리뷰")
            return df

        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def filter_reviews(self, filters: Dict) -> pd.DataFrame:
        """
        조건 필터링으로 리뷰 검색
        """

        sql = """
        SELECT
            review_id,
            product_name,
            brand,
            channel,
            category,
            rating,
            review_date,
            review_text,
            reviewer_skin_features
        FROM reviews
        WHERE LENGTH(review_text) > 10
        """

        params = []

        if filters.get('brand'):
            sql += " AND brand = %s"
            params.append(filters['brand'])

        if filters.get('channel'):
            sql += " AND channel = %s"
            params.append(filters['channel'])

        if filters.get('category'):
            sql += " AND category = %s"
            params.append(filters['category'])

        if filters.get('min_rating'):
            sql += " AND rating >= %s"
            params.append(filters['min_rating'])

        if filters.get('date_from'):
            sql += " AND review_date >= %s"
            params.append(filters['date_from'])

        if filters.get('date_to'):
            sql += " AND review_date <= %s"
            params.append(filters['date_to'])

        if filters.get('skin_features'):
            sql += " AND reviewer_skin_features LIKE %s"
            params.append(f"%{filters['skin_features']}%")

        sql += " LIMIT 10000"  # 안전장치

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()

            df = pd.DataFrame(data, columns=columns)
            print(f"필터 검색 완료: {len(df)}개 리뷰")
            return df

        except Exception as e:
            print(f"필터 검색 오류: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def calculate_stats(
        self,
        df: pd.DataFrame,
        metric: str = 'rating',
        group_by: Optional[str] = None
    ) -> Dict:
        """
        통계 계산
        """

        if df.empty:
            return {'error': '데이터 없음'}

        stats = {}

        # 기본 통계
        stats['총_리뷰수'] = len(df)

        if 'rating' in df.columns:
            # rating을 숫자로 변환
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
            stats['평균_평점'] = float(df['rating_numeric'].mean())
            stats['평점_분포'] = df['rating_numeric'].value_counts().sort_index().to_dict()

        # 그룹별 통계
        if group_by and group_by in df.columns:
            grouped = df.groupby(group_by)

            stats['그룹별_개수'] = grouped.size().to_dict()

            if 'rating_numeric' in df.columns:
                stats['그룹별_평균평점'] = grouped['rating_numeric'].mean().to_dict()

        print(f"통계 계산 완료: {len(df)}개 리뷰")
        return stats

    def close(self):
        """연결 종료"""
        if self.conn and not self.conn.closed:
            self.conn.close()
