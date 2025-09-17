#//==============================================================================//#
"""
다이소 네비게이션 모듈

기능:
- 카테고리 페이지 이동
- 정렬 드롭다운 조작

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import time
from typing import Optional
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

# config import
from config_daiso import (
    DROPDOWN_BUTTON,
    DROPDOWN_OPTION,
)
#//==============================================================================//#
# Daiso, navigator
#//==============================================================================//#

class DaisoNavigator:
    # 클래스 초기화
    def __init__(self, driver: WebDriver, wait_sec: int = 10):
        self.driver = driver
        self.wait_sec = wait_sec

    # 카테고리 페이지로 이동
    def goto_category(self, url: str) -> None:
        """
        url: 스킨케어/메이크업 카테고리 페이지 URL
        """
        self.driver.get(url)

    # 정렬 드롭 다운 박스 열기
    def open_sort_dropdown(self) -> bool:
        try:
            btn = W(self.driver, self.wait_sec).until(EC.element_to_be_clickable((By.CSS_SELECTOR, DROPDOWN_BUTTON)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)

            try:
                btn.click()
            
            # css selector 클릭 실패시 javascript 시도
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)

            return True
        
        except Exception as e:
            print(f"드롭다운박스 열기 실패: {e}")
            return False

    # 정렬 옵션 선택
    def click_sort_option(self, label_text: str) -> bool:
        """
        정렬 옵션 (판매량순, 좋아요순, 리뷰많은순 등...) 선택

        Args: 
            label_text: 정렬 옵션 딕셔너리에서 사용

        returns:
            bool type
        """
        try:
            opts = W(self.driver, self.wait_sec).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION)))

            for option in opts:
                option_text = option.text.strip().replace(" ", "").replace("\u200b", "")
                target_text = label_text.replace(" ", "").replace("\u200b", "")

                if option_text == target_text:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)

                    try:
                        option.click()

                    # css selector 클릭 실패시 javascript 시도
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", option)
                    
                    return True
                
            print(f"정렬 옵션을 찾을 수 없음: {label_text}")
            return False
            
        except Exception as e:
            print(f"정렬 옵션 클릭 실패: {e}")
            return False