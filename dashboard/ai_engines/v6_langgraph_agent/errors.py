#//==============================================================================//#
"""
errors.py
V6 LangGraph Agent 표준 에러 클래스

모든 노드에서 일관된 에러 처리를 위한 표준 에러 클래스들

last_updated: 2025.11.02
"""
#//==============================================================================//#

from typing import Dict, Optional, Any


class V6Error(Exception):
    """
    V6 Agent 기본 에러 클래스

    모든 V6 에러의 부모 클래스
    """

    def __init__(
        self,
        node: str,
        error_type: str,
        message: str,
        suggestion: Optional[str] = None,
        retry_possible: bool = False,
        original_error: Optional[Exception] = None
    ):
        self.node = node
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion or "다시 시도해주세요"
        self.retry_possible = retry_possible
        self.original_error = original_error

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """에러를 AgentState의 error 필드에 저장할 형식으로 변환"""
        return {
            "node": self.node,
            "error_type": self.error_type,
            "message": self.message,
            "suggestion": self.suggestion,
            "retry_possible": self.retry_possible,
            "auto_retry_count": 0
        }


class TimeoutError(V6Error):
    """
    타임아웃 에러 (재시도 가능)

    SQL 실행, LLM 호출 등에서 시간 초과
    """

    def __init__(self, node: str, message: str = "작업 시간 초과", original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="timeout",
            message=message,
            suggestion="쿼리를 단순화하거나 기간을 좁혀보세요",
            retry_possible=True,
            original_error=original_error
        )


class DatabaseError(V6Error):
    """
    데이터베이스 연결/실행 에러 (재시도 가능)

    PostgreSQL 연결 실패, 쿼리 실행 실패 등
    """

    def __init__(self, node: str, message: str, retry_possible: bool = True, original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="database_error",
            message=message,
            suggestion="잠시 후 다시 시도하거나 관리자에게 문의하세요",
            retry_possible=retry_possible,
            original_error=original_error
        )


class SQLGenerationError(V6Error):
    """
    SQL 생성 실패 (재시도 불가)

    LLM이 올바른 SQL을 생성하지 못함
    """

    def __init__(self, node: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="sql_generation_error",
            message=message,
            suggestion="질문을 더 구체적으로 말씀해주세요",
            retry_possible=False,
            original_error=original_error
        )


class ValidationError(V6Error):
    """
    데이터 검증 실패 (재시도 불가)

    잘못된 입력, State 불일치 등
    """

    def __init__(self, node: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="validation_error",
            message=message,
            suggestion="입력값을 확인하거나 개발팀에 문의하세요",
            retry_possible=False,
            original_error=original_error
        )


class LLMError(V6Error):
    """
    LLM 호출 실패 (재시도 가능)

    OpenAI API 오류, rate limit 등
    """

    def __init__(self, node: str, message: str, retry_possible: bool = True, original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="llm_error",
            message=message,
            suggestion="잠시 후 다시 시도해주세요",
            retry_possible=retry_possible,
            original_error=original_error
        )


class DataNotFoundError(V6Error):
    """
    데이터 없음 (재시도 불가)

    쿼리 결과가 없거나 엔티티 추출 실패
    """

    def __init__(self, node: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            node=node,
            error_type="data_not_found",
            message=message,
            suggestion="다른 브랜드나 기간으로 다시 질문해주세요",
            retry_possible=False,
            original_error=original_error
        )


# 에러 처리 유틸리티 함수
def handle_exception(node: str, e: Exception) -> Dict[str, Any]:
    """
    일반 Exception을 V6Error로 변환하여 State에 저장할 딕셔너리 반환

    Args:
        node: 에러가 발생한 노드명
        e: 발생한 예외

    Returns:
        State의 error 필드에 저장할 딕셔너리

    Example:
        ```python
        try:
            # ... 작업
        except Exception as e:
            state["error"] = handle_exception("EntityParser", e)
            return state
        ```
    """
    # 이미 V6Error면 그대로 사용
    if isinstance(e, V6Error):
        return e.to_dict()

    # psycopg2 에러 처리
    if "psycopg2" in str(type(e).__module__):
        if "timeout" in str(e).lower() or "cancel" in str(e).lower():
            return TimeoutError(node, f"쿼리 실행 시간 초과: {str(e)}", e).to_dict()
        else:
            return DatabaseError(node, f"데이터베이스 오류: {str(e)}", original_error=e).to_dict()

    # OpenAI 에러 처리
    if "openai" in str(type(e).__module__):
        return LLMError(node, f"LLM 호출 실패: {str(e)}", original_error=e).to_dict()

    # 기타 예외는 일반 V6Error로
    return V6Error(
        node=node,
        error_type="unknown_error",
        message=f"예상치 못한 오류: {str(e)}",
        suggestion="개발팀에 문의하세요",
        retry_possible=False,
        original_error=e
    ).to_dict()
