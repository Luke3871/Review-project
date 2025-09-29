"""
리뷰 분석 페이지
sentiment_analyzer와 tokenizer 모듈을 활용한 텍스트 분석
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from pathlib import Path
import glob

# 경로 설정 - dashboard 내 analyzer 모듈 접근
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(current_dir)  # dashboard 폴더

# dashboard 폴더를 path에 추가
if dashboard_dir not in sys.path:
    sys.path.append(dashboard_dir)

# 기존 분석 모듈 import (이제 dashboard 내에 있음)
try:
    from analyzer.txt_mining.sentiment_analyzer import SentimentAnalyzer
    from analyzer.txt_mining.tokenizer import get_count_vectorizer, get_tfidf_vectorizer
    from dashboard_config import DATA_PATHS
except ImportError as e:
    st.error(f"분석 모듈을 불러올 수 없습니다: {e}")
    st.info("analyzer 폴더의 모듈들이 dashboard 내에 올바르게 있는지 확인해주세요.")

def main():
    """리뷰 분석 메인 함수"""
    
    st.header("리뷰 분석")
    st.caption("텍스트 마이닝 및 감정 분석을 통한 리뷰 인사이트")
    
    # 분석이 완료된 상태인지 확인
    if st.session_state.get('analysis_completed', False):
        # 분석 결과 표시
        df = st.session_state.get('analysis_data')
        channel = st.session_state.get('analysis_channel')
        analysis_type = st.session_state.get('current_analysis_type')
        
        if df is not None and channel is not None:
            st.success(f"총 {len(df):,}개 리뷰 데이터 분석 완료")
            
            # 새로운 분석 시작 버튼
            if st.button("새로운 분석 시작", type="secondary"):
                # 분석 상태 초기화
                for key in ['analysis_completed', 'analysis_data', 'analysis_channel', 'current_analysis_type', 'keywords_result', 'ai_insights']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            
            st.markdown("---")
            show_analysis_results(df, channel, analysis_type)
            return
    
    # 데이터 선택 섹션
    show_data_selection()

def show_data_selection():
    """데이터 선택 섹션"""
    
    st.subheader("분석 데이터 선택")
    
    # 채널 선택
    col1, col2, col3 = st.columns(3)
    
    with col1:
        channels = ["다이소", "올리브영", "쿠팡", "무신사", "화해", "글로우픽"]
        selected_channel = st.selectbox("채널 선택", channels, key="review_channel")
    
    # 다이소만 활성화, 나머지는 비활성화
    if selected_channel != "다이소":
        st.warning(f"{selected_channel}은 준비 중입니다. 현재는 다이소만 분석 가능합니다.")
        return
    
    # 다이소 세부 설정
    with col2:
        categories = ["skincare", "makeup"]
        selected_category = st.selectbox("카테고리", categories, key="review_category")
    
    with col3:
        sort_options = ["리뷰많은순", "판매순", "좋아요순"]
        selected_sort = st.selectbox("정렬 방식", sort_options, key="review_sort")
    
    # 데이터 크기 조절 옵션
    st.markdown("### 데이터 크기 설정")
    col1, col2 = st.columns(2)
    
    with col1:
        sample_size_options = {
            "전체 데이터": None,
            "10,000개 샘플": 10000,
            "5,000개 샘플": 5000,
            "1,000개 샘플": 1000
        }
        selected_sample = st.selectbox(
            "데이터 크기",
            list(sample_size_options.keys()),
            index=2,  # 기본값: 5,000개
            key="sample_size",
            help="큰 데이터는 분석 시간이 오래 걸립니다. 테스트용으로는 1,000-5,000개 추천"
        )
        sample_size = sample_size_options[selected_sample]
    
    with col2:
        period_options = ["전체", "최근 1년", "최근 6개월", "최근 3개월"]
        selected_period = st.selectbox(
            "분석 기간",
            period_options,
            index=2,  # 기본값: 최근 3개월
            key="analysis_period",
            help="최근 데이터만 분석하면 속도가 빨라집니다"
        )
    
    st.info(f"선택: {selected_channel} > {selected_category} > {selected_sort} | 크기: {selected_sample} | 기간: {selected_period}")
    
    # 분석 설정 및 실행
    show_analysis_settings(selected_channel, selected_category, selected_sort, sample_size, selected_period)

def show_analysis_settings(channel, category, sort_method, sample_size, period):
    """분석 설정 및 실행"""
    
    st.markdown("---")
    st.subheader("분석 설정")
    
    # 분석 방법 선택
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_type = st.selectbox(
            "분석 방법",
            ["count", "tfidf"],
            format_func=lambda x: "Count 벡터라이저" if x == "count" else "TF-IDF 벡터라이저",
            key="analysis_type",
            index=0
        )
    
    with col2:
        st.markdown("**벡터라이저 하이퍼파라미터**")
    
    # 하이퍼파라미터 설정
    show_hyperparameter_settings()
    
    # 분석 실행 버튼
    if st.button("리뷰 분석 실행", type="primary"):
        with st.spinner("데이터를 로딩하고 분석중입니다..."):
            run_review_analysis(channel, category, sort_method, analysis_type, sample_size, period)

def show_hyperparameter_settings():
    """하이퍼파라미터 설정 섹션"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # min_df 설정
        min_df = st.number_input(
            "min_df (최소 문서 빈도)",
            min_value=1,
            max_value=20,
            value=2,
            key="min_df",
            help="숫자가 높을수록 희귀한 단어가 제거됩니다. 예) 2로 설정하면 '굳굳', '쌉굿' 같은 신조어나 '개꿀' 같은 속어가 제거되고, 5로 올리면 '향수', '틴트' 같은 단어도 제거될 수 있습니다"
        )
        
        # max_features 설정
        max_features = st.number_input(
            "max_features (최대 키워드 수)",
            min_value=10,
            max_value=100,
            value=30,
            key="max_features",
            help="결과로 표시할 키워드 개수입니다. 예) 30이면 '촉촉하다', '발림성' 같은 상위 30개 형태소만 표시, 50으로 늘리면 '흡수력', '지속성' 같은 세부 특성까지 볼 수 있습니다"
        )
    
    with col2:
        # max_df 설정
        max_df = st.number_input(
            "max_df (최대 문서 비율)",
            min_value=0.1,
            max_value=1.0,
            value=0.85,
            step=0.05,
            key="max_df",
            help="숫자가 낮을수록 흔한 단어가 제거됩니다. 예) 0.85는 전체 리뷰의 85% 이상에 등장하는 '좋다', '사용하다', '제품' 같은 기본 단어를 제거하고, 0.5로 낮추면 '만족', '추천' 같은 단어까지 제거됩니다"
        )
        
        # ngram_range 설정
        ngram_max = st.number_input(
            "ngram_range (N-gram 최대값)",
            min_value=1,
            max_value=3,
            value=2,
            key="ngram_max",
            help="1이면 '촉촉하다', '좋다' 같은 형태소만, 2면 '촉촉하다 느낌', '사용감 좋다', '발림성 좋다' 같은 형태소 조합도 포함되어 더 구체적인 의견을 파악할 수 있습니다"
        )
    
    # 세션 상태에 설정 저장
    st.session_state.vectorizer_config = {
        'analysis_type': st.session_state.get('analysis_type', 'count'),
        'min_df': min_df,
        'max_df': max_df,
        'max_features': max_features,
        'ngram_range': (1, ngram_max)
    }

