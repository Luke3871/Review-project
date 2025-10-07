#//==============================================================================//#
"""
execution_agent.py
실행 계획을 받아서 실제로 실행 (RAG 포함)

last_updated : 2025.10.02
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
from typing import Dict, List
from datetime import datetime, timedelta
from openai import OpenAI
from core.basic_stats import compute_product_statistics
from core.brand_analysis import analyze_brand_attributes

#//==============================================================================//#
# Execution Agent
#//==============================================================================//#

class ExecutionAgent:
    """
    계획을 받아서 실행 (RAG 벡터 검색 포함)
    """
    
    def __init__(self, db_config: Dict, api_key: str = None):
        self.db_config = db_config
        self.api_key = api_key
        self.conn = None
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
    
    def connect_db(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.db_config)
    
    def execute_plan(self, plan: Dict) -> Dict:
        """
        계획 실행
        """
        
        self.connect_db()
        results = {
            'plan': plan,
            'data': None,
            'retrieved_reviews': None,
            'analysis': None,
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
                    results['retrieved_reviews'] = self.retrieve_similar_reviews(
                        step.get('query'),
                        step.get('filters', {}),
                        step.get('top_k', 30)
                    )
                
                elif action == 'query_db':
                    db_result = self.query_database(
                        step.get('table'),
                        step.get('filters', {})
                    )
                    
                    # 여러 테이블 조회 결과 합치기
                    if results['data'] is None:
                        results['data'] = db_result
                    else:
                        # dict로 테이블별 저장
                        if not isinstance(results['data'], dict):
                            results['data'] = {'first': results['data']}
                        results['data'][step.get('table')] = db_result
                
                elif action == 'load_reviews':
                    loaded = self.load_reviews(step.get('filters', {}))
                    results['data'] = loaded
                
                elif action == 'analyze':
                    if results.get('data') is None:
                        results['error'] = "분석할 데이터 없음"
                        continue
                    
                    results['analysis'] = self.run_analysis(
                        results['data'],
                        step.get('module'),
                        step.get('params', {})
                    )
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def retrieve_similar_reviews(self, query: str, filters: Dict, top_k: int) -> pd.DataFrame:
        """
        벡터 검색으로 유사 리뷰 검색
        """
        
        if not self.api_key:
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
                product_name, brand, channel, rating, review_text, review_date,
                1 - (embedding <=> %s::vector) as similarity
            FROM reviews
            WHERE 1=1
            """
            
            params = [str(query_embedding)]
            
            # 필터 추가
            if filters.get('channel'):
                sql += " AND channel = %s"
                params.append(filters['channel'])
            
            if filters.get('brand'):
                sql += " AND brand = %s"
                params.append(filters['brand'])
            
            if filters.get('product_name'):
                sql += " AND product_name = %s"
                params.append(filters['product_name'])
            
            if filters.get('period_days'):
                cutoff = (datetime.now() - timedelta(days=filters['period_days'])).strftime('%Y-%m-%d')
                sql += " AND review_date >= %s"
                params.append(cutoff)
            
            sql += f" ORDER BY embedding <=> %s::vector LIMIT %s"
            params.extend([str(query_embedding), top_k])
            
            # 실행
            with self.conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description]
                data = cur.fetchall()
            
            return pd.DataFrame(data, columns=columns)
            
        except Exception as e:
            print(f"벡터 검색 오류: {e}")
            return pd.DataFrame()
    
    def query_database(self, table: str, filters: Dict) -> pd.DataFrame:
        """DB 조회"""
        
        where_clauses = []
        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        sql = f"SELECT * FROM {table} WHERE {where_sql}"
        
        return pd.read_sql(sql, self.conn)
    
    def load_reviews(self, filters: Dict) -> pd.DataFrame:
        """reviews 로드"""
        
        sql = "SELECT * FROM reviews WHERE 1=1"
        
        if filters.get('period_days'):
            cutoff = (datetime.now() - timedelta(days=filters['period_days'])).strftime('%Y-%m-%d')
            sql += f" AND review_date >= '{cutoff}'"
        
        if filters.get('brand'):
            sql += f" AND brand = '{filters['brand']}'"
        
        if filters.get('channel'):
            sql += f" AND channel = '{filters['channel']}'"
        
        return pd.read_sql(sql, self.conn)
    
    def run_analysis(self, data: pd.DataFrame, module: str, params: Dict) -> Dict:
        """분석 실행"""
        
        if data.empty:
            return {'error': '데이터 없음'}
        
        if module == 'brand_analysis':
            results = analyze_brand_attributes(data)
            
            if params.get('brand') or params.get('attribute'):
                results = [
                    r for r in results
                    if (not params.get('brand') or r['brand'] == params['brand']) and
                       (not params.get('attribute') or r['attribute'] == params['attribute'])
                ]
            
            return {'brand_attributes': results}
        
        return {'error': f'알 수 없는 모듈: {module}'}
    
    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()