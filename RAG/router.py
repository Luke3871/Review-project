#//==============================================================================//#
"""
Router.py
질문 분류기
 - LLM이 사용자의 질문을 보고 사전에 정의한 질문으로 라벨링
 - 

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# 0. Library import
#//==============================================================================//#
import re
from typing import Optional, List

#//==============================================================================//#
# 라벨
#//==============================================================================//#

LABELS: List[str] = [
    "trend",            # 최근 트렌드/상승 SKU·카테고리
    "persona",          # 세그먼트(지성/건성/민감/여드름 등) 인사이트
    "quality_issue",    # 리스크/클레임(자극/가루날림/번들거림 등)
    "brand_insight",    # 특정 브랜드 인사이트(핵심 키워드/강약점/포지셔닝)
    "price_promo",      # 가격/프로모션(세일/가성비) 관련 인사이트
    "attribute_drivers",# 속성→만족도 드라이버(발림성/지속력/보습/향 등)
    "default"           # 기타/분류불가
]


#//==============================================================================//#
# 규칙 기반 보조 라우팅
#//==============================================================================//#

KW = {
    "trend": [
        r"성장|상승|증가율|트렌드|최근\s*(4|8|12)\s*주|분기|상위\s*(sku|제품)|베스트|잘\s*나가"]
        ,
    "persona": [
        r"(지성|건성|복합성|민감성|여드름|진정|미백|보습)\s*(피부|세그먼트)|페르소나|타깃|타겟|니즈|거부"
        ],
    "quality_issue": [
        r"자극|따갑|트러블|붉어짐|가루날림|번들거림|끈적임|지속력\s*문제|부작용|리스크|불만|이슈|냄새\s*문제|묻어남|지워짐"
        ],
    "brand_insight": [
        r"브랜드\s*(이미지|헬스|평판|인식)|연상\s*키워드|강점|약점|리스크|메시지|차별화|브랜드\s*인사이트|포지셔닝"
        ],
    "price_promo": [
        r"가격|가성비|세일|할인|행사|1\+1|프로모션|최저가|구성|가격\s*민감|딜"]
        ,
    "attribute_drivers": [
        r"발림성|지속력|커버력|보습|흡수|텍스처|향|성분|속성|드라이버|기여|무너짐|밀착감|유분감"
        ],
}
#//==============================================================================//#
# UTILS
#//==============================================================================//#

# 질문에서 사전에 정의한 키워드가 보이면 우선 힌트 라벨을 반환
def _rule_hint(question: str) -> Optional[str]:
    
    q = question.lower()
    for label, patterns in KW.items():
        for pat in patterns:
            if re.search(pat, q):
                return label
    
    return None

# LLM 응답에서 라벨 매칭 시도, 모든 라벨 실패시 default
def _parse_label(text: str) -> str:

    m = re.search(r"label\s*:\s*([a-z_]+)", text.strip(), re.I)
    label = (m.group(1).lower() if m else "default")
    return label if label in LABELS else "default"


def route_question(question: str,
                   client,
                   use_llm: bool = True,
                   model_name: str = "gpt-4o-mini",
                   temperature: float = 0.1,
                   max_tokens: int = 10
                   ) -> str:
    """
    
    질문을 단일 라벨로 분류하는 함수
    1. 규칙(키워드)로 힌트를 먼저 잡고
    2. LLM이 최종 결정 (만약 LLM이 비활성화될 경우 규칙을 적용한 결과를 단순 사용)
    3. 위 모든 과정 실패시 default
    
    """

    # 1. 규칙 힌트
    hinted = _rule_hint(question)

    # LLM이 비활성화된 경우 규칙 힌트를 사용, 둘 다 적용할 수 없다면 default
    if not use_llm or client is None:
        return hinted or "default"
    
    # 2. LLM 최종 결정 (few-shot + 형식 강요)
    system = (
        "당신의 임무는 사용자의 질문을 다음 라벨 중 하나로 정확히 분류하는 것이다."
        "반드시 하나의 라벨만을 선택하고, 출력 형식은 오직 'label:<라벨>' 한 줄이어야 한다. "
        f"선택 가능한 라벨: {', '.join(LABELS)}, default"
    )

    shots = [
        ("최근 8주 기준 리뷰 증가율이 높은 카테고리와 상위 SKU 알려줘", "label:trend"),
        ("여드름 피부 세그먼트의 반복 니즈와 거부 요인을 요약해", "label:persona"),
        ("최근 60일 자극/트러블 불만이 급증한 제품이 있나?", "label:quality_issue"),
        ("토리든 브랜드의 핵심 연상 키워드와 리스크 포인트를 정리해", "label:brand_insight"),
        ("할인 언급이 평점에 긍정적으로 작동한 카테고리가 있나?", "label:price_promo"),
        ("발림성/지속력/보습 중 어떤 속성이 평점에 더 기여하는지 알려줘", "label:attribute_drivers"),
        ("전반적인 리뷰 인사이트를 요약해", "label:default"),
    ]

    messages = [{"role": "system", "content": system}]
    for q, a in shots:
        messages += [{"role":"user","content":q},{"role":"assistant","content":a}]

    hint_line = f"힌트 라벨(규칙 기반): {hinted}" if hinted else "힌트 라벨 없음"
    messages.append({"role":"user","content":f"{hint_line}\n질문: {question}\n출력은 'label:<라벨>' 한 줄만."})

    resp = client.chat.completions.create(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages
    )
    label = _parse_label(resp.choices[0].message.content)

    if label == "default" and hinted:
        return hinted
    return label
