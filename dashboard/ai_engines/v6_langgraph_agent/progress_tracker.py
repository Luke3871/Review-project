#//==============================================================================//#
"""
progress_tracker.py
사용자에게 실시간 진행상황 표시

last_updated: 2025.10.29
"""
#//==============================================================================//#

from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import time

from .config import NODE_ICONS, PROGRESS_CONFIG


class ProgressTracker:
    """에이전트 진행상황 추적 및 스트리밍"""

    def __init__(self, callback: Optional[Callable] = None):
        """
        Args:
            callback: 진행상황 업데이트 시 호출할 함수 (Streamlit st.empty() 등)
        """
        self.callback = callback
        self.steps = []
        self.current_step = None
        self.config = PROGRESS_CONFIG

    def start_step(
        self,
        node_name: str,
        description: str,
        substeps: Optional[List[str]] = None,
        estimated_time: Optional[float] = None
    ):
        """
        노드 시작

        Args:
            node_name: 노드 이름 (EntityParser, SQLGenerator 등)
            description: 사용자에게 표시할 설명 ("질문 분석 중...")
            substeps: 하위 단계 리스트 (옵션)
            estimated_time: 예상 실행 시간 (초)
        """
        step = {
            "node": node_name,
            "description": description,
            "status": "in_progress",
            "substeps": substeps or [],
            "completed_substeps": [],
            "start_time": time.time(),
            "estimated_time": estimated_time,
            "icon": NODE_ICONS.get(node_name, "▶️")
        }
        self.current_step = step
        self.steps.append(step)
        self._update_display()

    def update_substep(self, substep_description: str, data: Optional[Dict] = None):
        """
        하위 단계 완료 표시

        Args:
            substep_description: "브랜드: 빌리프, VT"
            data: 추가 데이터 (옵션)
        """
        if self.current_step:
            self.current_step["completed_substeps"].append({
                "description": substep_description,
                "data": data,
                "timestamp": time.time()
            })
            self._update_display()

    def complete_step(self, summary: Optional[str] = None):
        """
        현재 노드 완료

        Args:
            summary: 단계 완료 요약 메시지
        """
        if self.current_step:
            self.current_step["status"] = "completed"
            self.current_step["end_time"] = time.time()
            self.current_step["duration"] = (
                self.current_step["end_time"] - self.current_step["start_time"]
            )
            if summary:
                self.current_step["summary"] = summary
            self._update_display()
            self.current_step = None

    def error_step(self, error_msg: str, suggestion: Optional[str] = None):
        """
        현재 노드 에러

        Args:
            error_msg: 에러 메시지
            suggestion: 해결 방법 제안
        """
        if self.current_step:
            self.current_step["status"] = "error"
            self.current_step["error"] = error_msg
            self.current_step["suggestion"] = suggestion
            self.current_step["end_time"] = time.time()
            self.current_step["duration"] = (
                self.current_step["end_time"] - self.current_step["start_time"]
            )
            self._update_display()

    def _update_display(self):
        """콜백 호출하여 UI 업데이트"""
        if self.callback and self.config["enabled"]:
            self.callback(self._format_display())

    def _format_display(self) -> str:
        """사용자에게 보여줄 형식으로 포맷"""
        lines = []

        for step in self.steps:
            icon = step["icon"]
            desc = step["description"]
            status = step["status"]

            # 1. 노드 헤더
            if status == "completed":
                duration_str = f" ({step['duration']:.1f}초)" if self.config["show_timing"] else ""
                lines.append(f"{icon} {desc}{duration_str}")
            elif status == "in_progress":
                if self.config["show_timing"] and step.get("estimated_time"):
                    elapsed = time.time() - step["start_time"]
                    est = step["estimated_time"]
                    lines.append(f"{icon} {desc} (예상 {est:.1f}초)")
                else:
                    lines.append(f"{icon} {desc}")
            elif status == "error":
                lines.append(f"❌ {desc} - 오류 발생")
                lines.append(f"   {step['error']}")
                if step.get("suggestion"):
                    lines.append(f"   💡 {step['suggestion']}")

            # 2. 완료된 하위 단계
            if self.config["show_substeps"]:
                for substep in step["completed_substeps"]:
                    lines.append(f"  ✓ {substep['description']}")

            # 3. 진행 중인 하위 단계
            if status == "in_progress" and step["substeps"]:
                remaining = len(step["substeps"]) - len(step["completed_substeps"])
                if remaining > 0:
                    next_idx = len(step["completed_substeps"])
                    if next_idx < len(step["substeps"]):
                        next_substep = step["substeps"][next_idx]
                        lines.append(f"  ⏳ {next_substep}")

            lines.append("")  # 빈 줄

        return "\n".join(lines)

    def get_state_messages(self) -> List[Dict[str, Any]]:
        """
        LangGraph State에 저장할 messages 형식 반환

        Returns:
            messages 리스트
        """
        return [
            {
                "node": step["node"],
                "status": step["status"],
                "content": step["description"],
                "substeps": step.get("completed_substeps", []),
                "duration": step.get("duration"),
                "timestamp": datetime.fromtimestamp(step["start_time"]).isoformat(),
                "error": step.get("error"),
                "suggestion": step.get("suggestion")
            }
            for step in self.steps
        ]

    def get_summary(self) -> Dict[str, Any]:
        """
        전체 처리 요약 정보

        Returns:
            요약 딕셔너리
        """
        total_duration = sum(step.get("duration", 0) for step in self.steps)
        completed_count = sum(1 for step in self.steps if step["status"] == "completed")
        error_count = sum(1 for step in self.steps if step["status"] == "error")

        return {
            "total_steps": len(self.steps),
            "completed": completed_count,
            "errors": error_count,
            "total_duration": total_duration,
            "steps": [
                {
                    "node": step["node"],
                    "status": step["status"],
                    "duration": step.get("duration", 0)
                }
                for step in self.steps
            ]
        }
