# test_basic_stats.py
import sys
import os

# analytics 폴더 고정
current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)
    
import pandas as pd
import psycopg2
from core.basic_stats import get_basic_statistics, get_channel_statistics, get_brand_statistics

conn = psycopg2.connect(
    dbname="ragdb",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)

df = pd.read_sql("SELECT * FROM reviews LIMIT 10000", conn)

# 기본 통계
stats = get_basic_statistics(df)
print("=== 기본 통계 ===")
for key, value in stats.items():
    print(f"{key}: {value}")

# 채널별
print("\n=== 채널별 통계 ===")
print(get_channel_statistics(df))

# 브랜드별
print("\n=== 브랜드별 통계 ===")
print(get_brand_statistics(df).head(10))

conn.close()