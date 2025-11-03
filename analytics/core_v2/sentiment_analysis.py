#//==============================================================================//#
"""
sentiment_analysis.py
감성 분석 + ABSA (Aspect-Based Sentiment Analysis)

last_updated: 2025.10.16
"""
#//==============================================================================//#

import sys
import os

current_file = os.path.abspath(__file__)
analytics_dir = os.path.dirname(os.path.dirname(current_file))

if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from transformers import pipeline

# 토크나이저 import
utils_path = os.path.join(analytics_dir, 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

from utils.tokenizer import get_tokenizer_for_channel

#//==============================================================================//#
# 카테고리별 속성 정의
#//==============================================================================//#

CATEGORY_ASPECTS = {
    # 스킨케어 그룹
    'skincare': {
        '보습': ['보습', '촉촉', '수분', '건조', '유수분', '보습력', '보습감'],
        '흡수': ['흡수', '스며', '침투', '배어', '흡수력'],
        '발림성': ['발림', '텍스처', '펴발림', '발리', '제형'],
        '자극': ['자극', '따갑', '트러블', '붉어', '알러지', '민감', '각질'],
        '끈적임': ['끈적', '번들', '무거', '답답'],
        '진정': ['진정', '수딩', '쿨링', '시원', '완화'],
        '향': ['향', '냄새', '향기', '무향', '향료'],
        '가격': ['가격', '가성비', '비싸', '저렴', '가심비']
    },
    
    # 베이스 메이크업
    'base_makeup': {
        '발림성': ['발림', '텍스처', '펴발림', '밀림'],
        '커버력': ['커버', '가림', '커버력', '커버감', '보정'],
        '지속력': ['지속', '오래', '무너짐', '유지', '번짐'],
        '톤': ['톤업', '화사', '밝', '백탁', '회색'],
        '밀착력': ['밀착', '들뜸', '각질', '쪼개짐'],
        '광': ['광', '윤광', '촉촉', '매트', '세미'],
        '향': ['향', '냄새'],
        '가격': ['가격', '가성비', '비싸', '저렴']
    },
    
    # 립 메이크업
    'lip_makeup': {
        '발색': ['발색', '색감', '컬러', '색상', '진하'],
        '지속력': ['지속', '오래', '번짐', '유지', '안지워'],
        '보습': ['보습', '촉촉', '건조', '당김'],
        '발림성': ['발림', '텍스처', '펴발림', '뭉침'],
        '광': ['광', '매트', '글로시', '벨벳', '세미'],
        '향': ['향', '냄새', '민트향'],
        '틴트': ['물들임', '착색', '틴트', '입술'],
        '가격': ['가격', '가성비']
    },
    
    # 아이 메이크업
    'eye_makeup': {
        '발색': ['발색', '색감', '컬러', '진하'],
        '지속력': ['지속', '번짐', '펴짐', '날림', '뭉침'],
        '밀착력': ['밀착', '들뜸', '눈꺼풀'],
        '펄': ['펄', '글리터', '반짝', '시머'],
        '그라데이션': ['그라데이션', '블렌딩', '번짐'],
        '발림성': ['발림', '텍스처', '펴발림'],
        '자극': ['자극', '따갑', '눈물', '눈'],
        '가격': ['가격', '가성비']
    }
}

# 카테고리 매핑
CATEGORY_MAPPING = {
    'skincare': 'skincare',
    '스킨케어': 'skincare',
    '크림/올인원': 'skincare',
    '마스크/팩': 'skincare',
    '선케어': 'skincare',
    
    'makeup': 'base_makeup',
    '베이스 메이크업': 'base_makeup',
    '베이스/프라이머': 'base_makeup',
    
    '립 메이크업': 'lip_makeup',
    
    '아이 메이크업': 'eye_makeup'
}

def get_aspects_by_category(category: str) -> Dict:
    """
    카테고리에 맞는 속성 반환
    
    Args:
        category: 제품 카테고리
    
    Returns:
        속성 딕셔너리
    """
    mapped_category = CATEGORY_MAPPING.get(category)
    
    if mapped_category:
        return CATEGORY_ASPECTS[mapped_category]
    
    # 기본값 (스킨케어)
    return CATEGORY_ASPECTS['skincare']

#//==============================================================================//#
# Sentiment Analyzer
#//==============================================================================//#

class SentimentAnalyzer:
    """
    감성 분석기 (사전학습 모델 사용)
    """
    
    def __init__(self, model_name: str = "beomi/kcbert-base"):
        """
        초기화
        
        Args:
            model_name: 한국어 감성 분석 모델
        """
        self.model_name = model_name
        self.model = None  # Lazy Loading
    
    def _load_model(self):
        """모델 로드 (첫 사용 시 한 번만)"""
        if self.model is None:
            try:
                print(f"감성 분석 모델 로딩 중... ({self.model_name})")
                self.model = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    tokenizer=self.model_name
                )
                print("모델 로딩 완료!")
            except Exception as e:
                print(f"모델 로드 실패: {e}")
                self.model = None
    
    def analyze(self, text: str) -> Dict:
        """
        단일 텍스트 감성 분석
        
        Args:
            text: 리뷰 텍스트
        
        Returns:
            {'label': 'positive/negative', 'score': 0.95}
        """
        
        self._load_model()
        
        if self.model is None:
            return {'label': 'unknown', 'score': 0.5}
        
        try:
            result = self.model(text[:512])  # 최대 길이 제한
            return result[0]
        except Exception as e:
            print(f"감성 분석 실패: {e}")
            return {'label': 'unknown', 'score': 0.5}
    
    def analyze_batch(
        self,
        df: pd.DataFrame,
        text_column: str = 'review_text'
    ) -> pd.DataFrame:
        """
        배치 감성 분석
        
        Args:
            df: 리뷰 DataFrame
            text_column: 텍스트 컬럼명
        
        Returns:
            감성 분석 결과가 추가된 DataFrame
            - overall_label: positive/negative
            - overall_score: 0~1
        """
        
        if df.empty:
            return df
        
        self._load_model()
        
        df = df.copy()
        
        # 배치 감성 분석
        texts = df[text_column].fillna('').astype(str).tolist()
        
        labels = []
        scores = []
        
        # 배치 처리 (효율적)
        try:
            results = self.model(texts)
            for result in results:
                labels.append(result['label'])
                scores.append(result['score'])
        except:
            # 배치 실패 시 하나씩
            for text in texts:
                result = self.analyze(text)
                labels.append(result['label'])
                scores.append(result['score'])
        
        df['overall_label'] = labels
        df['overall_score'] = scores
        
        return df
    
    def close(self):
        """메모리 해제"""
        if self.model is not None:
            del self.model
            self.model = None
            import gc
            gc.collect()

