#//==============================================================================//#
"""
sql_refiner.py
SQL 오류 시 자동 수정 (Self-Correction)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
import logging
import psycopg2
import psycopg2.errors
from typing import Dict, Any, List
from openai import OpenAI

from ..state import AgentState
from ..progress_tracker import ProgressTracker
from ..config import LLM_CONFIG, DB_CONFIG
from ..errors import handle_exception, DatabaseError, SQLGenerationError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.sql_refiner")


class SQLRefiner:
    """SQL 자동 수정"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["sql_generator"]  # 0.0
        self.max_tokens = LLM_CONFIG["max_tokens"]
        self.db_config = DB_CONFIG
        self.max_retries = 3  # 최대 재시도 횟수

    def refine(self, state: AgentState) -> AgentState:
        """
        SQL 오류 검증 및 수정

        Args:
            state: 현재 상태

        Returns:
            업데이트된 상태
        """
        tracker = ProgressTracker(callback=state.get("ui_callback"))

        try:
            # 1. 실패한 쿼리만 필터링
            query_results = state.get("query_results", {}).get("results", [])
            failed_queries = [r for r in query_results if not r["success"]]

            logger.info(f"SQLRefiner 시작 - 실패 쿼리: {len(failed_queries)}개")

            if not failed_queries:
                # 실패한 쿼리 없음 - 스킵
                logger.info("실패한 쿼리 없음, 스킵")
                tracker.start_step(
                    node_name="SQLRefiner",
                    description="SQL 검증 (오류 없음 - 스킵)",
                )
                tracker.complete_step(summary="모든 쿼리 성공, 수정 불필요")
                state["messages"] = tracker.get_state_messages()
                return state

            # 2. 단계 시작
            tracker.start_step(
                node_name="SQLRefiner",
                description="SQL 오류 수정 중...",
                substeps=[f"Q{q['question_id']} 재시도" for q in failed_queries]
            )

            # 3. DB 연결
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 4. 각 실패한 쿼리 수정 시도
            refined_results = []
            for failed_query in failed_queries:
                logger.debug(f"Q{failed_query['question_id']} 수정 시도")
                refined = self._refine_single_query(
                    cursor,
                    failed_query,
                    tracker
                )
                refined_results.append(refined)
                logger.info(f"Q{failed_query['question_id']} 수정 완료 - success={refined['success']}")

            # 5. 연결 종료
            cursor.close()
            conn.close()

            # 6. 원본 결과에 수정된 쿼리 병합
            updated_results = []
            for original in query_results:
                if original["success"]:
                    updated_results.append(original)
                else:
                    # 수정된 결과로 교체
                    refined = next(
                        (r for r in refined_results if r["question_id"] == original["question_id"]),
                        original
                    )
                    updated_results.append(refined)

            success_count = sum(1 for r in updated_results if r["success"])
            logger.info(f"SQL 수정 완료: {len(failed_queries)}개 재시도, {success_count}개 성공")

            tracker.complete_step(
                summary=f"{len(failed_queries)}개 쿼리 재시도, {success_count}개 성공"
            )

            # State 업데이트
            state["query_results"]["results"] = updated_results
            state["query_results"]["refined_count"] = len(failed_queries)
            state["messages"] = tracker.get_state_messages()

            # State 검증
            try:
                errors = validate_state(state, "sql_refiner")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

        except psycopg2.OperationalError as e:
            # DB 연결 오류
            logger.error(f"DB 연결 오류: {e}", exc_info=True)

            tracker.error_step(
                error_msg=f"데이터베이스 연결 실패: {str(e)}",
                suggestion="잠시 후 다시 시도하거나 관리자에게 문의하세요"
            )

            state["error"] = DatabaseError("SQLRefiner", f"연결 실패: {str(e)}", retry_possible=True, original_error=e).to_dict()
            state["messages"] = tracker.get_state_messages()

        except Exception as e:
            logger.error(f"SQLRefiner 실패: {type(e).__name__} - {str(e)}", exc_info=True)

            tracker.error_step(
                error_msg=f"SQL 수정 오류: {str(e)}",
                suggestion="일부 쿼리를 건너뜁니다"
            )

            state["error"] = handle_exception("SQLRefiner", e)
            state["messages"] = tracker.get_state_messages()

        return state

    def _refine_single_query(
        self,
        cursor,
        failed_query: Dict[str, Any],
        tracker: ProgressTracker
    ) -> Dict[str, Any]:
        """
        단일 SQL 수정 및 재실행

        Args:
            cursor: DB 커서
            failed_query: 실패한 쿼리 정보
            tracker: 진행상황 추적

        Returns:
            수정 후 쿼리 결과
        """
        question_id = failed_query["question_id"]
        original_sql = failed_query["sql"]
        error_message = failed_query["error"]

        for attempt in range(1, self.max_retries + 1):
            try:
                # LLM으로 SQL 수정
                logger.debug(f"Q{question_id} 재시도 {attempt}회 - SQL 수정 중")
                refined_sql = self._generate_refined_sql(
                    original_sql,
                    error_message,
                    attempt
                )

                # 수정된 SQL 실행
                cursor.execute(refined_sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                data = [dict(zip(columns, row)) for row in rows]

                logger.info(f"Q{question_id} 재시도 {attempt}회 성공: {len(data)}건")
                tracker.update_substep(
                    f"Q{question_id} 재시도 {attempt}회 성공: {len(data)}건"
                )

                return {
                    "question_id": question_id,
                    "sub_question": failed_query["sub_question"],
                    "sql": refined_sql,
                    "original_sql": original_sql,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "success": True,
                    "refined": True,
                    "attempts": attempt,
                    "error": None
                }

            except psycopg2.Error as e:
                error_message = str(e)
                logger.warning(f"Q{question_id} 재시도 {attempt}회 실패: {type(e).__name__}")
                if attempt == self.max_retries:
                    logger.error(f"Q{question_id} {self.max_retries}회 시도 실패")
                    tracker.update_substep(
                        f"Q{question_id} {self.max_retries}회 시도 실패"
                    )

                    return {
                        "question_id": question_id,
                        "sub_question": failed_query["sub_question"],
                        "sql": refined_sql if 'refined_sql' in locals() else original_sql,
                        "original_sql": original_sql,
                        "data": [],
                        "columns": [],
                        "row_count": 0,
                        "success": False,
                        "refined": True,
                        "attempts": attempt,
                        "error": error_message
                    }

    def _generate_refined_sql(
        self,
        original_sql: str,
        error_message: str,
        attempt: int
    ) -> str:
        """
        LLM으로 SQL 수정

        Args:
            original_sql: 원본 SQL
            error_message: 에러 메시지
            attempt: 시도 횟수

        Returns:
            수정된 SQL
        """
        prompt = f"""당신은 PostgreSQL 오류를 수정하는 전문가입니다.
실패한 SQL 쿼리와 에러 메시지를 보고 수정된 SQL을 생성하세요.

**원본 SQL:**
```sql
{original_sql}
```

**에러 메시지:**
{error_message}

**재시도 횟수:** {attempt}

**일반적인 오류 패턴:**

1. JSONB 경로 오류:
   - 잘못: analysis->'보습력'
   - 올바름: analysis->'제품특성'->'보습력'

2. 타입 변환 오류:
   - 잘못: WHERE rating > 4
   - 올바름: WHERE CAST(rating AS FLOAT) > 4

3. 날짜 변환 오류:
   - 잘못: WHERE review_date > '2025-01-01'
   - 올바름: WHERE CAST(review_date AS DATE) > '2025-01-01'

4. 컬럼 존재하지 않음:
   - reviews 테이블에 analysis 없음
   - preprocessed_reviews 테이블에 review_text 없음

5. JSONB 배열 처리:
   - 잘못: SELECT analysis->'장점'
   - 올바름: SELECT jsonb_array_elements_text(analysis->'장점')

**수정된 SQL만 반환하세요 (설명 없이, 세미콜론 없이):**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        refined_sql = response.choices[0].message.content.strip()

        # 코드 블록 제거
        if refined_sql.startswith("```"):
            refined_sql = refined_sql.split("```")[1]
            if refined_sql.startswith("sql"):
                refined_sql = refined_sql[3:]
            refined_sql = refined_sql.strip()

        # 세미콜론 제거
        refined_sql = refined_sql.rstrip(";")

        return refined_sql
