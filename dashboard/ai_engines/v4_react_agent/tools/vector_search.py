#//==============================================================================//#
"""
vector_search.py
BGE-M3 Vector Search Tool for V4 ReAct Agent

Modified from agents_v2:
- Uses dashboard_config.DB_CONFIG
- Optimized for dashboard integration

last_updated: 2025.10.26
"""
#//==============================================================================//#

import sys
import os

# IMPORTANT: Set Keras backend BEFORE any imports that use transformers
os.environ['KERAS_BACKEND'] = 'tensorflow'

# Add dashboard to path
current_file = os.path.abspath(__file__)
v4_dir = os.path.dirname(os.path.dirname(current_file))
ai_engines_dir = os.path.dirname(v4_dir)
dashboard_dir = os.path.dirname(ai_engines_dir)

if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

import pandas as pd
import psycopg2
from typing import Dict, Optional
from sentence_transformers import SentenceTransformer

from dashboard_config import DB_CONFIG

#//==============================================================================//#
# Vector Search Tool
#//==============================================================================//#

class VectorSearchTool:
    """BGE-M3 Vector Search"""

    _model = None  # Class variable for shared BGE-M3 model

    def __init__(self):
        self.db_config = DB_CONFIG
        self.conn = None

        # Load BGE-M3 model (shared across instances)
        if VectorSearchTool._model is None:
            VectorSearchTool._model = SentenceTransformer('BAAI/bge-m3')

    def connect(self):
        """Connect to PostgreSQL"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                dbname=self.db_config['dbname'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                client_encoding='utf8'
            )

    def search(
        self,
        query: str,
        top_k: int = 10000,
        filters: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Vector search with BGE-M3

        Args:
            query: 검색 쿼리
            top_k: 상위 N개 (기본 10000 for Stage 1)
            filters: 필터 조건 {brand, channel, category, product_name_like, min_rating, date_from, date_to}

        Returns:
            검색 결과 DataFrame
        """

        self.connect()

        # 제품명 필터가 있으면 Vector 검색 없이 전체 가져오기
        if filters and filters.get('product_name_like'):
            return self._search_without_vector(filters, top_k)

        # Encode query with BGE-M3
        query_embedding = VectorSearchTool._model.encode(query, normalize_embeddings=True)
        query_embedding_str = str(query_embedding.tolist())

        # Build SQL
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

        params = [query_embedding_str]

        # Apply filters
        if filters:
            if filters.get('brand'):
                sql += " AND brand = %s"
                params.append(filters['brand'])

            if filters.get('channel'):
                sql += " AND channel = %s"
                params.append(filters['channel'])

            if filters.get('channels'):  # 복수 채널
                placeholders = ','.join(['%s'] * len(filters['channels']))
                sql += f" AND channel IN ({placeholders})"
                params.extend(filters['channels'])

            if filters.get('category'):
                sql += " AND category = %s"
                params.append(filters['category'])

            if filters.get('product_name_like'):
                sql += " AND product_name LIKE %s"
                params.append(filters['product_name_like'])

            if filters.get('min_rating'):
                sql += " AND rating >= %s"
                params.append(filters['min_rating'])

            if filters.get('date_from'):
                sql += " AND review_date >= %s"
                params.append(filters['date_from'])

            if filters.get('date_to'):
                sql += " AND review_date <= %s"
                params.append(filters['date_to'])

        sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding_str, top_k])

        # Execute
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()

        return pd.DataFrame(data, columns=columns)

    def _search_without_vector(
        self,
        filters: Dict,
        top_k: int
    ) -> pd.DataFrame:
        """
        제품명 필터가 있을 때 Vector 검색 없이 SQL 필터만 사용

        이미 product_name으로 제품을 특정했으므로,
        Vector 유사도 없이 최신순으로 가져옴

        Args:
            filters: 필터 조건
            top_k: 최대 개수

        Returns:
            검색 결과 DataFrame
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
            reviewer_skin_features,
            1.0 as similarity
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

        if filters.get('channels'):
            placeholders = ','.join(['%s'] * len(filters['channels']))
            sql += f" AND channel IN ({placeholders})"
            params.extend(filters['channels'])

        if filters.get('category'):
            sql += " AND category = %s"
            params.append(filters['category'])

        if filters.get('product_name_like'):
            sql += " AND product_name LIKE %s"
            params.append(filters['product_name_like'])

        if filters.get('min_rating'):
            sql += " AND rating >= %s"
            params.append(filters['min_rating'])

        if filters.get('date_from'):
            sql += " AND review_date >= %s"
            params.append(filters['date_from'])

        if filters.get('date_to'):
            sql += " AND review_date <= %s"
            params.append(filters['date_to'])

        # 최신순으로 정렬
        sql += " ORDER BY review_date DESC LIMIT %s"
        params.append(top_k)

        # Execute
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()

        return pd.DataFrame(data, columns=columns)

    def close(self):
        """Close connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
