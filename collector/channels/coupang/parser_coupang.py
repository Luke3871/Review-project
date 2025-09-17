#//==============================================================================//#
"""
쿠팡 제품 데이터 파싱 모듈
- 제품 카드에서 정보 추출
- 데이터 정제 및 구조화

last_updated : 2025.09.10
"""
#//==============================================================================//#

from selenium.webdriver.common.by import By
from config_coupang import (
    PRODUCT_NAME, 
    PRODUCT_PRICE_ORIGINAL,
    PRODUCT_PRICE_SALE,
    PRODUCT_DISCOUNT_RATE
)

#//==============================================================================//#
# 제품 데이터 파싱
#//==============================================================================//#
def parse_product_card(product, rank, category, sort_type):
    """개별 제품 카드에서 데이터 추출"""
    try:
        # 제품 링크
        link_elem = product.find_element(By.CSS_SELECTOR, "a")
        href = link_elem.get_attribute("href")
        
        # 제품명
        name_elem = product.find_element(By.CSS_SELECTOR, PRODUCT_NAME)
        name = name_elem.text.strip()
        
        # 할인된 가격 (필수)
        sale_price_elem = product.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_SALE)
        sale_price = sale_price_elem.text.strip()
        
        # 원래 가격 (선택적)
        try:
            original_price_elem = product.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_ORIGINAL)
            original_price = original_price_elem.text.strip()
        except:
            original_price = ""
        
        # 할인율 (선택적)
        try:
            discount_elem = product.find_element(By.CSS_SELECTOR, PRODUCT_DISCOUNT_RATE)
            discount_rate = discount_elem.text.strip()
        except:
            discount_rate = ""
        
        # 데이터 구조화
        product_data = {
            "category": category,
            "sort_type": sort_type,
            "rank": rank,
            "name": name,
            "url": href,
            "type": "beauty",
            "sale_price": sale_price,
            "original_price": original_price,
            "discount_rate": discount_rate
        }
        
        return product_data
        
    except Exception as e:
        print(f"제품 파싱 오류 (순위 {rank}): {e}")
        return None