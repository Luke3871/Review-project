from data_loader_preprocessor import DataLoader
from config_preprocessor import CHANNEL_CONFIGS, PREPROCESSING_CONFIG
from main_preprocessor import DataPreprocessor

__all__ = ['DataLoader', 'TextCleaner', 'CHANNEL_CONFIGS', 'PREPROCESSING_CONFIG']


if __name__ == "__main__":

    loader = DataLoader("daiso")
    df = loader.load_all_files()

    cleaner = DataPreprocessor()
    df_cleaned = cleaner.clean_dataframe(df)


    print(f"최종 결과: {len(df_cleaned)}개 리뷰")
    print(f"컬럼: {list(df_cleaned.columns)}")