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
    """쿠팡 크롤링에 최적화된 Chrome 드라이버 생성"""
    options = uc.ChromeOptions()
    
    # 자동화 감지 방지 설정
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return uc.Chrome(options=options)