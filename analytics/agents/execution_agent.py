#//==============================================================================//#
"""
execution_agent.py
실행 계획을 받아서 실제로 실행

last_updated : 2025.10.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import psycopg2
from typing import Dict, Optional
from datetime import datetime, timedelta
from openai import OpenAI

#//==============================================================================//#
# Execution Agent
#//==============================================================================//#

class ExecutionAgent:
    """
    계획을 받아서 실행
    """
    
    def __init__(self, db_config: Dict, api_key: str = None):
        self.db_config = db_config
        self.api_key = api_key
        self.conn = None
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
    
    def connect_db(self):
        """DB 연결"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
    
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
        벡터 검색으로 유사 리뷰 검색
        """
        
        if not self.api_key:
            print("API Key 없음 - 벡터 검색 불가")
            return pd.DataFrame()
        
        try:
            # 쿼리 임베딩
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = response.data[0].embedding
            
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
            stats['평균_평점'] = float(df['rating'].mean())
            stats['평점_분포'] = df['rating'].value_counts().sort_index().to_dict()
        
        # 그룹별 통계
        if group_by and group_by in df.columns:
            grouped = df.groupby(group_by)
            
            stats['그룹별_개수'] = grouped.size().to_dict()
            
            if 'rating' in df.columns:
                stats['그룹별_평균평점'] = grouped['rating'].mean().to_dict()
        
        print(f"통계 계산 완료: {len(df)}개 리뷰")
        return stats
    
    def close(self):
        """연결 종료"""
        if self.conn and not self.conn.closed:
            self.conn.close()