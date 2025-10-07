import psycopg2
from sentence_transformers import SentenceTransformer
from embed_model import get_embedding_model
from db import get_conn

def search_reviews(question, top_k=50):
    model = get_embedding_model()
    q_vec = model.encode([question])[0].tolist()

    sql = """
    SELECT review_id, review_text, brand, product_name, rating, review_date
    FROM reviews
    WHERE embedding IS NOT NULL
    ORDER BY embedding <-> %s::vector
    LIMIT %s;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (q_vec, top_k))
        return cur.fetchall()

