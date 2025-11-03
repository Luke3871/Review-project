#//==============================================================================//#
"""
cohort_analysis.py
코호트 분석 (피부타입별 분석 - 올리브영 전용)

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
from collections import Counter

# sentiment_analysis import
from .sentiment_analysis import ABSAAnalyzer, get_aspects_by_category

# keyword_extraction import
from .keyword_analysis import KeywordExtractor

#//==============================================================================//#
# 피부 정보 매핑
#//==============================================================================//#

SKIN_TYPES = {
    '지성': ['지성'],
    '건성': ['건성'],
    '복합성': ['복합성'],
    '민감성': ['민감성'],
    '약건성': ['약건성'],
    '트러블성': ['트러블성'],
    '중성': ['중성']
}

SKIN_CONCERNS = [
    '잡티', '미백', '주름', '각질', '트러블', '블랙헤드',
    '피지과다', '민감성', '모공', '탄력', '홍조', '아토피', '다크서클'
]

# 최소 데이터 수
MIN_REVIEWS_FOR_ANALYSIS = 30
MIN_REVIEWS_PER_TYPE = 10

#//==============================================================================//#
# 데이터 가용성 체크
#//==============================================================================//#

def check_cohort_data_availability(
    df: pd.DataFrame,
    brand: Optional[str] = None,
    product: Optional[str] = None
) -> Dict:
    """
    코호트 분석 가능 여부 확인
    
    Args:
        df: 리뷰 DataFrame
        brand: 브랜드명 (Optional)
        product: 제품명 (Optional)
    
    Returns:
        {
            'total_reviews': int,
            'oliveyoung_reviews': int,
            'with_skin_type': int,
            'with_skin_concerns': int,
            'analyzable': bool,
            'by_skin_type': {...},
            'recommendations': [...]
        }
    """
    
    # 필터링
    if brand:
        df = df[df['brand'] == brand]
    if product:
        df = df[df['product_name'] == product]
    
    total = len(df)
    
    # 올리브영만
    oy_df = df[df['channel'] == 'OliveYoung']
    oy_count = len(oy_df)
    
    # skin_features 있는 리뷰
    with_skin = oy_df[oy_df['skin_features'].notna()]
    skin_count = len(with_skin)
    
    # skin_concerns 있는 리뷰
    with_concerns = oy_df[oy_df['skin_concerns'].notna()]
    concerns_count = len(with_concerns)
    
    # 피부타입별 분포
    skin_type_dist = {}
    if skin_count > 0:
        for skin_type in SKIN_TYPES.keys():
            count = with_skin[
                with_skin['skin_features'].str.contains(skin_type, na=False)
            ].shape[0]
            skin_type_dist[skin_type] = count
    
    # 분석 가능 여부
    analyzable = skin_count >= MIN_REVIEWS_FOR_ANALYSIS
    
    # 추천 사항
    recommendations = []
    
    if not analyzable:
        recommendations.append(
            f"피부타입 데이터 부족 (최소 {MIN_REVIEWS_FOR_ANALYSIS}개 필요, 현재 {skin_count}개)"
        )
    else:
        # 데이터 부족한 피부타입
        insufficient = [
            skin_type for skin_type, count in skin_type_dist.items() 
            if count < MIN_REVIEWS_PER_TYPE
        ]
        if insufficient:
            recommendations.append(
                f"데이터 부족한 피부타입: {', '.join(insufficient)}"
            )
        
        # 분석 가능한 피부타입
        sufficient = [
            skin_type for skin_type, count in skin_type_dist.items() 
            if count >= MIN_REVIEWS_PER_TYPE
        ]
        if sufficient:
            recommendations.append(
                f"분석 가능한 피부타입: {', '.join(sufficient)}"
            )
    
    if oy_count == 0:
        recommendations.append("올리브영 채널 데이터 없음")
    
    return {
        'total_reviews': total,
        'oliveyoung_reviews': oy_count,
        'with_skin_type': skin_count,
        'with_skin_concerns': concerns_count,
        'coverage_rate': skin_count / oy_count if oy_count > 0 else 0,
        'analyzable': analyzable,
        'by_skin_type': skin_type_dist,
        'recommendations': recommendations
    }

#//==============================================================================//#
# 피부타입별 분석
#//==============================================================================//#

def analyze_by_skin_type(
    df: pd.DataFrame,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    category: str = 'skincare',
    min_reviews: int = MIN_REVIEWS_PER_TYPE
) -> Dict:
    """
    피부타입별 분석
    
    Args:
        df: 리뷰 DataFrame
        brand: 브랜드명
        product: 제품명
        category: 제품 카테고리
        min_reviews: 피부타입당 최소 리뷰 수
    
    Returns:
        {
            'data_summary': {...},
            'by_skin_type': {
                '지성': {
                    'count': int,
                    'overall_positive_ratio': float,
                    'aspects': {...},
                    'keywords': [...]
                }
            },
            'insights': [...]
        }
    """
    
    # 필터링
    if brand:
        df = df[df['brand'] == brand]
    if product:
        df = df[df['product_name'] == product]
    
    # 올리브영 + skin_features 있는 리뷰만
    df = df[
        (df['channel'] == 'OliveYoung') & 
        (df['skin_features'].notna())
    ].copy()
    
    if len(df) < MIN_REVIEWS_FOR_ANALYSIS:
        return {
            'error': '분석 가능한 데이터 부족',
            'available_count': len(df),
            'required_count': MIN_REVIEWS_FOR_ANALYSIS
        }
    
    # ABSA 준비
    absa = ABSAAnalyzer(category=category, channel='OliveYoung')
    
    # 감성 분석 (아직 안 되어 있으면)
    if 'overall_label' not in df.columns:
        from .sentiment_analysis import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
        df = sentiment_analyzer.analyze_batch(df)
    
    # ABSA (아직 안 되어 있으면)
    if 'absa_details' not in df.columns:
        df = absa.analyze_batch(df)
    
    # 피부타입별 분석
    results = {}
    
    for skin_type in SKIN_TYPES.keys():
        # 해당 피부타입 필터
        skin_df = df[df['skin_features'].str.contains(skin_type, na=False)]
        
        if len(skin_df) < min_reviews:
            continue
        
        # 전체 감성
        positive_ratio = (skin_df['overall_label'] == 'positive').mean()
        
        # 속성별 감성
        aspects = absa.aspects
        aspect_sentiments = {}
        
        for aspect in aspects.keys():
            aspect_col = f'aspect_{aspect}'
            if aspect_col in skin_df.columns:
                aspect_df = skin_df[skin_df[aspect_col].notna()]
                if len(aspect_df) > 0:
                    positive = (aspect_df[aspect_col] == 'positive').sum()
                    total = len(aspect_df)
                    aspect_sentiments[aspect] = positive / total
        
        # 키워드 추출
        extractor = KeywordExtractor(channel='OliveYoung')
        texts = skin_df['review_text'].tolist()
        keyword_result = extractor.extract(texts, top_n=10)
        keywords = [kw['word'] for kw in keyword_result['keywords']]
        
        results[skin_type] = {
            'count': len(skin_df),
            'overall_positive_ratio': float(positive_ratio),
            'aspects': aspect_sentiments,
            'keywords': keywords
        }
    
    # 인사이트 생성
    insights = _generate_insights(results, category)
    
    return {
        'data_summary': {
            'total_analyzed': len(df),
            'skin_types_analyzed': len(results),
            'coverage': f"{len(df) / len(df[df['channel'] == 'OliveYoung']) * 100:.1f}%"
        },
        'by_skin_type': results,
        'insights': insights
    }

#//==============================================================================//#
# 피부 고민별 분석
#//==============================================================================//#

def analyze_by_skin_concern(
    df: pd.DataFrame,
    concern: str,
    brand: Optional[str] = None,
    product: Optional[str] = None,
    category: str = 'skincare'
) -> Dict:
    """
    특정 피부 고민 가진 사람들의 평가
    
    Args:
        df: 리뷰 DataFrame
        concern: 피부 고민 ('잡티', '미백', '주름' 등)
        brand: 브랜드명
        product: 제품명
        category: 제품 카테고리
    
    Returns:
        {
            'concern': str,
            'count': int,
            'overall_positive_ratio': float,
            'aspects': {...},
            'keywords': [...]
        }
    """
    
    if concern not in SKIN_CONCERNS:
        return {'error': f'잘못된 피부 고민: {concern}'}
    
    # 필터링
    if brand:
        df = df[df['brand'] == brand]
    if product:
        df = df[df['product_name'] == product]
    
    # 올리브영 + 해당 고민 있는 리뷰만
    df = df[
        (df['channel'] == 'OliveYoung') & 
        (df['skin_concerns'].str.contains(concern, na=False))
    ].copy()
    
    if len(df) < MIN_REVIEWS_PER_TYPE:
        return {
            'error': '데이터 부족',
            'concern': concern,
            'available_count': len(df),
            'required_count': MIN_REVIEWS_PER_TYPE
        }
    
    # 감성 분석
    if 'overall_label' not in df.columns:
        from .sentiment_analysis import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
        df = sentiment_analyzer.analyze_batch(df)
    
    # ABSA
    if 'absa_details' not in df.columns:
        absa = ABSAAnalyzer(category=category, channel='OliveYoung')
        df = absa.analyze_batch(df)
    
    # 전체 감성
    positive_ratio = (df['overall_label'] == 'positive').mean()
    
    # 속성별 감성
    aspects = get_aspects_by_category(category)
    aspect_sentiments = {}
    
    for aspect in aspects.keys():
        aspect_col = f'aspect_{aspect}'
        if aspect_col in df.columns:
            aspect_df = df[df[aspect_col].notna()]
            if len(aspect_df) > 0:
                positive = (aspect_df[aspect_col] == 'positive').sum()
                total = len(aspect_df)
                aspect_sentiments[aspect] = positive / total
    
    # 키워드
    extractor = KeywordExtractor(channel='OliveYoung')
    texts = df['review_text'].tolist()
    keyword_result = extractor.extract(texts, top_n=10)
    keywords = [kw['word'] for kw in keyword_result['keywords']]
    
    return {
        'concern': concern,
        'count': len(df),
        'overall_positive_ratio': float(positive_ratio),
        'aspects': aspect_sentiments,
        'keywords': keywords
    }

#//==============================================================================//#
# 피부타입 간 비교
#//==============================================================================//#

def compare_skin_types(
    df: pd.DataFrame,
    skin_types: List[str],
    brand: Optional[str] = None,
    product: Optional[str] = None,
    category: str = 'skincare'
) -> Dict:
    """
    피부타입 간 비교
    
    Args:
        df: 리뷰 DataFrame
        skin_types: 비교할 피부타입 리스트
        brand: 브랜드명
        product: 제품명
        category: 제품 카테고리
    
    Returns:
        {
            'comparison': {
                '지성': {...},
                '건성': {...}
            },
            'differences': {
                '보습': {'지성': 0.68, '건성': 0.95, 'gap': 0.27},
                ...
            }
        }
    """
    
    # 각 피부타입별 분석
    analysis_result = analyze_by_skin_type(
        df, brand=brand, product=product, category=category
    )
    
    if 'error' in analysis_result:
        return analysis_result
    
    by_skin_type = analysis_result['by_skin_type']
    
    # 요청한 피부타입만 필터
    comparison = {
        st: by_skin_type[st] 
        for st in skin_types 
        if st in by_skin_type
    }
    
    if len(comparison) < 2:
        return {'error': '비교 가능한 피부타입 데이터 부족'}
    
    # 속성별 차이 계산
    aspects = get_aspects_by_category(category)
    differences = {}
    
    for aspect in aspects.keys():
        aspect_values = {}
        
        for skin_type, data in comparison.items():
            if aspect in data['aspects']:
                aspect_values[skin_type] = data['aspects'][aspect]
        
        if len(aspect_values) >= 2:
            values_list = list(aspect_values.values())
            gap = max(values_list) - min(values_list)
            
            differences[aspect] = {
                **aspect_values,
                'gap': gap
            }
    
    return {
        'comparison': comparison,
        'differences': differences,
        'summary': _generate_comparison_summary(comparison, differences)
    }

#//==============================================================================//#
# Helper Functions
#//==============================================================================//#

def _generate_insights(results: Dict, category: str) -> List[str]:
    """
    피부타입별 분석에서 인사이트 생성
    """
    
    insights = []
    
    if len(results) < 2:
        return insights
    
    # 전체 만족도 비교
    satisfaction = {
        st: data['overall_positive_ratio'] 
        for st, data in results.items()
    }
    
    best = max(satisfaction, key=satisfaction.get)
    worst = min(satisfaction, key=satisfaction.get)
    
    insights.append(
        f"{best} 피부타입이 가장 만족도 높음 ({satisfaction[best]:.1%})"
    )
    insights.append(
        f"{worst} 피부타입이 상대적으로 낮음 ({satisfaction[worst]:.1%})"
    )
    
    # 속성별 차이
    aspects = get_aspects_by_category(category)
    
    for aspect in list(aspects.keys())[:3]:  # 상위 3개 속성
        aspect_values = {}
        for st, data in results.items():
            if aspect in data['aspects']:
                aspect_values[st] = data['aspects'][aspect]
        
        if len(aspect_values) >= 2:
            best_aspect = max(aspect_values, key=aspect_values.get)
            worst_aspect = min(aspect_values, key=aspect_values.get)
            gap = aspect_values[best_aspect] - aspect_values[worst_aspect]
            
            if gap > 0.2:  # 20%p 이상 차이
                insights.append(
                    f"{aspect}: {best_aspect}({aspect_values[best_aspect]:.1%}) vs "
                    f"{worst_aspect}({aspect_values[worst_aspect]:.1%}) - {gap:.1%}p 차이"
                )
    
    return insights


def _generate_comparison_summary(comparison: Dict, differences: Dict) -> List[str]:
    """
    피부타입 비교에서 요약 생성
    """
    
    summary = []
    
    # 큰 차이 나는 속성
    large_gaps = {
        aspect: data 
        for aspect, data in differences.items() 
        if data['gap'] > 0.2
    }
    
    if large_gaps:
        summary.append("큰 차이가 나는 속성:")
        for aspect, data in sorted(large_gaps.items(), key=lambda x: x[1]['gap'], reverse=True):
            summary.append(f"  - {aspect}: {data['gap']:.1%}p 차이")
    
    # 비슷한 속성
    similar = {
        aspect: data 
        for aspect, data in differences.items() 
        if data['gap'] < 0.1
    }
    
    if similar:
        summary.append(f"비슷한 평가: {', '.join(similar.keys())}")
    
    return summary