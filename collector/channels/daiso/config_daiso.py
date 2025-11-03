#//==============================================================================//#
"""
다이소 크롤러 설정 파일
- 저장 경로 설정
- HTML 셀렉터
- URL 정보  
- 필터링 키워드
- 정렬 옵션 매핑

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# 0. Library import
#//==============================================================================//#
import os
from pathlib import Path

#//==============================================================================//#
# 1. 기본 경로
#//==============================================================================//#
# 프로젝트 루트에서 data 폴더 찾기
current_file = Path(__file__)
project_root = current_file.parent.parent.parent  # daiso -> collector -> Review-project-main

# 1.1. DATA 폴더 구조: data/data_daiso/raw_data
BASE_DATA_PATH = project_root / "data" / "data_daiso" / "raw_data"

# 1.2. DATA 하위 폴더
PRODUCTS_PATH = BASE_DATA_PATH / "products_daiso"
REVIEWS_PATH = BASE_DATA_PATH / "reviews_daiso"
PRODUCTS_IMAGE_PATH = BASE_DATA_PATH / "products_image_daiso"
REVIEWS_IMAGE_PATH = BASE_DATA_PATH / "reviews_image_daiso"

#//==============================================================================//#
# 2. 정렬 드롭다운 박스 관련 selector
#//==============================================================================//#
DROPDOWN_BUTTON = "span.el-input__suffix"
DROPDOWN_OPTION = "li.el-select-dropdown__item"

#//==============================================================================//#
# 3. 제품 카드 관련 selector
#//==============================================================================//#
CARD_CONTAINER = "div.goods-list.type-card.div-4"
CARD_ITEM = "div.goods-unit"
CARD_THUMB_LINK = "a.goods-link"
CARD_ITEM_NAME = "div.tit"
CARD_ITEM_PRICE = "div.goods-detail > a > div.goods-price > span.value"
CARD_ITEM_IMAGE = "img.thumb-img.lazyLoad.isLoaded"

# 추가: 브랜드 및 카테고리
BRAND_LINK = "a[href*='/dsBrand/']"
BREADCRUMB_ITEMS = "span.el-breadcrumb__item"

#//==============================================================================//#
# 4. 카테고리 URL
#//==============================================================================//#
CATEGORY_URLS = {
    "skincare": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00057",
    "makeup": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00054"
}

#//==============================================================================//#
# 5. 필터링 키워드
#//==============================================================================//#
EXCLUDE_KEYWORDS = [
    "퍼프", "브러시", "펜슬", "스폰지", "도구", "악세서리", "브러쉬", "패드", 
    "뷰러", "스패츌러", "빗", "집게", "분첩", "면봉", "기름종이"
]

#//==============================================================================//#
# 6. 정렬 옵션 매핑
#//==============================================================================//#
SORT_TEXT_MAP = {
    "RECOMMEND":   "추천순", 
    "NEW":         "신상품순",
    "SALES":       "판매량순",
    "REVIEW":      "리뷰많은순",
    "LIKE":        "좋아요순",
    "PRICE_HIGH":  "가격높은순",
    "PRICE_LOW":   "가격낮은순"
}

#//==============================================================================//#
# 7. 리뷰 관련 셀렉터
#//==============================================================================//#
REVIEW_BUTTON = "//button[contains(., '리뷰')]"
REVIEWER_NAME = "span.name"
REVIEW_RATING = "span.score"
REVIEW_DATE = "div.review-date"
REVIEW_CONTENT = "div.cont"
REVIEW_INFO_KEY = "div.item"
REVIEW_INFO_VALUE = "div.val"
REVIEW_HELPFUL = "span.num"
REVIEW_IMAGES = "img.thumb-img"
NEXT_BUTTON = "button.btn-next"
CURRENT_PAGE = "li.number.active"
PREV_BUTTON = "button.btn-prev"
REVIEW_SECTION = "ul.review-list"
REVIEW_ITEM = "div.cont"