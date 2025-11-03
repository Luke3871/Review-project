#//==============================================================================//#
"""
image_prompt_generator.py
AI Visual Agent - 이미지 프롬프트 생성 노드

Daiso 채널 최적화 디자인 프롬프트 생성:
1. 올리브영 제품 이미지 찾기 (DB 기반)
2. 올리브영 제품 리뷰 키워드 추출 (preprocessed_reviews)
3. Daiso 채널 리뷰 키워드 추출 (preprocessed_reviews)
4. GPT-4o로 Daiso 채널 특성 요약
5. Gemini (Nano Banana) 이미지 변환 프롬프트 생성

Image-to-Image Transformation:
- 올리브영 제품 이미지를 Gemini에 직접 전달
- 데이터 기반 채널 특성으로 변환 지침 생성
- 하드코딩 제거, 동적 프롬프트 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI

from ..state import AgentState
from ..config import DB_CONFIG, LLM_CONFIG
from ..errors import handle_exception, DatabaseError, LLMError
from ..state_validator import validate_state

# 로거 설정
logger = logging.getLogger("v6_agent.image_prompt_generator")

class ImagePromptGenerator:
    """이미지 프롬프트 생성 노드"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # 브랜드 시그니처 디자인 파일 로드
        self.brand_signatures = self._load_brand_signatures()

    def generate(self, state: AgentState) -> AgentState:
        """
        이미지 프롬프트 생성

        워크플로우:
        1. 올리브영 제품 이미지 찾기
        2. 올리브영 제품 리뷰 키워드 추출
        3. Daiso 채널 리뷰 키워드 추출 및 특성 요약
        4. Gemini 이미지 변환 프롬프트 생성
        """
        try:
            logger.info("ImagePromptGenerator 시작")

            # 1. 엔티티 추출
            entities = state.get("parsed_entities", {})
            brands = entities.get("brands", [])
            products = entities.get("products", [])

            logger.debug(f"brands: {brands}, products: {products}")

            if not brands and not products:
                error_msg = "브랜드나 제품명을 찾을 수 없습니다."
                logger.error(error_msg)
                state["error"] = {
                    "node": "ImagePromptGenerator",
                    "message": error_msg
                }
                return state

            # 2. 올리브영 제품 이미지 찾기
            image_path = self._find_oliveyoung_image(brands, products)
            if not image_path:
                error_msg = "올리브영 제품 이미지를 찾을 수 없습니다."
                logger.error(error_msg)
                state["error"] = {
                    "node": "ImagePromptGenerator",
                    "message": error_msg
                }
                return state

            logger.info(f"제품 이미지 발견: {image_path}")
            state["source_product_image"] = image_path

            # 3. 올리브영 제품 리뷰 키워드 추출
            oy_keywords = self._extract_keywords_from_reviews(brands, products)
            state["design_keywords"] = oy_keywords
            logger.debug(f"OY 키워드: {oy_keywords[:5]}")

            # 4. Daiso 채널 키워드 추출 및 특성 요약
            daiso_keywords = self._extract_daiso_channel_keywords()
            daiso_summary = self._summarize_daiso_channel(daiso_keywords)
            state["daiso_channel_summary"] = daiso_summary
            logger.debug(f"Daiso 키워드: {daiso_keywords[:5]}")

            # 5. 한글 키워드를 영어로 번역 (Gemini 이미지 내 한글 깨짐 방지)
            oy_keywords_en = self._translate_keywords_to_english(oy_keywords)
            logger.debug(f"영어 번역된 키워드: {oy_keywords_en[:5]}")

            # 6. Gemini 이미지 변환 프롬프트 생성 (간소화)
            design_prompt = self._generate_gemini_prompt(
                oy_keywords=oy_keywords_en,  # 영어 번역된 키워드 사용
                daiso_summary=daiso_summary,
                brand=" ".join(brands) if brands else "",
                product=" ".join(products) if products else ""
            )
            state["design_prompt"] = design_prompt

            logger.info(f"이미지 프롬프트 생성 완료: OY {len(oy_keywords)}개, Daiso {len(daiso_keywords)}개 키워드")

            # 진행상황 업데이트
            if state.get("ui_callback"):
                state["ui_callback"]({
                    "node": "ImagePromptGenerator",
                    "status": "completed",
                    "message": f"디자인 프롬프트 생성 완료 (OY 키워드: {len(oy_keywords)}개, Daiso 키워드: {len(daiso_keywords)}개)"
                })

            # State 검증
            try:
                errors = validate_state(state, "image_prompt_generator")
                if errors:
                    logger.error(f"State 검증 실패: {errors}")
            except Exception as validation_error:
                logger.warning(f"검증 중 예외: {validation_error}")

            return state

        except psycopg2.Error as e:
            logger.error(f"DB 오류: {type(e).__name__} - {str(e)}", exc_info=True)
            state["error"] = DatabaseError("ImagePromptGenerator", f"DB 오류: {str(e)}", original_error=e).to_dict()
            return state

        except Exception as e:
            logger.error(f"ImagePromptGenerator 실패: {type(e).__name__} - {str(e)}", exc_info=True)
            state["error"] = handle_exception("ImagePromptGenerator", e)
            return state

    def _find_oliveyoung_image(self, brands: List[str], products: List[str]) -> Optional[str]:
        """
        올리브영 제품 이미지 찾기
        - DB에서 brand/product 조회
        - ranking 기준으로 이미지 경로 매칭
        """
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 브랜드+제품명으로 검색
            query = """
                SELECT product_name, category, ranking
                FROM reviews
                WHERE channel = 'OliveYoung'
            """

            conditions = []
            if brands:
                brand_conditions = " OR ".join([f"brand ILIKE '%{b}%'" for b in brands])
                conditions.append(f"({brand_conditions})")
            if products:
                product_conditions = " OR ".join([f"product_name ILIKE '%{p}%'" for p in products])
                conditions.append(f"({product_conditions})")

            if conditions:
                query += " AND (" + " AND ".join(conditions) + ")"

            query += " AND ranking IS NOT NULL ORDER BY CAST(ranking AS INTEGER) LIMIT 1"

            cur.execute(query)
            result = cur.fetchone()

            if not result:
                return None

            # 이미지 경로 생성
            category = result['category']
            ranking = result['ranking']

            # 프로젝트 루트 기준 경로
            project_root = Path(__file__).resolve().parents[4]
            image_path = project_root / "data" / "data_oliveyoung" / "raw_data" / "reviews_image_oliveyoung" / f"oliveyoung_{category}_{int(ranking):03d}_product_main.jpg"

            if image_path.exists():
                return str(image_path)

            return None

        except Exception as e:
            logger.error(f"올리브영 이미지 검색 오류: {e}", exc_info=True)
            return None
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()


    def _extract_keywords_from_reviews(self, brands: List[str], products: List[str]) -> List[str]:
        """
        올리브영 제품 리뷰에서 키워드 추출 (TF-IDF 기반)
        preprocessed_reviews의 키워드 필드 활용
        """
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # 브랜드+제품으로 리뷰 검색
            query = """
                SELECT analysis->'키워드' as keywords
                FROM preprocessed_reviews
                WHERE channel = 'OliveYoung'
            """

            conditions = []
            if brands:
                brand_conditions = " OR ".join([f"brand ILIKE '%{b}%'" for b in brands])
                conditions.append(f"({brand_conditions})")
            if products:
                product_conditions = " OR ".join([f"product_name ILIKE '%{p}%'" for p in products])
                conditions.append(f"({product_conditions})")

            if conditions:
                query += " AND (" + " AND ".join(conditions) + ")"

            query += " LIMIT 50"  # 상위 50개 리뷰

            cur.execute(query)
            results = cur.fetchall()

            # 키워드 집계
            keyword_freq = {}
            for row in results:
                keywords = row.get('keywords')
                if keywords:
                    # JSONB array를 Python list로 변환
                    if isinstance(keywords, list):
                        for kw in keywords:
                            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

            # 빈도순 정렬
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)

            # 상위 10개 키워드 반환
            return [kw for kw, freq in sorted_keywords[:10]]

        except Exception as e:
            logger.error(f"키워드 추출 오류: {e}", exc_info=True)
            return ["보습", "진정", "효과"]  # 기본 키워드
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _extract_daiso_channel_keywords(self) -> List[str]:
        """
        Daiso 채널 제품 리뷰에서 키워드 추출
        실제 Daiso 리뷰 데이터 기반으로 채널 특성 파악
        """
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Daiso 채널 뷰티 제품 리뷰 조회
            query = """
                SELECT analysis->'키워드' as keywords
                FROM preprocessed_reviews
                WHERE channel = 'Daiso'
                LIMIT 100
            """

            cur.execute(query)
            results = cur.fetchall()

            # 키워드 집계
            keyword_freq = {}
            for row in results:
                keywords = row.get('keywords')
                if keywords:
                    if isinstance(keywords, list):
                        for kw in keywords:
                            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

            # 빈도순 정렬
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)

            # 상위 15개 키워드 반환
            return [kw for kw, freq in sorted_keywords[:15]]

        except Exception as e:
            logger.error(f"Daiso 키워드 추출 오류: {e}", exc_info=True)
            return ["가성비", "귀엽다", "미니", "휴대", "저렴"]  # 기본 키워드
        finally:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()

    def _summarize_daiso_channel(self, daiso_keywords: List[str]) -> str:
        """
        GPT-4o로 Daiso 채널 특성 요약
        리뷰 키워드를 바탕으로 채널 디자인 가이드 생성
        """
        try:
            keywords_text = ", ".join(daiso_keywords)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a design strategist analyzing channel characteristics from customer review keywords."
                    },
                    {
                        "role": "user",
                        "content": f"""Based on these Daiso channel review keywords, summarize the design characteristics:

Keywords: {keywords_text}

Provide a concise summary (2-3 sentences) covering:
- Visual style preferences
- Product format/size preferences
- Price/value positioning

Output in English, focusing on actionable design guidance."""
                    }
                ],
                temperature=0.3,
                max_tokens=150
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Daiso 채널 요약 오류: {e}", exc_info=True)
            return "Affordable, cute, portable mini-size products. Value-focused with playful, approachable design."

    def _translate_keywords_to_english(self, keywords: List[str]) -> List[str]:
        """
        한글 키워드를 영어로 번역 (GPT-4o 사용)
        Gemini 이미지 생성 시 한글 폰트 깨짐 방지
        """
        if not keywords:
            return []

        try:
            keywords_text = ", ".join(keywords)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator specializing in cosmetics and skincare terminology."
                    },
                    {
                        "role": "user",
                        "content": f"""Translate these Korean skincare/cosmetics keywords to English.
Provide ONLY the translated keywords separated by commas, no explanations.

Korean keywords: {keywords_text}

Format: keyword1, keyword2, keyword3"""
                    }
                ],
                temperature=0.2,
                max_tokens=100
            )

            # Parse response and return as list
            translated_text = response.choices[0].message.content.strip()
            translated_keywords = [kw.strip() for kw in translated_text.split(",")]

            return translated_keywords[:len(keywords)]  # Match original length

        except Exception as e:
            logger.error(f"키워드 번역 오류: {e}", exc_info=True)
            # Fallback: return generic English keywords
            return ["moisturizing", "soothing", "effective"][:len(keywords)]

    def _load_brand_signatures(self) -> Dict[str, Dict[str, str]]:
        """
        브랜드 시그니처 디자인 파일 로드

        Returns:
            브랜드별 시그니처 정보 딕셔너리
        """
        try:
            project_root = Path(__file__).resolve().parents[1]
            signature_file = project_root / "brand_signature_designs.txt"

            brand_signatures = {}

            if not signature_file.exists():
                return brand_signatures

            current_brand = None
            with open(signature_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    # Brand header [brand_name]
                    if line.startswith('[') and line.endswith(']'):
                        current_brand = line[1:-1].lower()
                        brand_signatures[current_brand] = {}
                        continue

                    # Key-value pairs
                    if current_brand and ':' in line:
                        key, value = line.split(':', 1)
                        brand_signatures[current_brand][key.strip()] = value.strip()

            return brand_signatures

        except Exception as e:
            logger.error(f"브랜드 시그니처 로드 오류: {e}", exc_info=True)
            return {}

    def _generate_gemini_prompt(self,
                                oy_keywords: List[str],
                                daiso_summary: str,
                                brand: str = "",
                                product: str = "") -> str:
        """
        Gemini (Nano Banana) 이미지 변환 프롬프트 생성
        - 올리브영 제품 리뷰 키워드 (영어 번역됨)
        - Daiso 채널 특성 요약
        - 브랜드 시그니처 디자인 요소 (있는 경우)
        """
        # 올리브영 제품 키워드 정리 (이미 영어로 번역된 상태)
        oy_keyword_text = ", ".join(oy_keywords[:5]) if oy_keywords else "moisturizing, soothing"

        # 브랜드 시그니처 디자인 요소 추출
        brand_signature_section = ""
        if brand:
            brand_lower = brand.lower().strip()
            if brand_lower in self.brand_signatures:
                signature = self.brand_signatures[brand_lower]
                brand_signature_section = "\nBRAND SIGNATURE DESIGN (MUST PRESERVE - CRITICAL):\n"

                if 'signature_cap' in signature:
                    brand_signature_section += f"- Signature cap: {signature['signature_cap']}\n"
                    brand_signature_section += "- IMPORTANT: Even in sachet pouch or trial kit format, the top closure/seal should reference this signature cap design\n"

                if 'colors' in signature:
                    brand_signature_section += f"- Brand colors: {signature['colors']}\n"

                if 'key_elements' in signature:
                    brand_signature_section += f"- Key visual elements: {signature['key_elements']}\n"

                brand_signature_section += "- These signature elements define the brand identity - DO NOT remove them\n"

        # 간소화된 이미지 변환 프롬프트
        prompt = f"""Transform this premium OliveYoung product packaging into a budget-friendly Daiso channel version.

IMAGE INPUT INSTRUCTIONS:
- Focus ONLY on the product packaging/container design itself
- Ignore any channel emblems, promotional badges, stickers, or overlay graphics
- Ignore character illustrations, collaboration IPs, or animated graphics
- Reference only the product bottle/tube/jar and its label design
{brand_signature_section}
PRODUCT INFO:
- Brand: {brand if brand else "Korean cosmetics"}
- Product: {product if product else "skincare"}
- Key benefits (from OliveYoung reviews): {oy_keyword_text}

DAISO CHANNEL CHARACTERISTICS (from customer reviews):
{daiso_summary}

TRANSFORMATION REQUIREMENTS:
1. Maintain brand recognition and key ingredient highlights
2. REDUCE SIZE: Transform to mini/travel size (10-15ml typical, compact and portable)
3. Adapt visual style to match Daiso channel characteristics above
4. Consider 5000 KRW price point positioning
5. Avoid cannibalization: Create a distinct "budget-friendly test version" appeal

TEXT RENDERING:
- Use ONLY English text on product labels and packaging
- Replace any Korean characters with English translations
- Ensure all text is clearly readable in Latin alphabet

OUTPUT FORMAT:
Professional product photography on white background, front view, studio lighting.

IMPORTANT CONSTRAINTS:
- DO NOT add any price tags, price stickers, or promotional badges
- DO NOT add "5000원" or price information as visual elements
- DO NOT use Korean characters (Hangul) anywhere in the generated image
- Focus purely on the product packaging design itself"""

        return prompt
