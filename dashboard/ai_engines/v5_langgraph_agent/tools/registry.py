"""
Tool Registry - 모든 Tool을 등록하고 관리

14개 Tool을 중앙에서 관리하며, Tool 이름으로 인스턴스를 가져올 수 있음
"""

from typing import Dict, Type

from .base_tool import BaseTool
from .attribute_tool import AttributeTool
from .sentiment_tool import SentimentTool
from .keyword_tool import KeywordTool
from .positioning_tool import PositioningTool
from .comparison_tool import ProductComparisonTool
from .promotion_mention_tool import PromotionMentionTool
from .promotion_analysis_tool import PromotionAnalysisTool
from .comparison_mention_tool import ComparisonMentionTool
from .keyword_sentiment_tool import KeywordSentimentTool
from .pros_tool import ProsTool
from .cons_tool import ConsTool
from .complaint_tool import ComplaintTool
from .purchase_motivation_tool import PurchaseMotivationTool
from .channel_category_tool import ChannelCategoryTool


# Tool Registry: Tool 이름 -> Tool 클래스 매핑
TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {
    # 1. 속성 분석
    "AttributeTool": AttributeTool,

    # 2. 감성 분석
    "SentimentTool": SentimentTool,

    # 3. 키워드 분석
    "KeywordTool": KeywordTool,

    # 4. 제품 포지셔닝
    "PositioningTool": PositioningTool,

    # 5. 제품 비교
    "ProductComparisonTool": ProductComparisonTool,

    # 6. 기획 언급 분석
    "PromotionMentionTool": PromotionMentionTool,

    # 7. 기획별 반응 분석
    "PromotionAnalysisTool": PromotionAnalysisTool,

    # 8. 타제품 언급 분석
    "ComparisonMentionTool": ComparisonMentionTool,

    # 9. 키워드-감성 연계 분석
    "KeywordSentimentTool": KeywordSentimentTool,

    # 10. 장점 분석
    "ProsTool": ProsTool,

    # 11. 단점 분석
    "ConsTool": ConsTool,

    # 12. 불만사항 분석
    "ComplaintTool": ComplaintTool,

    # 13. 구매동기 분석
    "PurchaseMotivationTool": PurchaseMotivationTool,

    # 14. 채널별 카테고리 분석
    "ChannelCategoryTool": ChannelCategoryTool,
}


def get_tool(tool_name: str) -> BaseTool:
    """
    Tool 이름으로 Tool 인스턴스 반환

    Args:
        tool_name: Tool 이름 (예: "AttributeTool")

    Returns:
        Tool 인스턴스

    Raises:
        ValueError: Tool 이름이 유효하지 않을 때
    """
    if tool_name not in TOOL_REGISTRY:
        available_tools = ", ".join(TOOL_REGISTRY.keys())
        raise ValueError(
            f"'{tool_name}'은 유효하지 않은 Tool 이름입니다.\n"
            f"사용 가능한 Tool: {available_tools}"
        )

    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class()


def get_all_tool_names() -> list:
    """
    모든 Tool 이름 반환

    Returns:
        Tool 이름 리스트
    """
    return list(TOOL_REGISTRY.keys())


def get_tool_description(tool_name: str) -> str:
    """
    Tool 설명 반환

    Args:
        tool_name: Tool 이름

    Returns:
        Tool 설명
    """
    tool_descriptions = {
        "AttributeTool": "제품 속성별 만족도 분석 (보습력, 발림성, 향, 가격 등)",
        "SentimentTool": "리뷰 감성 분석 (긍정/부정 비율, 핵심표현)",
        "KeywordTool": "키워드 추출 및 빈도 분석",
        "PositioningTool": "제품 포지셔닝 분석 (강점, 약점, 차별점)",
        "ProductComparisonTool": "2개 제품 비교 분석 (속성, 감성, 키워드)",
        "PromotionMentionTool": "기획/프로모션 언급 분석 (구성만족도, 가성비평가)",
        "PromotionAnalysisTool": "기획 타입별 반응 분석 (증정, 세트, 한정 등)",
        "ComparisonMentionTool": "타제품 언급 분석 (비교 대상, 우위/열위)",
        "KeywordSentimentTool": "키워드-감성 연계 분석 (키워드별 맥락, 공출현)",
        "ProsTool": "장점 분석 (빈도, 카테고리별 분류)",
        "ConsTool": "단점 분석 (빈도, 카테고리별 분류)",
        "ComplaintTool": "불만사항 분석 (유형별 분류, 심각도)",
        "PurchaseMotivationTool": "구매동기 분석 (유형별 분류)",
        "ChannelCategoryTool": "채널별 카테고리 중요 반응 분석"
    }

    return tool_descriptions.get(tool_name, "설명 없음")


# ===== 테스트 코드 =====
if __name__ == "__main__":
    print("=== Tool Registry 테스트 ===\n")

    # 1. 모든 Tool 이름 출력
    print("**등록된 Tool 목록:**")
    for i, tool_name in enumerate(get_all_tool_names(), 1):
        description = get_tool_description(tool_name)
        print(f"{i}. {tool_name}: {description}")

    # 2. Tool 가져오기 테스트
    print("\n**Tool 가져오기 테스트:**")
    try:
        attribute_tool = get_tool("AttributeTool")
        print(f"AttributeTool 인스턴스: {attribute_tool}")
        print(f"타입: {type(attribute_tool)}")
    except ValueError as e:
        print(f"에러: {e}")

    # 3. 잘못된 Tool 이름 테스트
    print("\n**잘못된 Tool 이름 테스트:**")
    try:
        invalid_tool = get_tool("InvalidTool")
    except ValueError as e:
        print(f"예상된 에러: {e}")

    print("\n✅ Tool Registry 테스트 완료!")
