#//==============================================================================//#
"""
output_generator.py
텍스트 출력 생성

last_updated: 2025.11.02
"""
#//==============================================================================//#

import json
from typing import Dict, Any, List
from openai import OpenAI

import sys
from pathlib import Path

# V7 config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import LLM_CONFIG


class OutputGenerator:
    """출력 생성"""

    def __init__(self):
        self.client = OpenAI()
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]["output_generator"]  # 0.3
        self.max_tokens = LLM_CONFIG["max_tokens"]

    def _generate_text_output(
        self,
        user_query: str,
        parsed_entities: Dict[str, Any],
        query_results: Dict[str, Any]
    ) -> str:
        """
        LLM으로 텍스트 요약 생성

        Args:
            user_query: 사용자 질문
            parsed_entities: 추출된 엔티티
            query_results: execute_sql Tool의 출력

        Returns:
            텍스트 요약
        """
        # 쿼리 결과를 텍스트로 변환
        results_summary = []
        for i, result in enumerate(query_results["results"], 1):
            if result["success"]:
                # datetime 객체를 문자열로 변환
                sample_data = result['data'][:5]  # 샘플 5개
                safe_sample = []
                for row in sample_data:
                    safe_row = {}
                    for k, v in row.items():
                        # datetime/date 객체는 isoformat()으로 변환
                        if hasattr(v, 'isoformat'):
                            safe_row[k] = v.isoformat()
                        else:
                            safe_row[k] = v
                    safe_sample.append(safe_row)

                purpose = result.get('purpose', '쿼리')
                table_name = result.get('table_name', '')
                table_info = f" (from {table_name})" if table_name else ""

                results_summary.append(
                    f"쿼리 {i}{table_info}: {purpose}\n"
                    f"결과: {result['row_count']}건\n"
                    f"데이터 샘플:\n{json.dumps(safe_sample, ensure_ascii=False, indent=2)}\n"
                )
            else:
                results_summary.append(
                    f"쿼리 {i}: {result.get('purpose', '쿼리')}\n"
                    f"오류: {result['error']}\n"
                )

        results_text = "\n".join(results_summary)

        prompt = f"""당신은 LG생활건강 마케팅팀을 위한 데이터 분석가입니다.
사용자 질문에 정확히 답변하되, **사용자가 요청한 내용만** 제공하세요.

**사용자 질문:**
{user_query}

**추출된 정보:**
- 브랜드: {', '.join(parsed_entities.get('brands', [])) or '전체'}
- 제품: {', '.join(parsed_entities.get('products', [])) or '전체'}
- 속성: {', '.join(parsed_entities.get('attributes', [])) or '전체'}
- 기간: {parsed_entities.get('period', {}).get('display', '전체')}

**SQL 쿼리 결과:**
{results_text}

---

**작성 가이드:**

사용자 질문의 의도를 파악하여 적절한 수준으로 답변하세요.

**1. 단순 조회 ("보여줘", "알려줘", "어때?"):**
   → 핵심 수치 + 간단한 설명만

**2. 비교/분석 요청 ("비교", "분석", "트렌드"):**
   → 핵심 수치 + 패턴/트렌드 분석

**3. 심층 분석 요청 ("마케팅", "활용", "시사점", "인사이트"):**
   → 전체 리포트 (마케팅 시사점 포함)

**사용 가능한 섹션:**

### 핵심 요약 (필수)
- SQL 결과의 주요 수치를 2-3문장으로 요약
- 사용자가 물어본 것에 대한 직접적인 답변

### 데이터 분석 (비교/분석 요청 시)
- SQL 결과에서 발견한 패턴과 트렌드
- 구체적 수치 제시 (건수, 비율, 평균 등)
- preprocessed_reviews 데이터인 경우:
  * 제품특성 (제형, 발림성, 향, 지속력 등)
  * 감정요약 (긍정/부정 비율, 핵심표현)
  * 장점/단점 키워드

### 리뷰 샘플 (SQL 결과에 리뷰 원문 있을 때만)
- 대표 긍정 리뷰 2-3개 직접 인용
- 대표 부정 리뷰 1-2개 직접 인용

### 마케팅 시사점 (사용자가 명시적으로 요청했을 때만)
- SQL 결과 기반 실무 제안
- 캠페인 소구점
- 개선 영역
- 타겟 확장 기회

### 데이터 범위 (필수)
- 분석 건수, 기간, 출처 명시
- 어느 테이블에서 쿼리했는지 (reviews 또는 preprocessed_reviews)
- 총 몇 건의 데이터를 기반으로 분석했는지

---

**중요 원칙:**
1. **사용자가 요청한 내용만 제공** - 불필요한 섹션 추가하지 말 것
2. **SQL 결과에 있는 데이터만 사용** - 없는 내용 추정 금지
3. **데이터 기반 답변** - 정량적 질문은 숫자로, 정성적 질문은 SQL 결과의 텍스트/키워드로 뒷받침
4. **이모지 사용 금지** - 깔끔한 마크다운만 사용
5. **간결하게** - 핵심만 전달

**사용자 질문의 의도를 정확히 파악하여 필요한 수준의 답변만 제공하세요:**"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        return response.choices[0].message.content.strip()
