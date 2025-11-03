#//==============================================================================//#
"""
bm25_search.py
BM25 Keyword Search Tool for V4 ReAct Agent

Modified from agents_v2:
- Uses dashboard tokenizer
- Uses dashboard_config.DB_CONFIG

last_updated: 2025.10.26
"""
#//==============================================================================//#

import sys
import os

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
from rank_bm25 import BM25Okapi

from dashboard_config import DB_CONFIG
from analyzer.txt_mining.tokenizer import get_tokenizer_for_channel

#//==============================================================================//#
# BM25 Search Tool
#//==============================================================================//#

class BM25SearchTool:
    """BM25 Keyword Search"""

    def __init__(self):
        self.db_config = DB_CONFIG
        self.conn = None
        self.tokenizers = {}

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
        BM25 keyword search

        Args:
            query: 검색 쿼리
            top_k: 상위 N개
            filters: 필터 조건

        Returns:
            검색 결과 DataFrame
        """

        self.connect()

        # Get channel for tokenizer
        channel = filters.get('channel', 'OliveYoung') if filters else 'OliveYoung'

        # Get tokenizer (cached)
        if channel not in self.tokenizers:
            self.tokenizers[channel] = get_tokenizer_for_channel(channel)

        tokenizer = self.tokenizers[channel]

        # Build query
        sql = "SELECT * FROM reviews WHERE LENGTH(review_text) > 10"
        params = []

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

            if filters.get('date_from'):
                sql += " AND review_date >= %s"
                params.append(filters['date_from'])

            if filters.get('date_to'):
                sql += " AND review_date <= %s"
                params.append(filters['date_to'])

        sql += " LIMIT 50000"  # BM25는 메모리에서 처리하므로 제한

        # Execute
        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()

        df = pd.DataFrame(data, columns=columns)

        if df.empty:
            return df

        # Tokenize corpus
        tokenized_corpus = [tokenizer(text) for text in df['review_text']]

        # Build BM25 index
        bm25 = BM25Okapi(tokenized_corpus)

        # Tokenize query
        query_tokens = tokenizer(query)

        # Search
        scores = bm25.get_scores(query_tokens)

        # Top results
        top_indices = scores.argsort()[-top_k:][::-1]
        result_df = df.iloc[top_indices].copy()
        result_df['bm25_score'] = scores[top_indices]

        return result_df

    def close(self):
        """Close connection"""
        if self.conn and not self.conn.closed:
            self.conn.close()
