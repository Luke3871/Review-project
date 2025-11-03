#//==============================================================================//#
"""
query_logger.py
V6 사용 기록 로깅

- 사용자 질문 기록
- SQL 쿼리 기록
- 실행 결과 기록
- 오류 기록

last_updated: 2025.10.29
"""
#//==============================================================================//#

import json
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .config import DB_CONFIG


class QueryLogger:
    """V6 사용 기록 로거"""

    def __init__(self, username: str = "anonymous", save_to_db: bool = True, save_to_file: bool = True):
        """
        Args:
            username: 사용자명
            save_to_db: DB에 저장 여부
            save_to_file: 파일에 저장 여부
        """
        self.username = username
        self.save_to_db = save_to_db
        self.save_to_file = save_to_file
        self.log_dir = Path("logs/v6_chatbot")

        if save_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        if save_to_db:
            self._ensure_log_table()

    def _ensure_log_table(self):
        """로그 테이블 생성 (없으면)"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS v6_chatbot_logs (
                    log_id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    user_query TEXT NOT NULL,
                    complexity TEXT,

                    -- 추출된 엔티티
                    parsed_entities JSONB,

                    -- 생성된 SQL 쿼리들
                    sql_queries JSONB,

                    -- 실행 결과
                    total_queries INTEGER,
                    successful_queries INTEGER,
                    failed_queries INTEGER,
                    total_data_rows INTEGER,

                    -- 시각화 정보
                    visualization_strategy TEXT,
                    visualization_confidence FLOAT,

                    -- 처리 시간
                    total_duration FLOAT,
                    processing_steps INTEGER,

                    -- 각 노드별 상세 정보
                    node_details JSONB,

                    -- 오류 정보 (있는 경우)
                    error_info JSONB,

                    -- 최종 응답 (텍스트만)
                    final_response_text TEXT,

                    -- 사용자 피드백
                    user_feedback TEXT,  -- 'positive' | 'negative' | NULL
                    feedback_reason TEXT,  -- 피드백 이유
                    feedback_comment TEXT,  -- 추가 코멘트
                    feedback_timestamp TIMESTAMP  -- 피드백 시간
                )
            """)

            # 인덱스 생성
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_v6_logs_username
                ON v6_chatbot_logs(username)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_v6_logs_timestamp
                ON v6_chatbot_logs(timestamp DESC)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_v6_logs_complexity
                ON v6_chatbot_logs(complexity)
            """)

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"로그 테이블 생성 실패: {e}")

    def log_query(
        self,
        user_query: str,
        state: Dict[str, Any],
        final_response: Dict[str, Any],
        error: Optional[Dict] = None
    ):
        """
        쿼리 실행 로그 저장

        Args:
            user_query: 사용자 질문
            state: AgentState (전체 실행 상태)
            final_response: 최종 응답
            error: 오류 정보 (있는 경우)
        """
        log_entry = self._create_log_entry(user_query, state, final_response, error)

        if self.save_to_db:
            self._save_to_db(log_entry)

        if self.save_to_file:
            self._save_to_file(log_entry)

    def _create_log_entry(
        self,
        user_query: str,
        state: Dict[str, Any],
        final_response: Dict[str, Any],
        error: Optional[Dict]
    ) -> Dict[str, Any]:
        """로그 엔트리 생성"""

        # 메타데이터 추출
        metadata = final_response.get("metadata", {})

        # 노드별 상세 정보 (messages에서 추출)
        node_details = []
        for msg in state.get("messages", []):
            node_details.append({
                "node": msg.get("node"),
                "status": msg.get("status"),
                "duration": msg.get("duration"),
                "content": msg.get("content"),
                "error": msg.get("error"),
                "suggestion": msg.get("suggestion")
            })

        log_entry = {
            "username": self.username,
            "timestamp": datetime.now(),
            "user_query": user_query,
            "complexity": metadata.get("complexity", "unknown"),

            # 엔티티
            "parsed_entities": state.get("parsed_entities", {}),

            # SQL 쿼리들
            "sql_queries": state.get("sql_queries", []),

            # 실행 결과
            "total_queries": metadata.get("total_queries", 0),
            "successful_queries": metadata.get("successful_queries", 0),
            "failed_queries": metadata.get("total_queries", 0) - metadata.get("successful_queries", 0),
            "total_data_rows": metadata.get("total_data_rows", 0),

            # 시각화
            "visualization_strategy": final_response.get("visualization_strategy", "none"),
            "visualization_confidence": metadata.get("visualization_confidence", 0.0),

            # 처리 시간
            "total_duration": metadata.get("total_duration", 0.0),
            "processing_steps": metadata.get("processing_steps", 0),

            # 노드 상세
            "node_details": node_details,

            # 오류
            "error_info": error,

            # 최종 응답 텍스트
            "final_response_text": final_response.get("text", "")
        }

        return log_entry

    def _save_to_db(self, log_entry: Dict[str, Any]):
        """DB에 저장"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO v6_chatbot_logs (
                    username, timestamp, user_query, complexity,
                    parsed_entities, sql_queries,
                    total_queries, successful_queries, failed_queries, total_data_rows,
                    visualization_strategy, visualization_confidence,
                    total_duration, processing_steps,
                    node_details, error_info, final_response_text
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
            """, (
                log_entry["username"],
                log_entry["timestamp"],
                log_entry["user_query"],
                log_entry["complexity"],
                json.dumps(log_entry["parsed_entities"], ensure_ascii=False),
                json.dumps(log_entry["sql_queries"], ensure_ascii=False),
                log_entry["total_queries"],
                log_entry["successful_queries"],
                log_entry["failed_queries"],
                log_entry["total_data_rows"],
                log_entry["visualization_strategy"],
                log_entry["visualization_confidence"],
                log_entry["total_duration"],
                log_entry["processing_steps"],
                json.dumps(log_entry["node_details"], ensure_ascii=False),
                json.dumps(log_entry["error_info"], ensure_ascii=False) if log_entry["error_info"] else None,
                log_entry["final_response_text"]
            ))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"DB 로그 저장 실패: {e}")

    def _save_to_file(self, log_entry: Dict[str, Any]):
        """JSON 파일로 저장"""
        try:
            # 날짜별 로그 파일
            date_str = log_entry["timestamp"].strftime("%Y%m%d")
            log_file = self.log_dir / f"v6_log_{date_str}.jsonl"

            # timestamp를 문자열로 변환
            log_entry_copy = log_entry.copy()
            log_entry_copy["timestamp"] = log_entry["timestamp"].isoformat()

            # JSONL 형식으로 추가 (한 줄에 하나씩)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry_copy, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"파일 로그 저장 실패: {e}")

    def get_user_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자의 최근 질문 히스토리"""
        if not self.save_to_db:
            return []

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    log_id,
                    timestamp,
                    user_query,
                    complexity,
                    total_duration,
                    successful_queries,
                    total_queries,
                    visualization_strategy
                FROM v6_chatbot_logs
                WHERE username = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (self.username, limit))

            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            history = [dict(zip(columns, row)) for row in rows]

            cur.close()
            conn.close()

            return history

        except Exception as e:
            print(f"히스토리 조회 실패: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """사용자의 사용 통계"""
        if not self.save_to_db:
            return {}

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # 전체 통계
            cur.execute("""
                SELECT
                    COUNT(*) as total_queries,
                    AVG(total_duration) as avg_duration,
                    SUM(CASE WHEN error_info IS NULL THEN 1 ELSE 0 END) as successful_count,
                    SUM(CASE WHEN error_info IS NOT NULL THEN 1 ELSE 0 END) as error_count,
                    AVG(visualization_confidence) as avg_viz_confidence
                FROM v6_chatbot_logs
                WHERE username = %s
            """, (self.username,))

            result = cur.fetchone()

            # 복잡도별 통계
            cur.execute("""
                SELECT
                    complexity,
                    COUNT(*) as count,
                    AVG(total_duration) as avg_duration
                FROM v6_chatbot_logs
                WHERE username = %s
                GROUP BY complexity
                ORDER BY count DESC
            """, (self.username,))

            complexity_stats = cur.fetchall()

            cur.close()
            conn.close()

            return {
                "total_queries": result[0] or 0,
                "avg_duration": round(result[1] or 0, 2),
                "successful_count": result[2] or 0,
                "error_count": result[3] or 0,
                "avg_viz_confidence": round(result[4] or 0, 2),
                "complexity_distribution": {
                    row[0]: {"count": row[1], "avg_duration": round(row[2], 2)}
                    for row in complexity_stats
                }
            }

        except Exception as e:
            print(f"통계 조회 실패: {e}")
            return {}

    def save_feedback(
        self,
        log_id: int,
        feedback: str,
        reason: Optional[str] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        사용자 피드백 저장

        Args:
            log_id: 로그 ID (v6_chatbot_logs의 log_id)
            feedback: 'positive' | 'negative'
            reason: 피드백 이유 (선택)
            comment: 추가 코멘트 (선택)

        Returns:
            성공 여부
        """
        if not self.save_to_db:
            return False

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            cur.execute("""
                UPDATE v6_chatbot_logs
                SET
                    user_feedback = %s,
                    feedback_reason = %s,
                    feedback_comment = %s,
                    feedback_timestamp = %s
                WHERE log_id = %s
                  AND username = %s
            """, (
                feedback,
                reason,
                comment,
                datetime.now(),
                log_id,
                self.username
            ))

            success = cur.rowcount > 0
            conn.commit()
            cur.close()
            conn.close()

            return success

        except Exception as e:
            print(f"피드백 저장 실패: {e}")
            return False

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """피드백 통계 조회"""
        if not self.save_to_db:
            return {}

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # 전체 피드백 통계
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE user_feedback = 'positive') as positive_count,
                    COUNT(*) FILTER (WHERE user_feedback = 'negative') as negative_count,
                    COUNT(*) FILTER (WHERE user_feedback IS NULL) as no_feedback_count,
                    COUNT(*) as total_count
                FROM v6_chatbot_logs
                WHERE username = %s
            """, (self.username,))

            result = cur.fetchone()

            # 피드백 이유별 통계 (부정적인 경우)
            cur.execute("""
                SELECT
                    feedback_reason,
                    COUNT(*) as count
                FROM v6_chatbot_logs
                WHERE username = %s
                  AND user_feedback = 'negative'
                  AND feedback_reason IS NOT NULL
                GROUP BY feedback_reason
                ORDER BY count DESC
            """, (self.username,))

            negative_reasons = {row[0]: row[1] for row in cur.fetchall()}

            cur.close()
            conn.close()

            positive_count = result[0] or 0
            negative_count = result[1] or 0
            no_feedback_count = result[2] or 0
            total_count = result[3] or 0

            satisfaction_rate = (
                round((positive_count / (positive_count + negative_count) * 100), 1)
                if (positive_count + negative_count) > 0
                else 0.0
            )

            return {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "no_feedback_count": no_feedback_count,
                "total_count": total_count,
                "satisfaction_rate": satisfaction_rate,
                "negative_reasons": negative_reasons
            }

        except Exception as e:
            print(f"피드백 통계 조회 실패: {e}")
            return {}
