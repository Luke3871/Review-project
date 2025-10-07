import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

conn = psycopg2.connect(
    dbname = "ragdb",
    user = "postgres",
    password = "postgres",
    host = "localhost",
    port = 5432
)

cur = conn.cursor()

CSV_DIR = r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data\data_oliveyoung\processed_data\reviews_oliveyoung"

# csv 로 끝나는 모든 파일들 붙이기
for fname in os.listdir(CSV_DIR):
    if not fname.endswith(".csv"):
        continue
    
    # 파일별 경로
    fpath = os.path.join(CSV_DIR, fname)

    # 파일 읽기
    df = pd.read_csv(fpath)

    # 필요한 컬럼만 추출
    cols = [
    'review_id','product_url','product_name','brand','category','category_use',
    'product_price_sale','product_price_origin','sort_type','ranking',
    'reviewer_name','rating','review_date','selected_option','review_text','helpful_count'
    ]
    df = df[cols]

    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce").dt.date

    # 튜플로 변환
    values = [tuple(x) for x in df.to_numpy()]

    # 적재
    insert_sql = f"""
        INSERT INTO reviews ({','.join(cols)})
        VALUES %s
        ON CONFLICT (review_id) DO NOTHING;
        """
    
    # 배치크기 조절 (성능 때문에)
    execute_values(cur, insert_sql, values, page_size= 5000)
    conn.commit()

cur.close()
conn.close()
print("done")

conn = psycopg2.connect(
    dbname="ragdb",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
df = pd.read_sql("SELECT review_id, review_text FROM reviews", conn)
conn.close()

df.to_csv("reviews_for_embedding.csv", index=False, encoding="utf-8-sig")

import psycopg2
import numpy as np
import pandas as pd
from tqdm import tqdm

df = pd.read_csv("reviews_with_krsbert.csv")
embeddings = np.load(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\RAG\embeddings_ksrbert.npy")

conn = psycopg2.connect(
    dbname="ragdb",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)
cur = conn.cursor()

for rid, emb in tqdm(zip(df["review_id"], embeddings), total=len(df)):
    cur.execute(
        "UPDATE reviews SET embedding = %s WHERE review_id = %s",
        (emb.tolist(), rid)
    )

conn.commit()
cur.close()
conn.close()

