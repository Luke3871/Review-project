#//==============================================================================//#
"""
executor.py
SQL 쿼리 실행

last_updated: 2025.11.02
"""
#//==============================================================================//#

import psycopg2
from typing import Dict, Any, List
import time

import sys
from pathlib import Path

# V7 config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_CONFIG


class Executor:
    """SQL 실행"""

    def __init__(self):
        self.db_config = DB_CONFIG

    def _execute_queries(
        self,
        sql_queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        SQL 쿼리 리스트 실행

        Args:
            sql_queries: generate_sql Tool의 출력 (1개 또는 2개)

        Returns:
            쿼리 실행 결과
        """
        # DB 연결
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # 각 SQL 실행
        query_results = []
        total_start_time = time.time()

        for i, sql_info in enumerate(sql_queries, 1):
            result = self._execute_single_query(cursor, sql_info, i)
            query_results.append(result)

        total_duration = time.time() - total_start_time

        # 연결 종료
        cursor.close()
        conn.close()

        # 데이터 특성 분석
        data_characteristics = self._analyze_data_characteristics(query_results)

        return {
            "results": query_results,
            "total_queries": len(query_results),
            "total_duration": total_duration,
            "data_characteristics": data_characteristics
        }

    def _execute_single_query(
        self,
        cursor,
        sql_info: Dict[str, Any],
        query_index: int
    ) -> Dict[str, Any]:
        """
        단일 SQL 실행

        Args:
            cursor: DB 커서
            sql_info: SQL 정보
            query_index: 쿼리 인덱스 (1부터 시작)

        Returns:
            쿼리 결과
        """
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

            return {
                "query_index": query_index,
                "sql": sql,
                "purpose": sql_info.get("purpose", ""),
                "table_name": sql_info.get("table_name"),  # data_scope="both" 시 구분용
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "duration": duration,
                "success": True,
                "error": None
            }

        except psycopg2.Error as e:
            duration = time.time() - start_time

            return {
                "query_index": query_index,
                "sql": sql,
                "purpose": sql_info.get("purpose", ""),
                "table_name": sql_info.get("table_name"),
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
        쿼리 결과 데이터 특성 분석 (시각화 판단용)

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
        )

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