def run_review_analysis(channel, category, sort_method, analysis_type, sample_size, period):
    """리뷰 분석 실행"""
    
    # 데이터 로드
    df = load_review_data(channel, category, sort_method, sample_size, period)
    
    if df.empty:
        st.error(f"{channel} {category} {sort_method} 데이터를 불러올 수 없습니다.")
        return
    
    # 분석 완료 상태를 세션에 저장 (위젯 key와 다른 이름 사용)
    st.session_state.analysis_completed = True
    st.session_state.analysis_data = df
    st.session_state.analysis_channel = channel
    st.session_state.current_analysis_type = analysis_type  # 위젯 key와 다른 이름으로 변경
    
    # 페이지 새로고침하여 결과 화면으로 전환
    st.rerun()

def load_review_data(channel, category, sort_method, sample_size=None, period="전체"):
    """리뷰 데이터 로딩 (샘플링 및 기간 필터링 적용)"""
    
    try:
        if channel != "다이소" or "다이소" not in DATA_PATHS:
            return pd.DataFrame()
        
        data_path = DATA_PATHS["다이소"]
        
        # 정렬방식별 파일 패턴
        sort_patterns = {
            "판매순": "*_SALES_*_processed.csv",
            "리뷰많은순": "*_REVIEW_*_processed.csv", 
            "좋아요순": "*_LIKE_*_processed.csv"
        }
        
        if sort_method not in sort_patterns:
            return pd.DataFrame()
        
        # 파일 찾기
        pattern = str(data_path / sort_patterns[sort_method])
        csv_files = glob.glob(pattern)
        
        if not csv_files:
            return pd.DataFrame()
        
        # 카테고리 필터링
        category_files = [f for f in csv_files if category.lower() in Path(f).name.lower()]
        csv_files = category_files
        
        if not csv_files:
            return pd.DataFrame()
        
        # 파일 로딩
        all_reviews = []
        for file in csv_files:
            try:
                df = pd.read_csv(file, encoding='utf-8')
                all_reviews.append(df)
            except:
                try:
                    df = pd.read_csv(file, encoding='cp949')
                    all_reviews.append(df)
                except:
                    continue
        
        if not all_reviews:
            return pd.DataFrame()
        
        combined_df = pd.concat(all_reviews, ignore_index=True)
        
        # 기간 필터링
        if period != "전체" and 'review_date' in combined_df.columns:
            combined_df = filter_by_period(combined_df, period)
        
        # 샘플링 적용
        if sample_size and len(combined_df) > sample_size:
            combined_df = combined_df.sample(n=sample_size, random_state=42)
            st.info(f"데이터가 {sample_size:,}개로 샘플링되었습니다.")
        
        return combined_df
        
    except Exception as e:
        st.error(f"데이터 로딩 중 오류: {e}")
        return pd.DataFrame()

