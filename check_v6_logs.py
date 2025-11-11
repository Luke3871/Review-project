"""V6 로그 DB 확인 스크립트"""
import psycopg2
from datetime import datetime

try:
    # DB 연결
    conn = psycopg2.connect(
        dbname='cosmetic_reviews',
        user='postgres',
        password='postgres',
        host='localhost',
        port=5432
    )
    cur = conn.cursor()

    # 테이블 존재 확인
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'v6_chatbot_logs'
        )
    """)
    table_exists = cur.fetchone()[0]

    if not table_exists:
        print("[X] v6_chatbot_logs table does not exist.")
    else:
        print("[OK] v6_chatbot_logs table exists")

        # 총 로그 수
        cur.execute('SELECT COUNT(*) FROM v6_chatbot_logs')
        total_count = cur.fetchone()[0]
        print(f"\n총 로그 수: {total_count}개")

        if total_count > 0:
            # 최근 5개 로그
            cur.execute("""
                SELECT
                    log_id,
                    timestamp,
                    user_query,
                    complexity,
                    total_queries,
                    successful_queries,
                    total_duration,
                    visualization_strategy
                FROM v6_chatbot_logs
                ORDER BY timestamp DESC
                LIMIT 5
            """)
            rows = cur.fetchall()

            print("\n" + "="*100)
            print("최근 5개 로그:")
            print("="*100)

            for row in rows:
                log_id, timestamp, query, complexity, total_q, success_q, duration, viz = row
                print(f"\nID: {log_id}")
                print(f"시간: {timestamp}")
                print(f"질문: {query[:80]}...")
                print(f"복잡도: {complexity} | 쿼리: {total_q}개 (성공: {success_q}개) | 소요시간: {duration:.2f}초")
                print(f"시각화: {viz}")
                print("-"*100)

            # 복잡도별 통계
            cur.execute("""
                SELECT
                    complexity,
                    COUNT(*) as count,
                    AVG(total_duration) as avg_duration
                FROM v6_chatbot_logs
                WHERE complexity IS NOT NULL
                GROUP BY complexity
                ORDER BY count DESC
            """)

            complexity_stats = cur.fetchall()

            if complexity_stats:
                print("\n" + "="*100)
                print("복잡도별 통계:")
                print("="*100)
                for comp, count, avg_dur in complexity_stats:
                    print(f"{comp}: {count}개 (평균 {avg_dur:.2f}초)")
        else:
            print("\n아직 저장된 로그가 없습니다.")

    cur.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"[ERROR] DB connection failed: {e}")
except Exception as e:
    print(f"[ERROR] Exception: {e}")
