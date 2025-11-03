#//==============================================================================//#
"""
query_handler.py
사용자 질문 분석

LLM을 사용하여 질문을 구조화
- 브랜드 추출
- 키워드 추출
- 쿼리 타입 판단
- 채널 추론

last_updated: 2025.01.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import json
from typing import Dict, List, Optional
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#//==============================================================================//#
# QueryHandler
#//==============================================================================//#

class QueryHandler:
    """
    사용자 질문 분석
    
    LLM 기반 구조화
    """
    
    def __init__(
        self,
        api_key: str,
        db_config: Dict,
        model: str = "gpt-4o-mini"
    ):
        """
        초기화
        
        Args:
            api_key: OpenAI API Key
            db_config: DB 설정
            model: 사용할 LLM 모델
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.db_config = db_config
        
        # ABSA 속성 로드 (재사용)
        self.aspects = self._load_aspects()
        
        # DB에서 브랜드 목록 로드
        self.brands = self._load_brands_from_db()
        
        logger.info(f"QueryHandler initialized with {len(self.brands)} brands")
    
    def _load_aspects(self) -> Dict:
        """
        ABSA 속성 로드
        
        Returns:
            카테고리별 속성 사전
        """
        
        try:
            from core_v2.sentiment_analysis import get_aspects_by_category
            
            aspects = {
                'skincare': get_aspects_by_category('skincare'),
                'makeup': get_aspects_by_category('makeup')
            }
            
            logger.info(f"Loaded aspects for {len(aspects)} categories")
            return aspects
            
        except Exception as e:
            logger.error(f"Failed to load aspects: {e}")
            
            # Fallback
            return {
                'skincare': {
                    '보습': ['촉촉', '수분'],
                    '흡수': ['흡수', '스며듦'],
                    '향': ['향', '냄새'],
                    '발림성': ['발림', '텍스처'],
                    '끈적임': ['끈적', '답답']
                }
            }
    
    def _load_brands_from_db(self) -> List[str]:
        """
        DB에서 브랜드 목록 로드
        
        Returns:
            브랜드 리스트
        """
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            query = "SELECT DISTINCT brand FROM reviews WHERE brand IS NOT NULL"
            cur.execute(query)
            
            brands = [row[0] for row in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            logger.info(f"Loaded {len(brands)} brands from DB")
            return brands
            
        except Exception as e:
            logger.error(f"Failed to load brands from DB: {e}")
            
            # Fallback: 하드코딩
            return [
                'VT', '라운드랩', 'CNP', '코스알엑스', '토리든',
                '메디힐', '닥터지', '달바', '아누아', '롬앤'
            ]
    
    def handle(self, query: str) -> Dict:
        """
        질문 분석 메인 함수
        
        Args:
            query: 사용자 질문
        
        Returns:
            구조화된 정보 Dict
        """
        
        logger.info(f"Handling query: {query}")
        
        # LLM으로 파싱
        parsed = self._llm_parse(query)
        
        # DB에서 추가 정보 보강
        self._enrich_with_db(parsed)
        
        logger.info(f"Query parsed: {parsed['query_type']}")
        
        return parsed
    
    def _llm_parse(self, query: str) -> Dict:
        """
        LLM을 사용한 질문 파싱
        
        Args:
            query: 사용자 질문
        
        Returns:
            파싱된 정보
        """
        
        # 프롬프트 생성
        prompt = self._create_parse_prompt(query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "화장품 리뷰 분석 전문가. JSON만 반환."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 원본 쿼리 추가
            result['original_query'] = query
            
            return result
            
        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            
            # Fallback
            return self._create_fallback_result(query)
    
    def _create_parse_prompt(self, query: str) -> str:
        """
        LLM 파싱 프롬프트 생성
        
        Args:
            query: 사용자 질문
        
        Returns:
            프롬프트 문자열
        """
        
        # 브랜드 목록 (상위 20개만)
        brands_str = ', '.join(self.brands[:20])
        
        # 속성 목록
        aspects_str = ', '.join(self.aspects.get('skincare', {}).keys())
        
        # 채널 목록
        channels = ['OliveYoung', 'Daiso', 'etc']
        channels_str = ', '.join(channels)
        
        prompt = f"""다음 화장품 리뷰 질문을 분석하여 JSON으로 반환하세요.

질문: "{query}"

분석 항목:
1. brands: 언급된 브랜드 리스트 (있으면)
   - 가능한 브랜드: {brands_str}
   
2. keywords: 언급된 키워드들
   
3. aspects: 분석 대상 속성 (있으면)
   - 가능한 속성: {aspects_str}
   
4. query_type: 쿼리 타입 (하나만 선택)
   - aspect_analysis: 특정 속성 분석
   - comparison_analysis: 브랜드 비교
   - skin_type_analysis: 피부타입별 분석
   - trend_analysis: 트렌드 분석
   - general_analysis: 일반 분석
   
5. channel: 채널 (언급되었으면)
   - 가능한 채널: {channels_str}
   - 없으면 null
   
6. needs_comparison: 비교가 필요한가? (true/false)

7. needs_skin_type: 피부타입 분석이 필요한가? (true/false)

8. confidence: 분석 신뢰도 (0.0 ~ 1.0)

JSON 형식으로만 반환:
{{
    "brands": ["브랜드1", "브랜드2"],
    "keywords": ["키워드1", "키워드2"],
    "aspects": ["속성1"],
    "query_type": "aspect_analysis",
    "channel": "OliveYoung",
    "needs_comparison": false,
    "needs_skin_type": false,
    "confidence": 0.95
}}"""
        
        return prompt
    
    def _create_fallback_result(self, query: str) -> Dict:
        """
        LLM 실패 시 Fallback 결과
        
        Args:
            query: 사용자 질문
        
        Returns:
            최소한의 파싱 결과
        """
        
        return {
            'original_query': query,
            'brands': [],
            'keywords': [],
            'aspects': [],
            'query_type': 'general_analysis',
            'channel': None,
            'needs_comparison': False,
            'needs_skin_type': False,
            'confidence': 0.3
        }
    
    def _enrich_with_db(self, result: Dict):
        """
        DB에서 추가 정보 보강
        
        Args:
            result: 파싱 결과 (in-place 수정)
        """
        
        try:
            import psycopg2
            
            # 브랜드별 리뷰 개수 추정
            if result.get('brands'):
                brand = result['brands'][0]  # 첫 번째 브랜드
                
                conn = psycopg2.connect(**self.db_config)
                cur = conn.cursor()
                
                query = """
                    SELECT COUNT(*) 
                    FROM reviews 
                    WHERE brand = %s
                """
                
                cur.execute(query, (brand,))
                count = cur.fetchone()[0]
                
                result['estimated_review_count'] = count
                
                cur.close()
                conn.close()
                
                logger.info(f"Brand '{brand}' has ~{count} reviews")
            else:
                result['estimated_review_count'] = 0
                
        except Exception as e:
            logger.error(f"Failed to enrich with DB: {e}")
            result['estimated_review_count'] = 0
