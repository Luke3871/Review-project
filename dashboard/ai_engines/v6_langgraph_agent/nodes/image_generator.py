#//==============================================================================//#
"""
image_generator.py
AI Visual Agent - 이미지 생성 노드

Gemini 2.5 Flash를 사용하여 Daiso 채널 최적화 디자인 이미지 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types

from ..state import AgentState
from ..errors import handle_exception, LLMError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.image_generator")

class ImageGenerator:
    """이미지 생성 노드 - Gemini 2.5 Flash"""

    def __init__(self):
        # Initialize Gemini client
        # Try multiple sources: env vars, streamlit secrets, or raise error
        api_key = None

        # 1. Try environment variables
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        # 2. Try Streamlit secrets
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
            except:
                pass

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables or Streamlit secrets")

        self.client = genai.Client(api_key=api_key)

        # 이미지 저장 경로 설정
        project_root = Path(__file__).resolve().parents[4]
        self.output_dir = project_root / "dashboard" / "generated_images" / "daiso"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 패키징 옵션 정의 (테스트베드용 3가지 버전)
        self.packaging_options = [
            {
                "type": "7-day_sachet_pouch",
                "name": "일주일치 샤쉐 파우치",
                "description": "7 individual sachets (1ml each) in a cute illustrated pouch packaging",
                "size": "7ml total (1ml x 7 sachets)",
                "format": "Flat pouch with 7 tearable sachets inside"
            },
            {
                "type": "3-day_trial_kit",
                "name": "3일 트라이얼 키트",
                "description": "3 mini tubes in a compact cardboard box set",
                "size": "3ml x 3 tubes (9ml total)",
                "format": "Small cardboard box containing 3 mini tubes"
            },
            {
                "type": "mini_bottle",
                "name": "10ml 미니 보틀",
                "description": "Single portable mini bottle with flip-cap or dropper",
                "size": "10ml bottle",
                "format": "Mini version of original bottle packaging"
            }
        ]

    def generate(self, state: AgentState) -> AgentState:
        """
        Gemini 2.5 Flash로 이미지 생성 (Image-to-Image 변환)
        3가지 패키징 옵션으로 각각 생성

        Args:
            state: 에이전트 상태 (design_prompt, source_product_image 포함)

        Returns:
            state: 생성된 이미지 정보 업데이트
        """
        try:
            logger.info("ImageGenerator 시작")

            base_prompt = state.get("design_prompt")
            source_image = state.get("source_product_image")

            logger.debug(f"design_prompt: {base_prompt[:100] if base_prompt else 'None'}...")
            logger.debug(f"source_image: {source_image}")

            if not base_prompt:
                error_msg = "디자인 프롬프트가 없습니다."
                logger.error(error_msg)
                state["error"] = {
                    "node": "ImageGenerator",
                    "message": error_msg
                }
                return state

            if not source_image:
                error_msg = "원본 제품 이미지가 없습니다."
                logger.error(error_msg)
                state["error"] = {
                    "node": "ImageGenerator",
                    "message": error_msg
                }
                return state

            # 이미지 로드
            source_pil_image = Image.open(source_image)

            # 생성된 이미지 정보
            generated_images = []

            # 3가지 패키징 옵션으로 각각 생성
            for idx, packaging in enumerate(self.packaging_options):
                logger.info(f"패키징 옵션 {idx+1}/3 생성 중: {packaging['name']}")

                # UI 업데이트
                if state.get("ui_callback"):
                    state["ui_callback"]({
                        "node": "ImageGenerator",
                        "status": "running",
                        "message": f"옵션 {idx+1}/3 생성 중: {packaging['name']}"
                    })

                # 패키징 타입별 프롬프트 생성
                packaging_prompt = self._create_packaging_prompt(base_prompt, packaging)

                # Gemini 2.5 Flash Image (Nano Banana) API 호출
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[source_pil_image, packaging_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="1:1",
                        )
                    )
                )

                # Extract image from response
                for part in response.candidates[0].content.parts:
                    if part.inline_data is not None:
                        # Get image bytes and convert to PIL Image
                        image_bytes = part.inline_data.data
                        image = Image.open(BytesIO(image_bytes))

                        # 로컬에 저장
                        local_path = self._save_image(
                            image=image,
                            packaging_type=packaging["type"],
                            index=idx
                        )

                        logger.info(f"이미지 저장 완료: {local_path}")

                        generated_images.append({
                            "url": None,
                            "local_path": str(local_path),
                            "packaging_type": packaging["type"],
                            "packaging_name": packaging["name"],
                            "packaging_description": packaging["description"],
                            "packaging_size": packaging["size"],
                            "revised_prompt": packaging_prompt,
                            "timestamp": datetime.now().isoformat(),
                            "model": "gemini-2.5-flash-image (Nano Banana)"
                        })

            state["generated_images"] = generated_images

            logger.info(f"이미지 생성 완료: {len(generated_images)}개")

            # UI 업데이트
            if state.get("ui_callback"):
                state["ui_callback"]({
                    "node": "ImageGenerator",
                    "status": "completed",
                    "message": f"이미지 생성 완료 ({len(generated_images)}개 패키징 옵션)"
                })

            # State 검증
            try:
                errors = validate_state(state, "image_generator")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

            return state

        except Exception as e:
            logger.error(f"ImageGenerator 실패: {type(e).__name__} - {str(e)}", exc_info=True)
            state["error"] = handle_exception("ImageGenerator", e)
            return state

    def _create_packaging_prompt(self, base_prompt: str, packaging: Dict[str, str]) -> str:
        """
        패키징 타입별 프롬프트 생성

        Args:
            base_prompt: 기본 프롬프트
            packaging: 패키징 옵션 정보

        Returns:
            패키징 타입이 반영된 프롬프트
        """
        # 기존 프롬프트에서 TRANSFORMATION REQUIREMENTS 부분을 찾아서 패키징 정보 삽입
        packaging_instruction = f"""
PACKAGING FORMAT (IMPORTANT):
- Type: {packaging['description']}
- Size: {packaging['size']}
- Format: {packaging['format']}
- Create packaging design that clearly shows this specific format
"""

        # 기존 프롬프트의 TRANSFORMATION REQUIREMENTS 앞에 패키징 정보 삽입
        if "TRANSFORMATION REQUIREMENTS:" in base_prompt:
            parts = base_prompt.split("TRANSFORMATION REQUIREMENTS:")
            enhanced_prompt = parts[0] + packaging_instruction + "\nTRANSFORMATION REQUIREMENTS:" + parts[1]
        else:
            # TRANSFORMATION REQUIREMENTS가 없으면 마지막에 추가
            enhanced_prompt = base_prompt + "\n" + packaging_instruction

        return enhanced_prompt

    def _save_image(self, image: Image.Image, packaging_type: str, index: int = 0) -> Path:
        """
        생성된 이미지를 로컬에 저장

        Args:
            image: PIL Image 객체
            packaging_type: 패키징 타입 (파일명에 포함)
            index: 이미지 인덱스

        Returns:
            저장된 파일 경로
        """
        # 타임스탬프 기반 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"daiso_{packaging_type}_{timestamp}.png"
        file_path = self.output_dir / filename

        # 이미지 저장
        image.save(file_path, format='PNG')

        logger.debug(f"이미지 저장: {file_path}")
        return file_path
