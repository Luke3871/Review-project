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
    
    # User-Agent 랜덤 설정
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]
    options.add_argument('user-agent=' + random.choice(user_agents))
    
    return uc.Chrome(options=options)