#//==============================================================================//#
# ABSA (Aspect-Based Sentiment Analysis)
#//==============================================================================//#

class ABSAAnalyzer:
    """
    속성 기반 감성 분석
    """
    
    def __init__(
        self, 
        category: str = 'skincare',
        channel: str = 'OliveYoung',
        model_name: str = "beomi/kcbert-base"
    ):
        """
        초기화
        
        Args:
            category: 제품 카테고리
            channel: 채널명 (토크나이저 선택용)
            model_name: 감성 분석 모델
        """
        self.category = category
        self.channel = channel
        self.aspects = get_aspects_by_category(category)
        self.sentiment_analyzer = SentimentAnalyzer(model_name)
        self.tokenizer = get_tokenizer_for_channel(channel)  # ← 토크나이저 추가
    
    def extract_mentioned_aspects(self, text: str) -> List[str]:
        """
        텍스트에서 언급된 속성 추출 (토크나이저 사용)
        
        Args:
            text: 리뷰 텍스트
        
        Returns:
            언급된 속성 리스트
        """
        
        # 토큰화
        tokens = self.tokenizer(text)  # ← 토크나이저 사용
        
        mentioned = []
        
        for aspect, keywords in self.aspects.items():
            for keyword in keywords:
                if keyword in tokens:  # ← 토큰 리스트에서 찾기
                    mentioned.append(aspect)
                    break
        
        return mentioned
    
    def analyze_aspect_sentiment(
        self,
        text: str,
        aspect: str,
        context_window: int = 50
    ) -> Optional[Dict]:
        """
        특정 속성에 대한 감성 분석
        
        Args:
            text: 리뷰 텍스트
            aspect: 속성명
            context_window: 전후 컨텍스트 글자 수
        
        Returns:
            {
                'aspect': '보습',
                'sentiment': 'positive',
                'score': 0.9,
                'context': '...'
            }
        """
        
        if aspect not in self.aspects:
            return None
        
        keywords = self.aspects[aspect]
        
        # 속성 키워드 위치 찾기 (원문에서)
        for keyword in keywords:
            if keyword in text:  # 원문에서 찾기 (위치 확인용)
                idx = text.find(keyword)
                
                # 컨텍스트 추출
                start = max(0, idx - context_window)
                end = min(len(text), idx + len(keyword) + context_window)
                context = text[start:end]
                
                # 컨텍스트에 대한 감성 분석
                sentiment_result = self.sentiment_analyzer.analyze(context)
                
                return {
                    'aspect': aspect,
                    'sentiment': sentiment_result['label'],
                    'score': sentiment_result['score'],
                    'context': context,
                    'keyword': keyword
                }
        
        return None
    
    def analyze_review(self, text: str) -> List[Dict]:
        """
        리뷰 전체에 대한 ABSA
        
        Args:
            text: 리뷰 텍스트
        
        Returns:
            속성별 감성 분석 결과 리스트
        """
        
        # 1단계: 언급된 속성 추출 (토큰화로 정확하게)
        mentioned_aspects = self.extract_mentioned_aspects(text)
        
        if not mentioned_aspects:
            return []
        
        # 2단계: 언급된 속성만 감성 분석
        results = []
        for aspect in mentioned_aspects:
            aspect_result = self.analyze_aspect_sentiment(text, aspect)
            if aspect_result:
                results.append(aspect_result)
        
        return results
    
    def analyze_batch(
        self,
        df: pd.DataFrame,
        text_column: str = 'review_text'
    ) -> pd.DataFrame:
        """
        배치 ABSA
        
        Args:
            df: 리뷰 DataFrame
            text_column: 텍스트 컬럼명
        
        Returns:
            ABSA 결과가 추가된 DataFrame
            - aspect_{속성명}: positive/negative/None
            - absa_details: 상세 정보 JSON
        """
        
        if df.empty:
            return df
        
        df = df.copy()
        
        # 각 리뷰에 대해 ABSA 실행
        absa_results = []
        
        for text in df[text_column]:
            results = self.analyze_review(text)
            absa_results.append(results)
        
        df['absa_details'] = absa_results
        
        # 속성별 컬럼 추가
        for aspect in self.aspects.keys():
            df[f'aspect_{aspect}'] = df['absa_details'].apply(
                lambda x: next(
                    (r['sentiment'] for r in x if r['aspect'] == aspect), 
                    None
                )
            )
        
        return df
    
    def close(self):
        """메모리 해제"""
        self.sentiment_analyzer.close()

