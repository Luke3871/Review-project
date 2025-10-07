from router import route_question
from prompt_templates import build_prompt
from search_engine import search_reviews   # 당신이 이미 만든 함수
from config import ROUTER_LLM
from typing import Tuple

# 라벨별 기본 검색 파라미터(간단 버전)
def search_params_for(label: str):
    if label == "trend":              return dict(top_k=100)   # 기간 필터는 DB 스키마에 맞춰 추후 추가
    if label == "persona":            return dict(top_k=100)
    if label == "quality_issue":      return dict(top_k=100)
    if label == "brand_insight":      return dict(top_k=100)
    if label == "price_promo":        return dict(top_k=100)
    if label == "attribute_drivers":  return dict(top_k=100)
    return dict(top_k=100)

def answer_with_rag(question: str, client) -> Tuple[str, str]:
    # 1) 라벨 결정
    label = route_question(
        question,
        client=client,
        use_llm=True,
        model_name=ROUTER_LLM["model_name"],
        temperature=ROUTER_LLM["temperature"],
        max_tokens=ROUTER_LLM["max_tokens"],
    )

    # 2) 벡터 검색
    params = search_params_for(label)
    hits = search_reviews(question, **params)  # [(review_id, review_text), ...]

    # 3) 프롬프트 구성
    prompt = build_prompt(question, hits, mode=label)

    # 4) LLM 호출(최종 답변 생성)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,  # 표준 모드: 낮게 유지
        messages=[{"role": "user", "content": prompt}]
    )
    answer = resp.choices[0].message.content
    return label, answer