def filter_by_period(df, period):
    """기간별 필터링"""
    from datetime import datetime, timedelta
    
    if period == "전체" or 'review_date' not in df.columns:
        return df
    
    now = datetime.now()
    
    if period == "최근 1년":
        start_date = now - timedelta(days=365)
    elif period == "최근 6개월":
        start_date = now - timedelta(days=180)
    elif period == "최근 3개월":
        start_date = now - timedelta(days=90)
    else:
        return df
    
    df_copy = df.copy()
    df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
    filtered_df = df_copy[df_copy['review_date'] >= start_date]
    
    return filtered_df

def show_analysis_results(df, channel, analysis_type):
    """분석 결과 표시"""
    
    # 분석기 초기화
    try:
        sentiment_analyzer = SentimentAnalyzer(channel_name=channel.lower())
    except Exception as e:
        st.error(f"분석기 초기화 오류: {e}")
        return
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["감정 분석", "키워드 분석", "제품별 분석", "AI 인사이트 보고서"])
    
    with tab1:
        show_sentiment_analysis_tab(df, sentiment_analyzer)
    
    with tab2:
        show_keyword_analysis_tab(df, channel, analysis_type)
    
    with tab3:
        show_product_analysis_tab(df, sentiment_analyzer, channel, analysis_type)
    
    with tab4:
        show_ai_insights_report_tab()

def show_sentiment_analysis_tab(df, sentiment_analyzer):
    """감정 분석 탭"""
    
    st.subheader("감정 분석")
    
    # 전체 감정 분포
    sentiment_dist = sentiment_analyzer.get_sentiment_distribution(df)
    
    if sentiment_dist:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("긍정 리뷰 (4-5점)", f"{sentiment_dist['positive_count']:,}개")
        
        with col2:
            st.metric("부정 리뷰 (1-3점)", f"{sentiment_dist['negative_count']:,}개")
        
        with col3:
            st.metric("긍정 비율", f"{sentiment_dist['positive_ratio']:.1%}")
        
        # 감정 분포 파이 차트
        labels = ['긍정 (4-5점)', '부정 (1-3점)']
        values = [sentiment_dist['positive_count'], sentiment_dist['negative_count']]
        colors = ['#4ecdc4', '#ff6b6b']
        
        fig = px.pie(
            values=values,
            names=labels,
            title="전체 감정 분포",
            color_discrete_sequence=colors
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("감정 분석을 위한 평점 데이터가 없습니다.")
    
    # 감정별 키워드 분석
    st.markdown("#### 감정별 주요 키워드")
    
    positive_keywords, negative_keywords = sentiment_analyzer.analyze_sentiment_keywords(df)
    
    if positive_keywords and negative_keywords:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 긍정 키워드 TOP 10")
            pos_df = pd.DataFrame(positive_keywords, columns=['키워드', '빈도'])
            
            fig_pos = px.bar(
                pos_df,
                x='빈도',
                y='키워드',
                orientation='h',
                title="긍정 리뷰 주요 키워드",
                color_discrete_sequence=['#4ecdc4']
            )
            fig_pos.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_pos, use_container_width=True)
        
        with col2:
            st.markdown("##### 부정 키워드 TOP 10")
            neg_df = pd.DataFrame(negative_keywords, columns=['키워드', '빈도'])
            
            fig_neg = px.bar(
                neg_df,
                x='빈도',
                y='키워드',
                orientation='h',
                title="부정 리뷰 주요 키워드",
                color_discrete_sequence=['#ff6b6b']
            )
            fig_neg.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_neg, use_container_width=True)
    else:
        st.info("감정별 키워드 분석 결과가 없습니다.")

