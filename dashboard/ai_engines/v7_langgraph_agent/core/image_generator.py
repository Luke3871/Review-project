#//==============================================================================//#
"""
image_generator.py
데이터 시각화 이미지 생성

쿼리 결과를 기반으로 차트 이미지 생성 (matplotlib)

last_updated: 2025.11.02
"""
#//==============================================================================//#

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import platform

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LLM_CONFIG


class ImageGenerator:
    """데이터 시각화 이미지 생성"""

    def __init__(self):
        # 한글 폰트 설정
        self._setup_korean_font()

        # 이미지 저장 경로
        project_root = Path(__file__).resolve().parents[4]
        self.output_dir = project_root / "dashboard" / "generated_images" / "v7_charts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _setup_korean_font(self):
        """
        한글 폰트 설정 (OS별)
        """
        system = platform.system()

        if system == "Windows":
            plt.rc('font', family='Malgun Gothic')
        elif system == "Darwin":  # macOS
            plt.rc('font', family='AppleGothic')
        else:  # Linux
            plt.rc('font', family='NanumGothic')

        # 마이너스 기호 깨짐 방지
        plt.rcParams['axes.unicode_minus'] = False

    def generate_images(
        self,
        query_results: Dict[str, Any],
        user_query: str
    ) -> List[str]:
        """
        쿼리 결과에 적합한 차트 이미지 생성

        Args:
            query_results: execute_sql의 출력
            user_query: 사용자 질문 (파일명에 사용)

        Returns:
            생성된 이미지 경로 리스트
        """
        image_paths = []
        data_chars = query_results.get("data_characteristics", {})
        results = query_results.get("results", [])

        # 시계열 데이터 → 라인 차트
        if data_chars.get("time_series"):
            path = self._create_line_chart(results, user_query)
            if path:
                image_paths.append(path)

        # 비교 데이터 → 바 차트
        if data_chars.get("multi_entity"):
            path = self._create_bar_chart(results, user_query)
            if path:
                image_paths.append(path)

        # 키워드 데이터는 차트로 안 만들고 워드클라우드가 필요하면 추후 추가

        return image_paths

    def _create_line_chart(
        self,
        results: List[Dict[str, Any]],
        user_query: str
    ) -> str:
        """
        시계열 라인 차트 생성

        Args:
            results: 쿼리 결과 리스트
            user_query: 사용자 질문

        Returns:
            이미지 파일 경로
        """
        # 첫 번째 성공한 결과 사용
        for result in results:
            if not result.get("success"):
                continue

            data = result.get("data", [])
            if not data:
                continue

            # 데이터 추출 (month/date + metric)
            x_data = []
            y_data = []

            for row in data:
                # x축: month, date, period 등
                x_val = row.get("month") or row.get("date") or row.get("period")
                if not x_val:
                    continue

                # y축: 숫자 값 찾기 (avg_rating, review_count 등)
                y_val = None
                for key, value in row.items():
                    if key in ["month", "date", "period", "brand", "product_name"]:
                        continue
                    if isinstance(value, (int, float)):
                        y_val = value
                        break

                if y_val is not None:
                    x_data.append(str(x_val))
                    y_data.append(y_val)

            if not x_data or not y_data:
                continue

            # 차트 생성
            plt.figure(figsize=(10, 6))
            plt.plot(x_data, y_data, marker='o', linewidth=2, markersize=8)

            # 레이블
            plt.xlabel("기간", fontsize=12)
            plt.ylabel("값", fontsize=12)
            plt.title(f"{user_query} - 시계열 추이", fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            # 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"line_chart_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            return str(filepath)

        return None

    def _create_bar_chart(
        self,
        results: List[Dict[str, Any]],
        user_query: str
    ) -> str:
        """
        비교 바 차트 생성

        Args:
            results: 쿼리 결과 리스트
            user_query: 사용자 질문

        Returns:
            이미지 파일 경로
        """
        # 첫 번째 성공한 결과 사용
        for result in results:
            if not result.get("success"):
                continue

            data = result.get("data", [])
            if not data:
                continue

            # 데이터 추출 (brand/product + metric)
            labels = []
            values = []

            for row in data:
                # label: brand, product_name 등
                label = row.get("brand") or row.get("product_name")
                if not label:
                    continue

                # value: 숫자 값 찾기
                value = None
                for key, val in row.items():
                    if key in ["brand", "product_name", "channel"]:
                        continue
                    if isinstance(val, (int, float)):
                        value = val
                        break

                if value is not None:
                    labels.append(label)
                    values.append(value)

            if not labels or not values:
                continue

            # 차트 생성
            plt.figure(figsize=(10, 6))
            plt.bar(labels, values, color='steelblue', alpha=0.8)

            # 레이블
            plt.xlabel("구분", fontsize=12)
            plt.ylabel("값", fontsize=12)
            plt.title(f"{user_query} - 비교 분석", fontsize=14, fontweight='bold')
            plt.grid(True, axis='y', alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bar_chart_{timestamp}.png"
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

            return str(filepath)

        return None