#//==============================================================================//#
# Aggregate Functions
#//==============================================================================//#

def analyze_brand_aspect_sentiment(
    df: pd.DataFrame,
    brand: str,
    aspect: str,
    category: str = 'skincare',
    channel: str = 'OliveYoung'
) -> Dict:
    """
    브랜드의 특정 속성에 대한 감성 분석 집계
    
    Args:
        df: 리뷰 DataFrame
        brand: 브랜드명
        aspect: 속성명
        category: 제품 카테고리
        channel: 채널명
    
    Returns:
        집계 결과
    """
    
    # 브랜드 필터
    brand_df = df[df['brand'] == brand].copy()
    
    if brand_df.empty:
        return {'error': '데이터 없음'}
    
    # ABSA 실행
    absa = ABSAAnalyzer(category=category, channel=channel)
    brand_df = absa.analyze_batch(brand_df)
    
    # 해당 속성 언급한 리뷰만
    aspect_col = f'aspect_{aspect}'
    if aspect_col not in brand_df.columns:
        return {'error': f'{aspect} 속성 데이터 없음'}
    
    aspect_df = brand_df[brand_df[aspect_col].notna()]
    
    if aspect_df.empty:
        return {'error': f'{aspect} 언급 없음'}
    
    # 집계
    total = len(aspect_df)
    positive = (aspect_df[aspect_col] == 'positive').sum()
    negative = (aspect_df[aspect_col] == 'negative').sum()
    
    return {
        'brand': brand,
        'aspect': aspect,
        'total_mentions': total,
        'positive_count': positive,
        'negative_count': negative,
        'positive_ratio': positive / total if total > 0 else 0,
        'negative_ratio': negative / total if total > 0 else 0,
        'sample_reviews': aspect_df.head(5)['review_text'].tolist()
    }


def compare_brands_on_aspect(
    df: pd.DataFrame,
    brands: List[str],
    aspect: str,
    category: str = 'skincare',
    channel: str = 'OliveYoung'
) -> Dict:
    """
    여러 브랜드의 특정 속성 비교
    
    Args:
        df: 리뷰 DataFrame
        brands: 브랜드 리스트
        aspect: 속성명
        category: 제품 카테고리
        channel: 채널명
    
    Returns:
        비교 결과
    """
    
    results = {}
    
    for brand in brands:
        result = analyze_brand_aspect_sentiment(df, brand, aspect, category, channel)
        if 'error' not in result:
            results[brand] = result
    
    return results


def get_overall_sentiment_stats(df: pd.DataFrame) -> Dict:
    """
    전체 감성 통계
    
    Args:
        df: 감성 분석이 완료된 DataFrame
    
    Returns:
        통계 결과
    """
    
    if 'overall_label' not in df.columns:
        return {'error': '감성 분석 필요'}
    
    total = len(df)
    positive = (df['overall_label'] == 'positive').sum()
    negative = (df['overall_label'] == 'negative').sum()
    
    return {
        'total_reviews': total,
        'positive_count': positive,
        'negative_count': negative,
        'positive_ratio': positive / total if total > 0 else 0,
        'negative_ratio': negative / total if total > 0 else 0,
        'avg_score': df['overall_score'].mean() if 'overall_score' in df.columns else None
    }