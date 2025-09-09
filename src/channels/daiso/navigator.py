#//==============================================================================//#
"""
url 진입
페이지내 이동
dropdown box 클릭
sorting option select
상품 페이지 돌입 및 종료


option - daiso
last_updated : 2025.08.30
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import sys
import os

from .config_daiso import CARD_ITEM, DROPDOWN_BUTTON, DROPDOWN_OPTION

from typing import Dict
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
import time

#//==============================================================================//#
# Daiso, navigator
#//==============================================================================//#

class DaisoNavigator:
    def __init__(self, driver, wait_sec: int = 10):
        self.driver = driver
        self.wait_sec = wait_sec

    def goto_category(self, url: str):
        self.driver.get(url)
        self.wait_cards()

    def open_sort_dropdown(self) -> bool:
        try:
            btn = W(self.driver, self.wait_sec).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, DROPDOWN_BUTTON))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            return False

    def click_sort_option(self, label_text: str) -> bool:
        opts = W(self.driver, self.wait_sec).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
        )
        for o in opts:
            txt = o.text.strip().replace(" ", "").replace("\u200b", "")
            if txt == label_text.replace(" ", "").replace("\u200b", ""):
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", o)
                try:
                    o.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", o)
                return True
        return False

    def wait_cards(self):
        # 리스트 로딩 트리거
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
        time.sleep(0.5)
        self.driver.execute_script("window.scrollTo(0, 0);")

        W(self.driver, self.wait_sec).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, CARD_ITEM))
        )

