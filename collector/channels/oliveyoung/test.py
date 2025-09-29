#//==============================================================================//#
"""
올리브영 크롤러 제작을 위한 test 파일

option - oliveyoung
last_updated : 2025.09.14
"""
#//==============================================================================//#

import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By

# 카테고리 URL
SKINCARE_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_스킨케어"
MAKEUP_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010002&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_메이크업"

def test_manual():
    driver = uc.Chrome()
    
    try:
        print("수동 테스트 모드")
        print("브라우저가 열린 상태로 유지됩니다.")
        print("개발자 도구로 요소를 확인하세요.")
        
        # 스킨케어 랭킹 페이지 접근
        driver.get(SKINCARE_URL)
        time.sleep(3)
        
        # 브라우저를 열어둔 상태로 대기
        while True:
            command = input("\n명령어 입력 (find/click/back/makeup/quit): ").strip().lower()
            
            if command == "quit":
                break
            elif command == "find":
                selector = input("CSS 선택자 입력: ")
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"찾은 요소 수: {len(elements)}")
                except Exception as e:
                    print(f"오류: {e}")
            elif command == "click":
                selector = input("클릭할 요소의 CSS 선택자: ")
                index = int(input("몇 번째 요소? (0부터 시작): "))
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if index < len(elements):
                        elements[index].click()
                        time.sleep(3)
                        print(f"페이지 제목: {driver.title}")
                    else:
                        print("해당 인덱스의 요소가 없음")
                except Exception as e:
                    print(f"클릭 오류: {e}")
            elif command == "back":
                driver.back()
                time.sleep(2)
                print("뒤로가기 완료")
            elif command == "makeup":
                driver.get(MAKEUP_URL)
                time.sleep(3)
                print("메이크업 페이지로 이동")
            else:
                print("사용 가능한 명령어: find, click, back, makeup, quit")
        
    except Exception as e:
        print(f"오류: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_manual()