#//==============================================================================//#
"""
bm25_search.py
BM25 Keyword Search Tool

last_updated: 2025.01.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import psycopg2
from typing import Dict, Optional
from rank_bm25 import BM25Okapi

tokenizer_path = os.path.join(analytics_dir, 'utils')
if tokenizer_path not in sys.path:
    sys.path.insert(0, tokenizer_path)

from utils.tokenizer import get_tokenizer_for_channel

#//==============================================================================//#
# BM25 Search Tool
#//==============================================================================//#

class BM25SearchTool:
    """BM25 Keyword Search"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.tokenizers = {}
    
    def connect(self):
        """Connect to PostgreSQL"""
        if not self.conn or self.conn.closed:
            # Use DSN string directly
            dsn = "host={} port={} dbname={} user={} password={} client_encoding=utf8".format(
                self.db_config['host'],
                self.db_config['port'],
                self.db_config['database'],
                self.db_config['user'],
                self.db_config['password']
            )
            self.conn = psycopg2.connect(dsn)
    
    def search(
        self,
        query: str,
        top_k: int = 30,
        filters: Optional[Dict] = None
    ) -> pd.DataFrame:
        """BM25 keyword search"""
        
        self.connect()
        
        # Get channel
        channel = filters.get('channel', 'OliveYoung') if filters else 'OliveYoung'
        
        # Get tokenizer
        if channel not in self.tokenizers:
            self.tokenizers[channel] = get_tokenizer_for_channel(channel)
        
        tokenizer = self.tokenizers[channel]
        
        # Load reviews
        sql = "SELECT * FROM reviews WHERE LENGTH(review_text) > 10"
        params = []
        
        if filters:
            if filters.get('brand'):
                sql += " AND brand = %s"
                params.append(filters['brand'])
            
            if filters.get('channel'):
                sql += " AND channel = %s"
                params.append(filters['channel'])
            
            if filters.get('category'):
                sql += " AND category = %s"
                params.append(filters['category'])
            
            if filters.get('date_from'):
                sql += " AND review_date >= %s"
                params.append(filters['date_from'])
        
        sql += " LIMIT 10000"
        
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