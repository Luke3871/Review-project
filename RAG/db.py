import psycopg2
from contextlib import contextmanager
from config import DB 

@contextmanager
def get_conn():
    conn = psycopg2.connect(**DB) 
    try:
        yield conn
    finally:
        conn.close()
