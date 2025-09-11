#//==============================================================================//#
"""
정렬/카테고리 세팅이 끝난 화면에서, '제품' 기준 Top100이 확보될 때까지 안정적으로 더 불러오기
데이터 로드 파트
 - 페이지다운 제품 로드
 - 제품 클릭
 - 리뷰 버튼 클릭
 - 다음 버튼 클릭 (끝까지)

option - daiso
last_updated : 2025.09.08
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import time
import random
from typing import Callable, Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config_daiso import CARD_ITEM

#//==============================================================================//#
# 기존 단순 함수 (하위 호환성)
#//==============================================================================//#
def scroll_pagedown(driver, n_times: int = 20, pause: float = 1.0):
    """
    PAGE_DOWN 키를 n_times만큼 눌러서 스크롤 내림
    - driver: Selenium WebDriver
    - n_times: 몇 번 내릴지
    - pause: 각 내림 사이 대기 시간 (초)
    """
    body = driver.find_element(By.TAG_NAME, "body")
    for i in range(n_times):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(pause)

#//==============================================================================//#
# DaisoScroller Class
#//==============================================================================//#
class DaisoScroller:
    """다이소 페이지 스크롤링 클래스"""
    
    def __init__(
        self,
        driver: WebDriver,
        wait_sec: int = 10,
        step_px: int = 1500,
        base_pause: float = 0.6,
        jitter: float = 0.4
    ):
        """
        초기화
        
        Args:
            driver: Selenium WebDriver
            wait_sec: 요소 대기 시간
            step_px: 스크롤 단위 (픽셀)
            base_pause: 기본 대기 시간
            jitter: 랜덤 지연 범위
        """
        self.driver = driver
        self.wait_sec = wait_sec
        self.step_px = step_px
        self.base_pause = base_pause
        self.jitter = jitter

    def _sleep(self):
        """랜덤 sleep (봇 감지 방지)"""
        time.sleep(self.base_pause + random.random() * self.jitter)

    def _doc_height(self) -> int:
        """문서 전체 높이 반환"""
        return self.driver.execute_script(
            "return document.body.scrollHeight || document.documentElement.scrollHeight;"
        )

    def _scroll_to(self, y: int):
        """지정 위치로 스크롤"""
        self.driver.execute_script(f"window.scrollTo(0, {y});")

    def _wait_items_any(self, item_selector: str) -> bool:
        """제품 카드 로딩 대기"""
        try:
            WebDriverWait(self.driver, self.wait_sec).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, item_selector))
            )
            return True
        except Exception:
            print("[Alert] 제품 요소를 찾을 수 없습니다.")
            return False

    def scroll_pagedown_simple(self, n_times: int = 5, pause: float = 1.0):
        """
        PAGE_DOWN 키를 이용한 단순 스크롤
        
        Args:
            n_times: 스크롤 횟수
            pause: 각 스크롤 사이 대기 시간
        """
        body = self.driver.find_element(By.TAG_NAME, "body")
        for i in range(n_times):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(pause)

    def scroll_until_target_count(
        self,
        target_count: int,
        product_counter: Callable[[], int],
        item_selector: str = CARD_ITEM,
        no_growth_limit: int = 3,
        max_scrolls: int = 500
    ) -> tuple[bool, int]:
        """
        목표 개수만큼 제품이 로드될 때까지 스크롤
        
        Args:
            target_count: 목표 제품 수
            product_counter: 현재 제품 수를 반환하는 함수
            item_selector: 제품 카드 셀렉터
            no_growth_limit: 증가 없이 시도할 최대 횟수
            max_scrolls: 최대 스크롤 횟수
            
        Returns:
            tuple[성공 여부, 최종 제품 수]
        """
        if not self._wait_items_any(item_selector):
            return (False, product_counter())

        no_growth_rounds = 0
        prev_doc_h = self._doc_height()
        prev_count = product_counter()

        # 초기 스크롤로 로딩 트리거
        self._scroll_to(prev_doc_h - self.step_px)
        self._sleep()

        for i in range(max_scrolls):
            current_count = product_counter()
            
            # 목표 달성 확인
            if current_count >= target_count:
                print(f"목표 달성: {current_count}/{target_count}")
                return (True, current_count)

            # 문서 끝까지 스크롤
            current_h = self._doc_height()
            next_y = current_h - 1
            self._scroll_to(next_y)
            self._sleep()

            # 로딩 대기
            self._wait_items_any(item_selector)

            # 증가 확인
            new_h = self._doc_height()
            new_count = product_counter()

            height_grew = new_h > prev_doc_h
            count_grew = new_count > prev_count

            if not height_grew and not count_grew:
                no_growth_rounds += 1
                print(f"증가 없음 ({no_growth_rounds}/{no_growth_limit})")
            else:
                no_growth_rounds = 0
                print(f"진행중: {new_count}개 (높이: {new_h})")

            prev_doc_h = max(prev_doc_h, new_h)
            prev_count = max(prev_count, new_count)

            # 더 이상 증가하지 않으면 중단
            if no_growth_rounds >= no_growth_limit:
                print("더 이상 새로운 제품을 로드할 수 없습니다.")
                break

        final_count = product_counter()
        success = final_count >= target_count
        
        print(f"스크롤 완료: {final_count}/{target_count} ({'성공' if success else '부족'})")
        return (success, final_count)

    def scroll_to_load_more(self, scroll_count: int = 5) -> int:
        """
        추가 제품 로드를 위한 스크롤
        
        Args:
            scroll_count: 스크롤 횟수
            
        Returns:
            int: 스크롤 후 제품 수
        """
        initial_count = len(self.driver.find_elements(By.CSS_SELECTOR, CARD_ITEM))
        
        for i in range(scroll_count):
            # 현재 문서 높이의 끝으로 스크롤
            doc_height = self._doc_height()
            self._scroll_to(doc_height)
            self._sleep()
            
            # 새 콘텐츠 로딩 대기
            time.sleep(1)
        
        final_count = len(self.driver.find_elements(By.CSS_SELECTOR, CARD_ITEM))
        print(f"스크롤 결과: {initial_count} → {final_count} (+{final_count - initial_count})")
        
        return final_count