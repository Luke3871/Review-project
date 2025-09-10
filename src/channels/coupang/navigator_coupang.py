#//==============================================================================//#
"""
쿠팡 네비게이션 모듈
- 페이지 이동 및 대기 로직
- 제품 카드 수집
- 리뷰 페이지네이션 이동 (리뷰 수집은 제외)

last_updated : 2025.09.10
"""
#//==============================================================================//#

import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from random import randint
from config_coupang import (
    PRODUCT_CARD, 
    build_category_url,
    REVIEW_NEXT_BUTTON,
    REVIEW_PAGE_NUMBERS
)

#//==============================================================================//#
# 제품 목록 페이지 네비게이션
#//==============================================================================//#
def navigate_to_category(driver, category, sort_type, list_size=120):
    """특정 카테고리 페이지로 이동"""
    try:
        url = build_category_url(category, sort_type, list_size)
        print(f"페이지 이동: {url}")
        
        driver.get(url)
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"페이지 이동 실패: {e}")
        return False

def collect_product_cards(driver, max_products=100):
    """제품 카드 요소들 수집"""
    try:
        products = driver.find_elements(By.CSS_SELECTOR, PRODUCT_CARD)
        print(f"발견된 제품 카드: {len(products)}개")
        
        if len(products) > max_products:
            products = products[:max_products]
            print(f"최대 {max_products}개로 제한")
        
        return products
        
    except Exception as e:
        print(f"제품 카드 수집 실패: {e}")
        return []

#//==============================================================================//#
# 리뷰 페이지 네비게이션 (이동만 담당)
#//==============================================================================//#
def go_to_page(driver, target_page):
    """
    특정 페이지 번호로 이동
    
    Args:
        driver: Selenium WebDriver
        target_page: 이동할 페이지 번호
        
    Returns:
        bool: 이동 성공 여부
    """
    try:
        print(f"페이지 {target_page}로 이동 시도...")
        
        # 현재 화면에 표시된 페이지 번호들 확인
        available_pages = get_available_pages(driver)
        
        if not available_pages:
            print("페이지 번호 버튼을 찾을 수 없습니다.")
            return False
        
        print(f"현재 표시된 페이지들: {available_pages}")
        
        # 목표 페이지가 현재 화면에 있는지 확인
        if target_page in available_pages:
            # 해당 페이지 번호 버튼 클릭
            success = click_page_button(driver, target_page)
            if success:
                print(f"페이지 {target_page} 이동 완료")
                return True
        else:
            # 목표 페이지가 화면에 없으면 다음 그룹 로드
            if click_next_group(driver):
                time.sleep(2)
                # 다시 시도
                return go_to_page(driver, target_page)
            else:
                print(f"페이지 {target_page}에 도달할 수 없습니다.")
                return False
                
    except Exception as e:
        print(f"페이지 {target_page} 이동 오류: {e}")
        return False
    
    return False

def get_available_pages(driver):
    """
    현재 화면에 표시된 페이지 번호들 반환
    
    Returns:
        List[int]: 사용 가능한 페이지 번호 리스트
    """
    try:
        page_buttons = driver.find_elements(By.CSS_SELECTOR, REVIEW_PAGE_NUMBERS)
        available_pages = []
        
        for btn in page_buttons:
            try:
                # data-page 속성에서 페이지 번호 추출
                page_num = btn.get_attribute("data-page")
                if page_num:
                    available_pages.append(int(page_num))
                else:
                    # data-page가 없으면 텍스트에서 추출 시도
                    text = btn.text.strip()
                    if text.isdigit():
                        available_pages.append(int(text))
            except:
                continue
        
        return sorted(available_pages)
        
    except Exception as e:
        print(f"페이지 번호 확인 오류: {e}")
        return []

def click_page_button(driver, page_num):
    """
    특정 페이지 번호 버튼 클릭
    
    Args:
        page_num: 클릭할 페이지 번호
        
    Returns:
        bool: 클릭 성공 여부
    """
    try:
        # data-page 속성으로 찾기
        try:
            target_button = driver.find_element(By.CSS_SELECTOR, f'[data-page="{page_num}"]')
        except:
            # data-page가 없으면 텍스트로 찾기
            page_buttons = driver.find_elements(By.CSS_SELECTOR, REVIEW_PAGE_NUMBERS)
            target_button = None
            for btn in page_buttons:
                if btn.text.strip() == str(page_num):
                    target_button = btn
                    break
            
            if not target_button:
                print(f"페이지 {page_num} 버튼을 찾을 수 없습니다.")
                return False
        
        # 버튼 클릭
        driver.execute_script("arguments[0].click();", target_button)
        time.sleep(randint(1, 2))
        return True
        
    except Exception as e:
        print(f"페이지 {page_num} 버튼 클릭 오류: {e}")
        return False

def click_next_group(driver):
    """
    다음 페이지 그룹으로 이동 (예: 1-10 → 11-20)
    
    Returns:
        bool: 이동 성공 여부
    """
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, REVIEW_NEXT_BUTTON)
        
        # disabled 상태 확인
        if next_button.get_attribute("disabled") is not None:
            print("다음 그룹 버튼이 비활성화됨")
            return False
        
        if "disabled" in next_button.get_attribute("class"):
            print("다음 그룹 버튼 클래스에 disabled 포함")
            return False
        
        # 다음 그룹 버튼 클릭
        driver.execute_script("arguments[0].click();", next_button)
        time.sleep(randint(1, 2))
        print("다음 그룹으로 이동 완료")
        return True
        
    except NoSuchElementException:
        print("다음 그룹 버튼을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"다음 그룹 이동 오류: {e}")
        return False

def is_last_page_group(driver):
    """
    현재 페이지 그룹이 마지막인지 확인
    
    Returns:
        bool: 마지막 그룹 여부
    """
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, REVIEW_NEXT_BUTTON)
        
        # disabled 상태면 마지막 그룹
        if next_button.get_attribute("disabled") is not None:
            return True
        
        if "disabled" in next_button.get_attribute("class"):
            return True
        
        return False
        
    except:
        return True  # 버튼이 없으면 마지막으로 간주