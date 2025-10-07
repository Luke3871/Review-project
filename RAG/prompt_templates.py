# prompt_templates.py — Evidence Brief 모드 (행동 지시 금지)

from typing import List, Tuple, Optional

Hit = Tuple[str, str, Optional[str], Optional[str], Optional[float], Optional[str]]

MODE_TITLE = {
    "trend": "최근 리뷰 기반 상승/변화 신호 브리핑",
    "persona": "세그먼트(피부타입/고민) 기반 반복 니즈·거부 브리핑",
    "quality_issue": "반복 품질 이슈(자극/가루/번들 등) 브리핑",
    "brand_insight": "브랜드 키워드/강약점 브리핑",
    "price_promo": "가격/프로모션 관련 언급 브리핑",
    "attribute_drivers": "속성(발림/보습/지속/향/자극) 만족 신호 브리핑",
    "default": "반복 주제 핵심 브리핑",
}

COMMON_RULES = """
[출력 원칙]
- **행동 지시나 권고를 하지 마십시오.** (예: 하라/하자/추천 X)
- **외부 사실/기억/추정을 금지**합니다. 제공된 리뷰 텍스트 안에서만 말하십시오.
- **숫자**(표본 N, 비율 %, 간단 점수)를 함께 제시하십시오.
- **대표 근거 문장**을 괄호로 1문장 첨부하십시오. 예: (“1+1 행사 때 샀는데 가성비 좋았어요”, 평점=5.0, 2024-08-02)
- 근거 부족/상충 시 **“확실하지않음”**으로 명시하십시오.
- 경쟁사/이벤트는 **리뷰 내 언급**에 한해 말하십시오 (“타 브랜드” 언급 문장, “1+1/증정/세일/기획전/사은품” 등).
"""

EVENT_HINT = """
[이벤트/프로모션 추출 힌트(리뷰 내 언급만)]
- 키워드 예시: 1+1, 증정, 사은품, 기획전, 리뉴얼, 세일, 할인, 특가, 쿨링/여름한정, NEW
- “타 브랜드/경쟁” 언급 여부도 함께 포착 (예: “OO보다 촉촉”, “XX 쓰다가 갈아탐”)
"""

def _ctx(results: List[Hit]) -> str:
    lines = []
    for rid, text, brand, pname, rating, rdate in results:
        meta = []
        if brand: meta.append(f"브랜드={brand}")
        if pname: meta.append(f"제품={pname}")
        if rating is not None: 
            try: meta.append(f"평점={float(rating):.1f}")
            except: meta.append(f"평점={rating}")
        if rdate: meta.append(f"날짜={rdate}")
        m = " | ".join(meta) if meta else ""
        lines.append(f"- {text}" + (f"  ({m})" if m else ""))
    return "\n".join(lines)

def build_prompt(
    question: str,
    results: List[Hit],
    mode: str = "default",
    period_days: int = 60,
    min_evidence: int = 40,   # 최소 표본 기준 상향
    want_events: bool = True  # 이벤트/경쟁 언급 강조
) -> str:
    title = MODE_TITLE.get(mode, MODE_TITLE["default"])
    ctx = _ctx(results)

    header = f"""
[브리핑 목적] {title}

[분석 전제]
- 사용자 질문: {question}
- 분석 기간 가정: 최근 {period_days}일
- 근거 표본: N={len(results)} (최소 보증 N={min_evidence}, 미만이면 “확실하지않음” 강조)
- 채널: OliveYoung (제공된 리뷰 내 정보만 사용)
"""

    sections = f"""
[필수 섹션]
1) 핵심 신호 요약 (2~4문장, 숫자 포함. 판단/권고 금지)
2) 지표 요약 (간단 표 형식 허용: 항목/비율/변화/표본N)
3) 이벤트/프로모션/경쟁 언급 (리뷰 내 직접 언급만, 확실하지않음 표시)
4) 대표 근거 문장 (항목별 1문장, (평점/날짜/브랜드/제품) 메타 포함)
5) 데이터 한계 (표본/기간/상충 신호)
"""

    events = EVENT_HINT if want_events else ""

    return f"""{header}
{sections}
[근거 리뷰(샘플)]
{ctx}

{COMMON_RULES}
{events}
[출력 형식 예시]
핵심 신호
- 최근 60일 기준, 보습 긍정 언급이 상대적으로 높음(대략 60%±, N≈…)
- 지속력 관련 평가가 혼재(확실하지않음), “오후 무너짐”과 “오래감”이 공존

지표 요약 (예시)
- 보습 긍정 60% / 부정 9% (N=…)
- 발림 긍정 58% / 부정 7% (N=…)
- 자극 부정 12% (N=…) — 민감 언급과 동반
- 향 호불호 혼재 (확실하지않음)

이벤트/경쟁 언급
- “1+1/증정” 언급 리뷰 비중 약 …% (N=…): “기획 세트가 가성비 좋았다” 등 (확실도: 중)
- 경쟁 비교 자의식적 언급: “XX보다 촉촉”, “OO 쓰다 갈아탐” (대표 1문장 인용, 확실도: 낮음)

대표 근거 문장
- 보습: “촉촉함이 오래가요” (평점=5.0, 2024-08-18, 브랜드=…, 제품=…)
- 이벤트: “1+1 행사 때 쟁여뒀어요” (평점=5.0, 2024-08-02, 브랜드=…, 제품=…)

데이터 한계
- 향은 호불호가 갈려 한 방향성 부족(확실하지않음)
- 특정 제품군 표본이 적음(N<40)
"""
