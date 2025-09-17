
"""간단한 전처리 테스트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_preprocessor import DataPreprocessor
from data_loader_preprocessor import DataLoader



def main():
    print("전처리 테스트 시작")
    
    # 1. 데이터 로딩
    loader = DataLoader('daiso')
    print(f"사용 가능한 파일: {len(loader.get_available_files())}개")
    
    df = loader.load_all_files()
    print(f"로딩된 데이터: {len(df)}개 리뷰")
    
    # 2. 전처리
    cleaner = DataPreprocessor()
    cleaned_df = cleaner.clean_dataframe(df)
    print(f"전처리 후: {len(cleaned_df)}개 리뷰")
    
    # 3. 저장 테스트
    cleaner.clean_and_save(df, 'daiso', 'test_processed.csv')
    print("저장 완료")
    
    # 4. 결과 확인
    print(f"새 컬럼들: {list(set(cleaned_df.columns) - set(df.columns))}")


if __name__ == "__main__":
    main()