def show_keyword_analysis_tab(df, channel, analysis_type):
    """키워드 분석 탭"""
    
    st.subheader("키워드 분석")
    
    # 벡터라이저 설정 가져오기
    vectorizer_config = st.session_state.get('vectorizer_config', {
        'analysis_type': analysis_type,
        'min_df': 2,
        'max_df': 0.85,
        'max_features': 30,
        'ngram_range': (1, 2)
    })
    
    # 현재 설정 표시
    st.info(f"분석 방법: {vectorizer_config['analysis_type'].upper()} | "
            f"min_df: {vectorizer_config['min_df']} | "
            f"max_df: {vectorizer_config['max_df']} | "
            f"max_features: {vectorizer_config['max_features']} | "
            f"ngram_range: {vectorizer_config['ngram_range']}")
    
    if 'review_text' not in df.columns:
        st.warning("리뷰 텍스트 데이터가 없습니다.")
        return
    
    # 키워드 분석 실행
    with st.spinner("키워드를 분석중입니다..."):
        keywords = analyze_keywords(df, channel, vectorizer_config)
        
        # 키워드 결과를 세션에 저장
        if keywords:
            st.session_state.keywords_result = keywords
    
    if keywords:
        # 키워드 차트
        keywords_df = pd.DataFrame(keywords[:vectorizer_config['max_features']], columns=['키워드', '점수'])
        
        fig = px.bar(
            keywords_df,
            x='점수',
            y='키워드',
            orientation='h',
            title=f"주요 키워드 ({vectorizer_config['analysis_type'].upper()} 기반)",
            labels={'점수': '중요도 점수', '키워드': '키워드'},
            color_discrete_sequence=['#26a69a']
        )
        fig.update_layout(height=800, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 키워드 테이블
        st.markdown("#### 상세 키워드 목록")
        st.dataframe(keywords_df, use_container_width=True)
    else:
        st.warning("키워드 분석 결과가 없습니다.")

def show_product_analysis_tab(df, sentiment_analyzer, channel, analysis_type):
    """제품별 분석 탭"""
    
    st.subheader("제품별 분석")
    
    if 'product_name' not in df.columns:
        st.warning("제품명 데이터가 없습니다.")
        return
    
    # 제품 선택
    products = df['product_name'].unique()
    selected_product = st.selectbox(
        "분석할 제품 선택",
        products,
        key="sentiment_product"
    )
    
    product_df = df[df['product_name'] == selected_product]
    
    # 제품 기본 정보
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 리뷰 수", f"{len(product_df):,}개")
    
    with col2:
        if 'rating_numeric' in product_df.columns:
            avg_rating = product_df['rating_numeric'].mean()
            st.metric("평균 평점", f"{avg_rating:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    
    with col3:
        # LG 제품 여부 표시
        is_lg = product_df['is_lg_product'].iloc[0] if 'is_lg_product' in product_df.columns else False
        st.metric("브랜드", "LG 생활건강" if is_lg else "기타")
    
    # 제품별 감정 분석
    product_sentiment = sentiment_analyzer.get_sentiment_distribution(product_df)
    
    if product_sentiment:
        col1, col2 = st.columns(2)
        
        with col1:
            # 감정 분포 차트
            labels = ['긍정', '부정']
            values = [product_sentiment['positive_count'], product_sentiment['negative_count']]
            colors = ['#4ecdc4', '#ff6b6b']
            
            fig = px.pie(
                values=values,
                names=labels,
                title=f"{selected_product} 감정 분포",
                color_discrete_sequence=colors
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 제품별 키워드
            st.markdown("##### 주요 키워드")
            vectorizer_config = st.session_state.get('vectorizer_config', {})
            vectorizer_config['max_features'] = 15  # 제품별은 15개로 제한
            
            product_keywords = analyze_keywords(product_df, channel, vectorizer_config)
            
            if product_keywords:
                keywords_df = pd.DataFrame(product_keywords[:15], columns=['키워드', '점수'])
                st.dataframe(keywords_df, use_container_width=True)

def show_ai_insights_report_tab():
    """AI 인사이트 보고서 탭"""
    
    st.subheader("AI 인사이트 보고서")
    st.caption("키워드 분석 결과를 기반으로 한 AI 해석 및 조언")
    
    # 분석이 완료되었는지 확인
    if not st.session_state.get('analysis_completed', False):
        st.warning("먼저 리뷰 분석을 실행해주세요.")
        return
    
    # 이미 AI 결과가 있는지 확인
    if st.session_state.get('ai_insights'):
        st.success("AI 분석이 완료되었습니다!")
        st.markdown("### AI 키워드 분석 해석 및 조언")
        st.markdown(st.session_state.ai_insights)
        
        # 보고서 다운로드
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        st.download_button(
            label="보고서 다운로드 (TXT)",
            data=st.session_state.ai_insights,
            file_name=f"키워드분석_AI해석_{timestamp}.txt",
            mime="text/plain"
        )
        
        # 새로운 분석 버튼
        if st.button("새 AI 분석 실행", key="new_ai_analysis"):
            if 'ai_insights' in st.session_state:
                del st.session_state.ai_insights
            st.rerun()
        
        return
    
    st.info("현재 분석된 키워드 결과를 바탕으로 AI 인사이트를 생성합니다.")
    
    # 분석 상태 확인
    analysis_data = st.session_state.get('analysis_data')
    analysis_channel = st.session_state.get('analysis_channel')
    keywords_result = st.session_state.get('keywords_result')
    
    # 키워드 결과가 없으면 다시 생성
    if analysis_data is not None and keywords_result is None:
        with st.spinner("키워드 분석 결과를 준비중입니다..."):
            vectorizer_config = st.session_state.get('vectorizer_config', {
                'analysis_type': 'count',
                'min_df': 2,
                'max_df': 0.85,
                'max_features': 30,
                'ngram_range': (1, 2)
            })
            keywords_result = analyze_keywords(analysis_data, analysis_channel, vectorizer_config)
            if keywords_result:
                st.session_state.keywords_result = keywords_result
                st.success("키워드 분석 준비 완료!")
    
    if analysis_data is not None and keywords_result is not None:
        
        # API 키 입력 (세션에 저장)
        if 'api_key_input' not in st.session_state:
            st.session_state.api_key_input = ""
            
        api_key = st.text_input(
            "OpenAI API Key 입력",
            value=st.session_state.api_key_input,
            type="password",
            help="GPT 분석을 위해 OpenAI API 키가 필요합니다"
        )
        
        if api_key:
            st.session_state.api_key_input = api_key
        
        # AI 분석 실행 버튼
        if st.button("AI 분석 결과 해석 및 조언 생성", type="primary", key="generate_ai_insights"):
            if not api_key:
                st.error("API 키를 입력해주세요.")
                st.stop()
                
            # AI 분석 실행
            with st.spinner("AI가 키워드 분석 결과를 해석중입니다..."):
                vectorizer_config = st.session_state.get('vectorizer_config', {})
                
                try:
                    insights = generate_keyword_interpretation(analysis_data, keywords_result, vectorizer_config, api_key)
                    
                    if insights:
                        # 세션에 저장
                        st.session_state.ai_insights = insights
                        st.success("AI 분석이 완료되었습니다!")
                        st.rerun()  # 결과를 표시하기 위해 새로고침
                    else:
                        st.error("AI 해석 생성 중 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"AI 분석 중 오류: {str(e)}")
    else:
        if analysis_data is None:
            st.warning("분석 데이터가 없습니다. 먼저 리뷰 분석을 실행해주세요.")
        elif keywords_result is None:
            st.warning("키워드 분석 결과를 준비할 수 없습니다. 키워드 분석 탭에서 먼저 분석을 완료해주세요.")

def generate_keyword_interpretation(df, keywords, vectorizer_config, api_key):
    """키워드 분석 결과에 대한 AI 해석 생성"""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # 키워드 결과 요약
        top_keywords = keywords[:20]  # 상위 20개 키워드
        keyword_list = [f"{word}: {score:.3f}" for word, score in top_keywords]
        
        # 기본 통계
        total_reviews = len(df)
        avg_rating = df['rating_numeric'].mean() if 'rating_numeric' in df.columns else None
        
        # 감정 분포
        positive_count = len(df[df['rating_numeric'] >= 4]) if 'rating_numeric' in df.columns else 0
        negative_count = len(df[df['rating_numeric'] <= 3]) if 'rating_numeric' in df.columns else 0
        
        # GPT 프롬프트
        prompt = f"""
다음은 리뷰 데이터의 키워드 분석 결과입니다:

**분석 설정:**
- 벡터라이저: {vectorizer_config['analysis_type'].upper()}
- 최소 문서 빈도(min_df): {vectorizer_config['min_df']}
- 최대 문서 비율(max_df): {vectorizer_config['max_df']}
- N-gram 범위: {vectorizer_config['ngram_range']}

**기본 통계:**
- 총 리뷰 수: {total_reviews:,}개
- 평균 평점: {avg_rating:.2f}점 (5점 만점)
- 긍정 리뷰: {positive_count:,}개 ({positive_count/total_reviews*100:.1f}%)
- 부정 리뷰: {negative_count:,}개 ({negative_count/total_reviews*100:.1f}%)

**상위 20개 키워드 (중요도 순):**
{chr(10).join(keyword_list)}

위 키워드 분석 결과를 해석하고 다음 관점에서 조언해주세요:

1. **키워드 패턴 분석**
   - 어떤 키워드들이 주로 등장하는지
   - 긍정적/부정적 키워드의 특징
   - 고객들이 중요하게 생각하는 요소들

2. **제품 개선 방향**
   - 키워드를 통해 파악된 개선점
   - 고객 불만사항과 해결 방안
   - 강화해야 할 긍정 요소들

3. **마케팅 전략 제안**
   - 키워드 기반 마케팅 포인트
   - 고객 커뮤니케이션 방향
   - 경쟁 우위 확보 방안

4. **우선순위 액션 아이템**
   - 즉시 실행 가능한 개선사항
   - 중장기 전략 과제
   - 성과 측정 방법

구체적이고 실용적인 조언을 마크다운 형식으로 작성해주세요.
"""
        
        # GPT API 호출
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 텍스트 마이닝 전문가이자 비즈니스 컨설턴트입니다. 키워드 분석 결과를 해석하여 구체적이고 실행 가능한 비즈니스 조언을 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"AI 해석 생성 오류: {str(e)}")
        return None

def analyze_keywords(df, channel, vectorizer_config):
    """키워드 분석 실행"""
    
    if df.empty or 'review_text' not in df.columns:
        return None
    
    reviews = df['review_text'].fillna('').astype(str)
    reviews = reviews[reviews.str.len() > 0]
    
    if len(reviews) == 0:
        return None
    
    try:
        # 벡터라이저 선택
        if vectorizer_config['analysis_type'] == 'count':
            vectorizer = get_count_vectorizer(
                channel_name=channel.lower(),
                min_df=vectorizer_config.get('min_df', 2),
                max_df=vectorizer_config.get('max_df', 1.0),
                max_features=vectorizer_config.get('max_features', 30),
                ngram_range=vectorizer_config.get('ngram_range', (1, 2))
            )
        else:  # tfidf
            vectorizer = get_tfidf_vectorizer(
                channel_name=channel.lower(),
                min_df=vectorizer_config.get('min_df', 2),
                max_df=vectorizer_config.get('max_df', 0.85),
                max_features=vectorizer_config.get('max_features', 30),
                ngram_range=vectorizer_config.get('ngram_range', (1, 2))
            )
        
        # 벡터화 및 점수 계산
        matrix = vectorizer.fit_transform(reviews)
        feature_names = vectorizer.get_feature_names_out()
        
        if vectorizer_config['analysis_type'] == 'count':
            scores = matrix.sum(axis=0).A1
        else:
            scores = matrix.mean(axis=0).A1
        
        # 결과 정렬
        word_scores = list(zip(feature_names, scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        return word_scores
        
    except Exception as e:
        st.error(f"키워드 분석 중 오류: {e}")
        return None

if __name__ == "__main__":
    main()