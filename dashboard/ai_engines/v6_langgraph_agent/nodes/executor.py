#//==============================================================================//#
"""
executor.py
SQL 쿼리 실행

last_updated: 2025.11.02
"""
#//==============================================================================//#

import psycopg2
import psycopg2.errors
import logging
from typing import Dict, Any, List
import time

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import DB_CONFIG, ERROR_MESSAGES
from ..errors import handle_exception, DatabaseError, TimeoutError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.executor")


class Executor:
    """SQL 실행"""

    def __init__(self):
        self.db_config = DB_CONFIG
        self.max_retries = 3  # 재시도 횟수
        self.retry_delay = 1.0  # 재시도 대기 시간 (초)

    def execute(self, state: AgentState) -> AgentState:
        """
        SQL 실행

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            sql_queries = state.get("sql_queries", [])
            logger.info(f"Executor 시작 - SQL 쿼리 개수: {len(sql_queries)}")

            # 1. 단계 시작
            tracker.start_step(
                node_name="Executor",
                description="데이터베이스 쿼리 실행 중...",
                substeps=[f"Q{q.get('question_id', i)} 실행" for i, q in enumerate(sql_queries, 1)]
            )

            # 2. DB 연결
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 3. 각 SQL 실행
            query_results = []
            total_start_time = time.time()

            for i, sql_info in enumerate(sql_queries, 1):
                sql_preview = sql_info.get('sql', '')[:100]
                logger.debug(f"쿼리 {i} 실행 중: {sql_preview}...")

                result = self._execute_single_query_with_retry(
                    cursor,
                    sql_info,
                    tracker,
                    query_index=i
                )

                logger.info(f"쿼리 {i} 완료: {result.get('row_count', 0)} rows, success={result.get('success')}")
                query_results.append(result)

            total_duration = time.time() - total_start_time

            # 4. 연결 종료
            cursor.close()
            conn.close()

            # 5. 데이터 특성 분석
            data_characteristics = self._analyze_data_characteristics(query_results)

            tracker.complete_step(
                summary=f"{len(query_results)}개 쿼리 실행 완료 ({total_duration:.2f}초)"
            )

            # State 업데이트
            state["query_results"] = {
                "results": query_results,
                "total_queries": len(query_results),
                "total_duration": total_duration,
                "data_characteristics": data_characteristics
            }
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "executor")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
                else:
                    logger.info(f"SQL 실행 성공: {len(query_results)}개 쿼리, 총 {data_characteristics.get('total_rows', 0)}건")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except psycopg2.errors.QueryCanceled as e:
            # 타임아웃 에러 (재시도 가능)
            logger.error(f"쿼리 타임아웃: {e}", exc_info=True)

            tracker.error_step(
                error_msg="쿼리 실행 시간 초과 (30초)",
                suggestion="기간을 좁히거나 브랜드를 구체적으로 지정해보세요"
            )

            state["error"] = TimeoutError("Executor", "쿼리 실행 시간 초과 (30초)", e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except psycopg2.OperationalError as e:
            # DB 연결 오류 (재시도 가능)
            logger.error(f"DB 연결 오류: {e}", exc_info=True)

            tracker.error_step(
                error_msg=f"데이터베이스 연결 실패: {str(e)}",
                suggestion="잠시 후 다시 시도하거나 관리자에게 문의하세요"
            )

            state["error"] = DatabaseError("Executor", f"연결 실패: {str(e)}", retry_possible=True, original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except psycopg2.Error as e:
            # 기타 DB 에러
            logger.error(f"DB 에러: {type(e).__name__} - {e}", exc_info=True)

            tracker.error_step(
                error_msg=f"데이터베이스 오류: {str(e)}",
                suggestion=ERROR_MESSAGES.get("sql_error", "관리자에게 문의하세요")
            )

            state["error"] = DatabaseError("Executor", str(e), retry_possible=False, original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except Exception as e:
            # 일반 예외
            logger.error(f"Executor 실패: {type(e).__name__} - {e}", exc_info=True)

            tracker.error_step(
                error_msg=f"실행 오류: {str(e)}",
                suggestion="다시 시도해주세요"
            )

            state["error"] = handle_exception("Executor", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _execute_single_query_with_retry(
        self,
        cursor,
        sql_info: Dict[str, Any],
        tracker: ProgressTracker,
        query_index: int
    ) -> Dict[str, Any]:
        """
        단일 쿼리 실행 (재시도 포함)

        Args:
            cursor: DB cursor
            sql_info: SQL 정보
            tracker: Progress tracker
            query_index: 쿼리 인덱스

        Returns:
            실행 결과
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self._execute_single_query(cursor, sql_info, tracker)

                if result.get('success'):
                    return result
                else:
                    # 실패했지만 재시도 가능한 경우
                    if attempt < self.max_retries:
                        logger.warning(f"쿼리 {query_index} 실패 (시도 {attempt}/{self.max_retries}), 재시도 중...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error(f"쿼리 {query_index} 최종 실패 (시도 {attempt}/{self.max_retries})")
                        return result

            except psycopg2.errors.QueryCanceled:
                # 타임아웃은 재시도해도 소용없음
                raise

            except psycopg2.OperationalError as e:
                # 연결 오류는 재시도
                if attempt < self.max_retries:
                    logger.warning(f"연결 오류 발생 (시도 {attempt}/{self.max_retries}), 재시도 중...")
                    time.sleep(self.retry_delay * attempt)  # 점진적 대기
                else:
                    raise

            except Exception as e:
                # 기타 오류는 재시도 안 함
                logger.error(f"쿼리 {query_index} 실행 중 예외: {e}")
                raise

        return {"success": False, "error": "최대 재시도 횟수 초과"}

    def _execute_single_query(
        self,
        cursor,
        sql_info: Dict[str, Any],
        tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """
        단일 SQL 실행

        Args:
            cursor: DB 커서
            sql_info: SQL 정보
            tracker: 진행상황 추적

        Returns:
            쿼리 결과
        """
        question_id = sql_info["question_id"]
        sql = sql_info["sql"]

        start_time = time.time()

        try:
            # SQL 실행
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            duration = time.time() - start_time

            # 딕셔너리 리스트로 변환
            data = [dict(zip(columns, row)) for row in rows]

            tracker.update_substep(
                f"Q{question_id} 완료: {len(data)}건 ({duration:.2f}초)"
            )

            return {
                "question_id": question_id,
                "sub_question": sql_info["sub_question"],
                "sql": sql,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "duration": duration,
                "success": True,
                "error": None
            }

        except psycopg2.Error as e:
            duration = time.time() - start_time

            tracker.update_substep(
                f"Q{question_id} 오류: {str(e)[:50]}..."
            )

            return {
                "question_id": question_id,
                "sub_question": sql_info["sub_question"],
                "sql": sql,
                "data": [],
                "columns": [],
                "row_count": 0,
                "duration": duration,
                "success": False,
                "error": str(e)
            }

    def _analyze_data_characteristics(
        self,
        query_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        쿼리 결과 데이터 특성 분석 (ResponsePlanner용)

        Args:
            query_results: 쿼리 결과 리스트

        Returns:
            데이터 특성
        """
        total_rows = sum(r["row_count"] for r in query_results)
        successful_queries = sum(1 for r in query_results if r["success"])

        # 시계열 데이터 감지 (month, date 등 컬럼 존재)
        has_time_series = any(
            any(col in ["month", "date", "period", "year"] for col in r["columns"])
            for r in query_results if r["success"]
        )

        # 여러 엔티티 비교 감지 (brand, product 등으로 그룹화)
        has_multi_entity = any(
            any(col in ["brand", "product_name", "channel"] for col in r["columns"])
            for r in query_results if r["success"]
        ) and len(query_results) > 1

        # 분포 데이터 감지 (count, percentage 등)
        has_distribution = any(
            any(col in ["count", "percentage", "ratio"] for col in r["columns"])
            for r in query_results if r["success"]
        )

        # 키워드 데이터 감지
        keyword_count = 0
        for r in query_results:
            if r["success"] and any(col in ["keyword", "advantage", "disadvantage"] for col in r["columns"]):
                keyword_count = max(keyword_count, r["row_count"])

        return {
            "total_rows": total_rows,
            "successful_queries": successful_queries,
            "failed_queries": len(query_results) - successful_queries,
            "time_series": has_time_series,
            "multi_entity": has_multi_entity,
            "has_distribution": has_distribution,
            "keyword_count": keyword_count
        }
