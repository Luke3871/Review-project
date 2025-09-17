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
"""
import os
from .config_daiso import BASE_DATA_PATH, PRODUCTS_PATH

# 환경변수 확인 후 경로 오버라이드해서 사용
if os.getenv("DAISO_DATA_PATH"):
    custom_base = Path(os.getenv("DAISO_DATA_PATH"))
    products_path = custom_base / "products_daiso"
else:
    products_path = PRODUCTS_PATH
"""
#//==============================================================================//#
# 1.1. DATA 폴더
BASE_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "data_daiso" / "raw_data"

# 1.2. DATA 하위 폴더
# 1.2.1. TOP100 상품 메타 데이터
PRODUCTS_PATH = BASE_DATA_PATH / "products_daiso"

# 1.2.2. TOP100 상품 리뷰 데이터
REVIEWS_PATH = BASE_DATA_PATH / "reviews_daiso"

# 1.2.3. TOP100 상품 이미지 데이터
PRODUCTS_IMAGE_PATH = BASE_DATA_PATH / "products_image_daiso"

# 1.2.4. TOP100 상품 리뷰 이미지 데이터
REVIEWS_IMAGE_PATH = BASE_DATA_PATH / "reviews_image_daiso"

#//==============================================================================//#
# 2. 정렬 드롭다운 박스 관련 selector
#//==============================================================================//#
# 2.1. 드롭다운 내리는 화살표
DROPDOWN_BUTTON = "span.el-input__suffix"

# 2.2. 추천순, 리뷰많은순 ... 
DROPDOWN_OPTION = "li.el-select-dropdown__item"

#//==============================================================================//#
# 3. 제품 카드 관련 selector
#//==============================================================================//#
# 3.1. 제품 전체 컨테이너
CARD_CONTAINER = "div.goods-list.type-card.div-4"

# 3.2. 개별 제품
CARD_ITEM = "div.goods-unit"

# 3.3. 개별 제품 링크
CARD_THUMB_LINK = "a.goods-link"

# 3.4. 개별 제품 이름
CARD_ITEM_NAME = "div.tit"

# 3.5. 개별 제품 가격
CARD_ITEM_PRICE = "div.goods-detail > a > div.goods-price > span.value"

# 3.6. 제품 썸네일 이미지
CARD_ITEM_IMAGE = "img.thumb-img.lazyLoad.isLoaded"

#//==============================================================================//#
# 4. 카테고리 URL
#//==============================================================================//#
# 4.1. 스킨케어/메이크업 각 카테고리
CATEGORY_URLS = {
    "skincare": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00057",
    "makeup": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00054"
}

#//==============================================================================//#
# 5. 필터링 키워드
#//==============================================================================//#
"""
다이소의 경우 상품과 관련없는 뷰티 악세서리 관련한 제품들이 많이 노출...
더 좋은 해결방법을 찾아야하겠지만 우선은 이름에서 필터링 하는 걸로
향후 수정 예정
"""
# 5.1. 필터링 사전
EXCLUDE_KEYWORDS = [
    "퍼프", "브러시", "펜슬", "스폰지", "도구", "악세서리", "브러쉬", "패드", 
    "뷰러", "스패츌러", "빗", "집게", "분첩", "면봉", "기름종이"
]

#//==============================================================================//#
# 6. 정렬 옵션 매핑
#//==============================================================================//#
"""
판매량순을 사용하는 것이 수요예측을 위해서는 필요할 것 같으나
마케팅 인사이트 제공을 위해서는 리뷰 많은 순이 필요할 것으로 생각
채널별 추천순은 기준을 모르겠의 이부분 질의 
"""
# 6.1. 정렬 드롭다운 박스 dictionary
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

# 7.1. 리뷰 버튼
REVIEW_BUTTON = "//button[contains(., '리뷰')]"  # XPath

# 7.2. 개별 리뷰 요소들
REVIEWER_NAME = "span.name"           # 리뷰어 이름

REVIEW_RATING = "span.score"          # 별점/평점

REVIEW_DATE = "div.review-date"       # 작성일

REVIEW_CONTENT = "div.cont"           # 리뷰 텍스트

REVIEW_INFO_KEY = "div.item"          # 평가 키
"""
스킨케어 - 보습력, 자극도, 흡수력
메이크업 - 보습력, 향, 발색정도
"""

REVIEW_INFO_VALUE = "div.val"         # 평가 값
"""
스킨케어 - 
메이크업 -
"""

# 7.3. 페이지네이션
NEXT_BUTTON = "button.btn-next"              # 다음 버튼

CURRENT_PAGE = "li.number.active"     # 현재 페이지 번호

PREV_BUTTON = "button.btn-prev"              # 이전 버튼

# 7.4. 리뷰 컨테이너/섹션
REVIEW_SECTION = "ul.review-list"       # 리뷰 목록 컨테이너

REVIEW_ITEM = "div.cont"          # 개별 리뷰 아이템

# 7.5. 도움이 되요 수
REVIEW_HELPFUL = "span.num"

# 7.6. 소비자 리뷰 이미지
REVIEW_IMAGES = "img.thumb-img"       