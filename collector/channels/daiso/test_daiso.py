import pandas as pd
from parser import DaisoProductCollector
from driver import DriverConfig

# 설정
DRIVER_CONFIG = DriverConfig(headless=False)

# 누락된 제품 정보
missing_product = {
    'url': 'https://www.daisomall.co.kr/pd/pdr/SCR_PDR_0001?pdNo=1049301',
    'name': 'VT 시카 카밍 마스크팩 4매입',
    'product_id': '1049301',  # URL에서 추출
    'category': 'skincare',
    'sort_type': 'SALES',
    'rank': 94
}

def crawl_single_product():
    with DaisoProductCollector(DRIVER_CONFIG) as collector:
        print(f"=== 누락 제품 리뷰 수집 ===")
        print(f"제품명: {missing_product['name']}")
        print(f"순위: {missing_product['rank']}위")
        print(f"URL: {missing_product['url']}\n")
        
        reviews = collector.collect_product_reviews(
            missing_product['url'],
            missing_product['name'],
            missing_product['product_id'],
            missing_product['category'],
            missing_product['sort_type'],
            missing_product['rank']
        )
        
        if reviews:
            collector.save_reviews_csv(
                reviews, 
                missing_product['category'], 
                missing_product['sort_type'], 
                missing_product['name']
            )
            print(f"\n✅ 완료!")
            print(f"   - 리뷰: {len(reviews)}개")

        else:
            print("\n❌ 리뷰 없음 또는 수집 실패")

if __name__ == "__main__":
    crawl_single_product()