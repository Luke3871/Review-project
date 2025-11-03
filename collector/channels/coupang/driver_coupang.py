#//==============================================================================//#
"""
쿠팡 크롤링용 웹드라이버 설정
- undetected_chromedriver 설정
- 브라우저 옵션 관리

last_updated : 2025.09.10
"""
#//==============================================================================//#

import random
import undetected_chromedriver as uc

#//==============================================================================//#
# 웹드라이버 생성
#//==============================================================================//#

def make_driver():
    """쿠팡 크롤링용 빠른 Chrome 드라이버 (headless + 이미지 비활성화)"""
    options = uc.ChromeOptions()

    # --- 성능 최적화 ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(options=options)
    return driver