# test_connection.py
import os
import sys
import locale

# 강제로 UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PGCLIENTENCODING'] = 'UTF8'

# 작업 디렉토리를 C:\ 로 변경
os.chdir('C:\\')

# 로케일 변경
try:
    locale.setlocale(locale.LC_ALL, 'C')
except:
    pass

import psycopg2

print("Test 1: Basic connect")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='cosmetic_reviews',
        user='postgres',
        password='postgres'
    )
    print("✅ Basic connect OK")
    conn.close()
except Exception as e:
    print(f"❌ Basic connect FAILED: {e}")

print("\nTest 2: With client_encoding keyword")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='cosmetic_reviews',
        user='postgres',
        password='postgres',
        client_encoding='utf8'
    )
    print("✅ With client_encoding OK")
    conn.close()
except Exception as e:
    print(f"❌ With client_encoding FAILED: {e}")

print("\nTest 3: With DSN string")
try:
    dsn = "host=localhost port=5432 dbname=cosmetic_reviews user=postgres password=postgres client_encoding=utf8"
    conn = psycopg2.connect(dsn)
    print("✅ DSN string OK")
    conn.close()
except Exception as e:
    print(f"❌ DSN string FAILED: {e}")

print("\nTest 4: Dict unpack")
try:
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'cosmetic_reviews',
        'user': 'postgres',
        'password': 'postgres'
    }
    conn = psycopg2.connect(**db_config)
    print("✅ Dict unpack OK")
    conn.close()
except Exception as e:
    print(f"❌ Dict unpack FAILED: {e}")

print("\nTest 5: Dict unpack + client_encoding")
try:
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'cosmetic_reviews',
        'user': 'postgres',
        'password': 'postgres'
    }
    conn = psycopg2.connect(**db_config, client_encoding='utf8')
    print("✅ Dict unpack + client_encoding OK")
    conn.close()
except Exception as e:
    print(f"❌ Dict unpack + client_encoding FAILED: {e}")

print("\n" + "="*60)
print("Test completed")