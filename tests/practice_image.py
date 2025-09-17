#!/usr/bin/env python3
"""
다이소 리뷰 간단 테스트
- 제품 하나, 한 페이지만 크롤링
- 기존 코드 그대로 활용
- 이미지와 도움됨 수만 추가
"""

import os
import time
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 기존 모듈 import
from driver import make_driver, close_driver, DriverConfig
from config_daiso import (
    REVIEWER_NAME, REVIEW_RATING, REVIEW_DATE, REVIEW_CONTENT, REVIEW_BUTTON
)

def test_single_product():
    """단일 제품 리뷰 테스트"""
    
    # 테스트할 제품 URL
    test_url = "https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1061153"
    
    driver_config = DriverConfig(headless=False, window_size="1920,1080")
    driver = make_driver(driver_config)
    
    try:
        print("=== 다이소 리뷰 테스트 시작 ===")
        
        # 제품 페이지 이동
        driver.get(test_url)
        time.sleep(3)
        
        # 제품명 추출 (기존 방식 유지)
        try:
            product_name = driver.find_element(By.CSS_SELECTOR, "h3.tit").text.strip()
            print(f"제품명: {product_name}")
        except:
            product_name = "제품명_추출실패"
        
        # 리뷰 버튼 클릭 (기존 config 사용)
        try:
            review_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, REVIEW_BUTTON))
            )
            review_button.click()
            time.sleep(3)
        except Exception as e:
            print(f"리뷰 버튼 클릭 실패: {e}")
            return
        
        # 기존 방식으로 파싱
        doc = BeautifulSoup(driver.page_source, "html.parser")
        
        # 기존 crawler.py 방식 그대로
        reviewer_names = [n.text.strip() if n and n.text.strip() else None 
                         for n in doc.find_all("span", class_="name")]
        
        review_stars = [s.text.strip() if s and s.text.strip() else None 
                       for s in doc.find_all("span", class_="score")]
        
        review_dates = [d.text.strip() if d and d.text.strip() else None 
                       for d in doc.find_all(class_='review-date')]
        
        review_contents = [r.text.strip() if r and r.text.strip() else None 
                          for r in doc.find_all(class_='cont')]
        
        # 도움됨 수 (스크린샷에서 확인한 class="num")
        helpful_counts = [h.text.strip() if h and h.text.strip() else "0"
                         for h in doc.find_all("span", class_="num")]
        
        print(f"추출된 데이터: 이름{len(reviewer_names)}, 별점{len(review_stars)}, 날짜{len(review_dates)}, 내용{len(review_contents)}, 도움됨{len(helpful_counts)}")
        
        # 최소 개수로 맞춤
        min_length = min(len(reviewer_names), len(review_stars), 
                        len(review_dates), len(review_contents))
        
        if min_length == 0:
            print("리뷰를 찾을 수 없습니다.")
            return
        
        # 이미지 폴더 생성
        os.makedirs("test_images", exist_ok=True)
        
        # 리뷰 데이터 생성
        reviews = []
        for i in range(min_length):
            
            print(f"리뷰 {i+1} 처리 중...")
            
            # 이미지 처리
            try:
                image_info = check_images(doc, i)
                print(f"이미지 정보: {image_info}")
            except Exception as e:
                print(f"이미지 처리 오류: {e}")
                image_info = {
                    'has_images': False,
                    'count': 0,
                    'files': []
                }
            
            review = {
                'product_name': product_name,
                'reviewer_name': reviewer_names[i],
                'rating': review_stars[i],
                'review_date': review_dates[i],
                'review_text': review_contents[i],
                'helpful_count': helpful_counts[i] if i < len(helpful_counts) else "0",
                'has_images': image_info.get('has_images', False),
                'image_count': image_info.get('count', 0),
                'image_files': ','.join(image_info.get('files', []))
            }
            reviews.append(review)
        
        # 결과 출력
        print(f"\n=== 수집 완료: {len(reviews)}개 리뷰 ===")
        for i, review in enumerate(reviews):
            print(f"[{i+1}] {review['reviewer_name']} | {review['rating']} | 도움됨:{review['helpful_count']} | 이미지:{review['has_images']}")
        
        # CSV 저장
        df = pd.DataFrame(reviews)
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', product_name)[:30]
        filename = f"test_{safe_name}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n저장완료: {filename}")
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        close_driver(driver)

def check_images(doc, review_index):
    """리뷰 이미지 확인 및 다운로드"""
    
    print(f"이미지 확인 시작 - 리뷰 인덱스: {review_index}")
    
    # swiper-slide 클래스 찾기
    swiper_slides = doc.find_all('div', class_='swiper-slide')
    print(f"찾은 swiper-slide 개수: {len(swiper_slides)}")
    
    if not swiper_slides:
        print("swiper-slide를 찾을 수 없습니다.")
        return {
            'has_images': False,
            'count': 0,
            'urls': [],
            'files': []
        }
    
    image_urls = []
    downloaded_files = []
    
    for slide in swiper_slides:
        img = slide.find('img')
        if img and img.get('src'):
            image_urls.append(img.get('src'))
    
    print(f"찾은 이미지 URL 개수: {len(image_urls)}")
    
    # 이미지 다운로드
    for i, img_url in enumerate(image_urls[:5]):  # 최대 5개
        try:
            print(f"이미지 다운로드 시도: {img_url}")
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                # 확장자 결정
                ext = 'jpg'
                if '.' in img_url:
                    url_ext = img_url.split('.')[-1].split('?')[0].lower()
                    if url_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        ext = url_ext
                
                # 파일명 생성
                filename = f"review_{review_index}_img_{i+1}.{ext}"
                filepath = os.path.join("test_images", filename)
                
                # 파일 저장
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                downloaded_files.append(filename)
                print(f"이미지 다운로드 성공: {filename}")
                
        except Exception as e:
            print(f"이미지 다운로드 실패 {img_url}: {e}")
            continue
    
    return {
        'has_images': len(image_urls) > 0,
        'count': len(image_urls),
        'urls': image_urls,
        'files': downloaded_files
    }

if __name__ == "__main__":
    test_single_product()