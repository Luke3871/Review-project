#//==============================================================================//#
"""
selenium driver set up
chrome driver set up
drvier start and close

option - daiso
last_updated : 2025.09.03
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
from typing import Optional

#//==============================================================================//#
# driver option set up
# 브라우저 실행 옵션을 설정 객체로 관리
#//==============================================================================//#

@dataclass
class DriverConfig:
    headless: bool = True
    window_size: str = "1920,1080"
    page_load_timeout: int = 30          
    script_timeout: int = 30             
    implicit_wait: float = 0.0           
    user_agent: Optional[str] = None     
    accept_language: str = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    sandboxless: bool = True

#//==============================================================================//#
# chrome options set up
#//==============================================================================//#
def _make_chrome_options(cfg: DriverConfig) -> Options:
    opts = Options()

    if cfg.headless:
        opts.add_argument("--headless=new")

    if cfg.sandboxless:
        opts.add_argument("--no-sandbox")

    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={cfg.window_size}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-infobars")
    opts.add_argument(f"--lang={cfg.accept_language}")

    if cfg.user_agent:
        opts.add_argument(f"--user-agent={cfg.user_agent}")

    return opts

#//==============================================================================//#
# create chrome instance
#//==============================================================================//#
def make_driver(cfg: DriverConfig= DriverConfig()) -> webdriver.Chrome:
    
    # driver config의 설정을 받아 드라이버의 옵션 설정
    options = _make_chrome_options(cfg)
    service= Service(ChromeDriverManager().install())

    # 드라이버 생성
    driver = webdriver.Chrome(service= service, options= options)


    driver.set_page_load_timeout(cfg.page_load_timeout)
    driver.set_script_timeout(cfg.script_timeout)
    driver.implicitly_wait(cfg.implicit_wait)

    return driver

#//==============================================================================//#
# close driver
#//==============================================================================//#
def close_driver(driver: webdriver.Chrome):
    try:
        driver.quit()
    except Exception:
        pass
