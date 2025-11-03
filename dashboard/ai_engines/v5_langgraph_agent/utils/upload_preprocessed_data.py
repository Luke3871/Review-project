#//==============================================================================//#
"""
upload_preprocessed_data.py
전처리된 JSON 데이터를 PostgreSQL에 업로드

5000개 전처리 데이터:
- analyzed_results_5000.json
- failed_retry_results.json
"""
#//==============================================================================//#

import json
import psycopg2
from psycopg2.extras import Json
import sys
import os

# DB Config 직접 정의
DB_CONFIG = {
    "dbname": "cosmetic_reviews",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

def load_json_file(file_path):
    """JSON 파일 로드"""
    print(f"Loading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")
    return data

def upload_to_db(data_list):
    """PostgreSQL에 업로드"""

    conn = psycopg2.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )

    cur = conn.cursor()

    success_count = 0
    skip_count = 0
    error_count = 0

    for item in data_list:
        try:
            review_id = item.get('review_id')
            analysis = item.get('analysis', {})
            product_name = item.get('product_name')
            channel = item.get('channel')

            # 브랜드 및 카테고리 추출
            brand = analysis.get('표준_브랜드')
            category = analysis.get('제품_카테고리')

            # INSERT (UPSERT)
            cur.execute("""
                INSERT INTO preprocessed_reviews
                    (review_id, analysis, brand, product_name, channel, category)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (review_id)
                DO UPDATE SET
                    analysis = EXCLUDED.analysis,
                    brand = EXCLUDED.brand,
                    product_name = EXCLUDED.product_name,
                    channel = EXCLUDED.channel,
                    category = EXCLUDED.category
            """, (
                review_id,
                Json(analysis),
                brand,
                product_name,
                channel,
                category
            ))

            success_count += 1

            if success_count % 100 == 0:
                print(f"Progress: {success_count} records inserted...")
                conn.commit()

        except Exception as e:
            print(f"Error processing {review_id}: {e}")
            error_count += 1
            continue

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n=== Upload Complete ===")
    print(f"Success: {success_count}")
    print(f"Skipped: {skip_count}")
    print(f"Errors: {error_count}")
    print(f"Total: {len(data_list)}")

    return success_count

if __name__ == "__main__":
    # 파일 경로
    file1 = r"C:\ReviewFW_LG_hnh\analyzed_results_5000.json"
    file2 = r"C:\ReviewFW_LG_hnh\failed_retry_results.json"

    # 데이터 로드
    data1 = load_json_file(file1)
    data2 = load_json_file(file2)

    # 합치기
    all_data = data1 + data2
    print(f"\nTotal records to upload: {len(all_data)}")

    # 업로드
    upload_to_db(all_data)
