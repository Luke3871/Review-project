#//==============================================================================//#
"""
raw_data 로딩 모듈

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import pandas as pd
import glob
import os
from config_preprocessor import CHANNEL_CONFIGS
#//==============================================================================//#

#//==============================================================================//#
# Data loader
#//==============================================================================//#

class DataLoader:

    # 설정 초기화

    def __init__(self, channel_name):
        if channel_name not in CHANNEL_CONFIGS:
            raise ValueError(f"채널이 존재하지 않습니다. : {channel_name}")
        
        self.channel_name = channel_name
        self.config = CHANNEL_CONFIGS[channel_name]

    def load_all_files(self):
        raw_path = self.config['raw_data_path']
        file_pattern = self.config['file_pattern']

        csv_files = glob.glob(os.path.join(raw_path, file_pattern))

        if not csv_files:
            print(f"{raw_path}에서 파일을 찾을 수 없습니다.")
            return pd.DataFrame
        
        all_dataframes = []

        for file_path in csv_files:
            df = self._load_single_file(file_path)
            if not df.empty:
                df['source_file'] = os.path.basename(file_path)
                all_dataframes.append(df)

        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index= True)
            combined_df['channel'] = self.channel_name
            print(f"{self.config['name']}: {len(csv_files)}개 파일, {len(combined_df)}개 리뷰 로딩 완료")
            return combined_df
        
        return pd.DataFrame()

    # 특정 제품 파일 로딩
    def load_single_product(self, file_name):
        file_path = os.path.join(self.config['raw_data_path'], file_name)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        df = self._load_single_file(file_path)
        if not df.empty:
            df['source_file'] = file_name
            df['channel'] = self.channel_name

    # 현재 사용 가능한 파일 목록
    def get_available_files(self):
        raw_path = self.config['raw_data_path']
        file_pattern = self.config['file_pattern']
        
        csv_files = glob.glob(os.path.join(raw_path, file_pattern))
        return [os.path.basename(f) for f in csv_files]

    # 단일 파일 로딩 (제품 하나하나...)
    def _load_single_file(self, file_path):
        for encoding in self.config['encoding']:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"파일 읽기 실패: {file_path} - {e}")
                break
        
        print(f"모든 파일 로딩 실패: {file_path}")
        return pd.DataFrame()