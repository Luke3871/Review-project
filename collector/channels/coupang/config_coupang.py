#//==============================================================================//#
"""
쿠팡 크롤링 설정 파일
- HTML 셀렉터
- URL 정보  
- 필터링 키워드
- 정렬 옵션 매핑

last_updated : 2025.09.10
"""
#//==============================================================================//#

#//==============================================================================//#
# 1. 네비게이션 관련
#//==============================================================================//#
# 카테고리 버튼 (메인페이지에서 좌측 메뉴 열기)
CATEGORY_BUTTON = ".fw-flex.fw-h-\\[24px\\].fw-w-\\[24px\\].fw-flex-col.fw-items-center.fw-justify-around"
# 대안 카테고리 버튼 (부분 매칭)
CATEGORY_BUTTON_ALT = "[class*='fw-flex'][class*='fw-h-'][class*='fw-w-'][class*='fw-flex-col']"

# 뷰티 카테고리 링크
BEAUTY_CATEGORY = ".beauty.wa-category-icon"

#//==============================================================================//#
# 2. 페이지당 아이템 수 조절 관련
#//==============================================================================//#
# 개수 선택 드롭다운 트리거 (호버로 드롭다운 열기)
ITEMS_DROPDOWN_TRIGGER = ".ListSizeOption_selected__Ym5KI"

# 120개 보기 라디오 버튼
ITEMS_PER_PAGE_120 = 'input[type="radio"][id="listSize-120"]'

# 120개 보기 라벨 (대안)
ITEMS_PER_PAGE_120_LABEL = 'label[for="listSize-120"]'

#//==============================================================================//#
# 3. 제품 카드 관련 셀렉터
#//==============================================================================//#
# 개별 제품 카드
PRODUCT_CARD = ".ProductUnit_productUnit__Qd6sv"

# 제품 링크 (카드 내의 a 태그)
PRODUCT_LINK = f"{PRODUCT_CARD} a"

# 제품 정보 섹션
PRODUCT_INFO = ".ProductUnit_productInfo__1l0il"

# 제품명
PRODUCT_NAME = ".ProductUnit_productName__gre7e"

# 가격 관련 셀렉터들
PRODUCT_PRICE_ORIGINAL = "del.PriceInfo_basePrice__8BQ32"    # 원래 가격  
PRODUCT_PRICE_SALE = "strong.Price_priceValue__A4KOr"          # 할인된 가격
PRODUCT_DISCOUNT_RATE = "span.PriceInfo_discountRate__EsQ8I" # 할인율

#//==============================================================================//#
# 4. 카테고리 URL
#//==============================================================================//#
CATEGORY_URLS = {
    "skincare": "https://www.coupang.com/np/categories/176530",  
    "makeup": "https://www.coupang.com/np/categories/176573"     
}

# 베스트셀러 URL (7일간 판매량 기준 - 참고용)
BESTSELLER_URLS = {
    "skincare": "https://www.coupang.com/np/best100/bestseller/176430",
    "makeup": "https://www.coupang.com/np/best100/bestseller/176473"
}

#//==============================================================================//#
# 5. 정렬 옵션 매핑
#//==============================================================================//#
SORT_OPTIONS = {
    "SALES": "saleCountDesc",              # 판매량순
    "RANKED_COUPANG": "bestAsc",           # 쿠팡랭킹순 
    "REVIEW": "reviewCountDesc",           # 리뷰많은순 (나중에 필요시)
    "RATING": "scoreDesc",                 # 평점순 (나중에 필요시)
    "PRICE_LOW": "salePriceAsc",          # 낮은가격순 (나중에 필요시)
    "PRICE_HIGH": "salePriceDesc"         # 높은가격순 (나중에 필요시)
}

def build_category_url(category_key, sort_key="SALES", list_size=120):
    """카테고리 URL 생성 함수 (업데이트된 매핑 사용)"""
    base_url = CATEGORY_URLS[category_key]
    sort_param = SORT_OPTIONS[sort_key]
    params = [
        f"listSize={list_size}",
        f"sorter={sort_param}"
    ]
    return f"{base_url}?{'&'.join(params)}"

#//==============================================================================//#
# 6. 필터링 키워드 (필요시 사용 - 일단은 빈 리스트로 시작)
#//==============================================================================//#
EXCLUDE_KEYWORDS = [
    # 쿠팡은 카테고리가 잘 정리되어 있어서 일단 필터링 없이 시작
    # 필요하면 나중에 추가
]

#//==============================================================================//#
# 7. 제품 상세 페이지 관련 셀렉터
#//==============================================================================//#
# 제품 정보 (상세 페이지)
PRODUCT_NAME_DETAIL = ".sdp-review__article__list__info__product-info__name"        # 상세 페이지 제품명
PRODUCT_PRICE_SALE_DETAIL = ".price-amount final-price-amount !twc-leading-[24px]"  # 상세 페이지 할인 가격
PRODUCT_PRICE_ORIGINAL_DETAIL = ".price-amount original-price-amount"  # 상세 페이지 원래 가격  
PRODUCT_DISCOUNT_RATE_DETAIL = ".order:0;margin-right:3px;color:#212b36"   # 상세 페이지 할인율, style
PRODUCT_BRAND_DETAIL = "div.twc-text-sm twc-text-blue-600" # 브랜드명
CATEGORY_USE_BREADCRUMB = "ul.breadcrumb li a" # 중분류
#//==============================================================================//#
# 8. 리뷰 관련 셀렉터
#//==============================================================================//#
REVIEW_CONTAINER = ".js_reviewArticleListContainer"
REVIEW_ITEM = ".sdp-review__article__list js_reviewArticleReviewList"
REVIEWER_NAME = ".sdp-review__article__list__info__user__name js_reviewUserProfileImage"
REVIEW_RATING = ".sdp-review__article__list__info__product-info__star-orange[data-rating]"
REVIEW_DATE = ".sdp-review__article__list__info__product-info__reg-date"
REVIEW_TEXT = ".sdp-review__article__list__review__content"
REVIEW_SELECTED_OPTION = "div.sdp-review__article__list__info__product-info__name"
REVIEW_HELPFUL_COUNT = ".sdp-review__article__list__help_count strong"
REVIEW_SURVEY_ROW = ".sdp-review__article__list__survey_row"
REVIEW_SURVEY_QUESTION = ".sdp-review__article__list__survey_row__question"
REVIEW_SURVEY_ANSWER = ".sdp-review__article__list__survey_row__answer"


#//==============================================================================//#
# 9. 리뷰 페이지네이션 관련 셀렉터
#//==============================================================================//#
REVIEW_PAGE_NUMBERS = ".js_reviewArticlePageBtn"  # 페이지 번호 버튼들
REVIEW_NEXT_BUTTON = ".js_reviewArticlePageNextBtn"  # 다음 페이지 버튼
REVIEW_CURRENT_PAGE = ".sdp-review__article__page__num--active"  # 현재 활성 페이지
