import sys
import os

# daiso 폴더를 Python 경로에 추가
current_dir = os.path.dirname(__file__)
sys.path.append(current_dir)

from parser import DaisoProductCollector

def test_full_collection():
    with DaisoProductCollector() as collector:
        # 테스트용으로 적은 개수 수집
        products = collector.collect_products("makeup", "SALES", 2)
        
        # 각 제품의 리뷰 수집
        for product in products:
            print(f"\n리뷰 수집 시작: {product['name']}")
            reviews = collector.collect_product_reviews(
                product['url'], 
                product['name'], 
                product['product_id'],
                product['category'], 
                product['sort_type'], 
                product['rank']
            )
            
            if reviews:
                collector.save_reviews_csv(reviews, product['category'], product['sort_type'], product['name'])
                print(f"리뷰 수집 완료: {len(reviews)}개")
            else:
                print("리뷰 수집 실패")
        
        # 제품 CSV 저장
        collector.save_products_csv(products, "makeup", "SALES")
        print(f"\n전체 테스트 완료: {len(products)}개 제품 및 리뷰 수집")

if __name__ == "__main__":
    test_full_collection()