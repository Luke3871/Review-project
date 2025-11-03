#//==============================================================================//#
"""
vector_search.py
BGE-M3 Vector Search Tool

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
from sentence_transformers import SentenceTransformer

#//==============================================================================//#
# Vector Search Tool
#//==============================================================================//#

class VectorSearchTool:
    """BGE-M3 Vector Search"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None
        self.model = SentenceTransformer('BAAI/bge-m3')
    
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
        """Vector search with BGE-M3"""
        
        self.connect()
        
        # Encode query
        query_embedding = self.model.encode(query, normalize_embeddings=True)
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
        
        sql += f" ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding_str, top_k])
        
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