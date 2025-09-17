#//==============================================================================//#
"""
정렬/카테고리 세팅이 끝난 화면에서, 
'제품' 기준 Top100이 확보될 때까지 안정적으로 더 불러오기

 - TOP100 확보를 위한 PAGEDOWN
 - 제품 카드 로딩 대기
 - TOP100 확보 까지 스크롤 반복

option - daiso
last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import time
import random
from typing import Callable
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# config import
from config_daiso import CARD_ITEM

#//==============================================================================//#
# DaisoScroller Class
#//==============================================================================//#
class DaisoScroller:
    # 클래스 초기화
    def __init__(self, driver: WebDriver, wait_sec: int = 10):
        self.driver = driver
        self.wait_sec = wait_sec
        
        # 스크롤 설정값
        self.default_pause = 0.5       # 기본 대기 시간
        self.default_scroll_count = 30 # 기본 page_down 클릭수

    # 제품 카드 로딩 대기
    def wait_cards(self) -> bool:
        """
        Returns:
            bool type
        """
        # 로드될 때까지 대기
        try:
            WebDriverWait(self.driver, self.wait_sec).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, CARD_ITEM)))
            return True
        
        except Exception as e :
            print(f"제품 카드 로딩 실패 {e}")
            return False
        
    def scroll_pagedown_simple(self, n_times: int = None, pause: float = None) -> None:
        """
        PAGE_DOWN 키를 이용한 단순 스크롤
        
        Args:
            n_times: 스크롤 횟수 none -> 기본값 사용
            pause: 각 스크롤 사이 대기 시간 none -> 기본값 사용
        """
        n_times = n_times if n_times is not None else self.default_scroll_count
        pause = pause if pause is not None else self.default_pause

        # PAGE_DOWN 활용 스크롤
        body = self.driver.find_element(By.TAG_NAME, "body")
        for i in range(n_times):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(pause)

    def scroll_until_target_count(self, target_count: int, product_counter: Callable[[], int], no_growth_limit: int = 3, max_scrolls: int = 100) -> tuple[bool, int]:
        """
        TOP100을 채울 때 까지 제품이 로드될 때까지 스크롤
        
        Args:
            target_count: 목표 제품 수 100
            product_counter: 현재 로딩된 제품 수를 반환하는 함수
            no_growth_limit: 스크롤 횟수 증가 없이 시도할 최대 횟수
            max_scrolls: 최대 스크롤 횟수
            
        Returns:
            tuple[성공 여부, 최종 제품 수]
        """
        # 초기 카드 로딩 대기
        if not self.wait_cards():
            return (False, product_counter())

        no_growth_rounds = 0
        prev_count = product_counter()   

        for i in range(max_scrolls):
            current_count = product_counter()
            
            # 목표 달성 확인
            if current_count >= target_count:
                print(f"목표 달성: {current_count}/{target_count}")
                return (True, current_count)
            
            # 스크롤 실행
            self.scroll_pagedown_simple(n_times=3)
            
            # 로딩 대기
            self.wait_cards()

            # 제품 수 증가 확인
            new_count = product_counter()

            if new_count > prev_count:
                no_growth_rounds = 0
                print(f"진행중: {new_count}/{target_count}개")
                prev_count = new_count
            else:
                no_growth_rounds += 1
                print(f"증가 없음 ({no_growth_rounds}/{no_growth_limit})")

            # 더 이상 증가하지 않으면 중단
            if no_growth_rounds >= no_growth_limit:
                print("더 이상 새로운 제품을 로드할 수 없습니다.")
                break

        final_count = product_counter()
        success = final_count >= target_count
        
        print(f"스크롤 완료: {final_count}/{target_count} ({'TOP100 구성 성공' if success else '부족'})")
        return (success, final_count)
