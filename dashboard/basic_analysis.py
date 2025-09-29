"""
기본 통계량 분석 모듈
채널별 기본 통계 정보 제공
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard_config import *

def show_basic_analysis():
    """기본 통계량 분석 화면"""
    
    st.subheader("기본 통계량 분석")
    st.caption("채널별 제품 리뷰 기본 현황을 확인할 수 있습니다")
    
    # 채널 및 카테고리 선택
    col1, col2 = st.columns(2)
    
    with col1:
        # 실제 데이터가 있는 채널만 표시
        available_channels = ["다이소", "올리브영", "쿠팡"]
        selected_channel = st.selectbox("채널 선택", available_channels, key="stats_channel")
    
    with col2:
        category_options = ["전체", "skincare", "makeup"]
        selected_category = st.selectbox("카테고리 선택", category_options, key="stats_category")
    
    # 분석 실행 버튼
    if st.button("분석 실행", type="primary"):
        with st.spinner("데이터를 로딩하고 분석중입니다..."):
            show_channel_analysis(selected_channel, selected_category)

def show_channel_analysis(channel, category):
    """채널 분석 실행"""
    
    # 전체 채널 데이터 로드
    df = load_channel_data(channel)
    
    if df.empty:
        st.error(f"{channel} 데이터를 불러올 수 없습니다.")
        st.info("데이터 파일 경로를 확인해주세요.")
        return
    
    # 데이터 구조 확인
    st.info(f"총 {len(df):,}개 데이터 로드 완료")
    
    # category 컬럼 확인
    if 'category' in df.columns:
        unique_categories = df['category'].unique()
        st.write(f"발견된 카테고리: {list(unique_categories)}")
        
        # 카테고리 필터링
        if category != "전체":
            original_len = len(df)
            # 대소문자 구분 없이 필터링
            df_filtered = df[df['category'].str.lower() == category.lower()]
            
            if df_filtered.empty:
                # 정확히 일치하는게 없으면 부분 매치 시도
                df_filtered = df[df['category'].str.contains(category, case=False, na=False)]
            
            df = df_filtered
            st.info(f"{category} 카테고리 필터링: {original_len:,}개 → {len(df):,}개 리뷰")
            
            if df.empty:
                st.warning(f"{channel}에서 {category} 카테고리 데이터가 없습니다.")
                st.write("사용 가능한 카테고리:", list(unique_categories))
                return
    else:
        st.warning("category 컬럼이 없습니다. 전체 데이터로 분석합니다.")
    
    # 기본 통계 표시
    show_basic_stats(df, channel, category)
    
    # 상세 분석
    show_detailed_analysis(df, channel, category)

def show_basic_stats(df, channel, category):
    """기본 통계 지표"""
    
    st.markdown("---")
    st.subheader(f"{channel} {category} 기본 통계")
    
    # 핵심 지표 계산
    total_reviews = len(df)
    unique_products = df['product_name'].nunique() if 'product_name' in df.columns else 0
    
    # 평균 평점 계산
    avg_rating = None
    if 'rating' in df.columns:
        try:
            df['rating_numeric'] = pd.to_numeric(df['rating'], errors='coerce')
            avg_rating = df['rating_numeric'].mean()
        except:
            pass
    
    # 평균 리뷰 길이
    avg_length = None
    if 'review_text' in df.columns:
        avg_length = df['review_text'].str.len().mean()
    elif 'text_length' in df.columns:
        avg_length = df['text_length'].mean()
    
    # 메트릭 카드 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 리뷰 수", f"{total_reviews:,}개")
    
    with col2:
        if unique_products > 0:
            st.metric("제품 수", f"{unique_products:,}개")
        else:
            st.metric("제품 수", "N/A")
    
    with col3:
        if avg_rating is not None:
            st.metric("평균 평점", f"{avg_rating:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    
    with col4:
        if avg_length is not None:
            st.metric("평균 리뷰 길이", f"{avg_length:.0f}자")
        else:
            st.metric("평균 리뷰 길이", "N/A")

def show_detailed_analysis(df, channel, category):
    """상세 분석 차트"""
    
    st.markdown("---")
    st.subheader("상세 분석")
    
    # 분석 탭
    tab1, tab2, tab3 = st.tabs(["제품별 분석", "평점 분석", "시간 분석"])
    
    with tab1:
        show_product_analysis(df)
    
    with tab2:
        show_rating_analysis(df)
    
    with tab3:
        show_time_analysis(df)

def show_product_analysis(df):
    """제품별 분석"""
    
    if 'product_name' not in df.columns:
        st.warning("제품명 데이터가 없습니다.")
        return
    
    # 제품별 리뷰 수
    product_counts = df['product_name'].value_counts().head(15)
    
    if not product_counts.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("리뷰 많은 제품 TOP 15")
            fig1 = px.bar(
                x=product_counts.values,
                y=product_counts.index,
                orientation='h',
                title="제품별 리뷰 수",
                labels={'x': '리뷰 수', 'y': '제품명'}
            )
            fig1.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("제품별 통계")
            
            # 제품별 평균 평점 (상위 10개)
            if 'rating_numeric' in df.columns:
                product_ratings = df.groupby('product_name')['rating_numeric'].agg(['count', 'mean']).round(2)
                product_ratings = product_ratings[product_ratings['count'] >= 5]  # 최소 5개 리뷰
                product_ratings = product_ratings.sort_values('mean', ascending=False).head(10)
                
                if not product_ratings.empty:
                    fig2 = px.bar(
                        x=product_ratings['mean'],
                        y=product_ratings.index,
                        orientation='h',
                        title="평점 높은 제품 TOP 10 (최소 5개 리뷰)",
                        labels={'x': '평균 평점', 'y': '제품명'}
                    )
                    fig2.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("평점 데이터가 없어 제품별 평점 분석을 할 수 없습니다.")

def show_rating_analysis(df):
    """평점 분석"""
    
    if 'rating_numeric' not in df.columns:
        st.warning("평점 데이터가 없습니다.")
        return
    
    # 평점 분포
    valid_ratings = df.dropna(subset=['rating_numeric'])
    
    if valid_ratings.empty:
        st.warning("유효한 평점 데이터가 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("평점 분포")
        
        # 히스토그램
        fig1 = px.histogram(
            valid_ratings, 
            x='rating_numeric', 
            title="평점 분포 히스토그램",
            labels={'rating_numeric': '평점', 'count': '빈도'},
            nbins=20
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 평점 통계
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("평균", f"{valid_ratings['rating_numeric'].mean():.2f}")
        col_b.metric("중앙값", f"{valid_ratings['rating_numeric'].median():.2f}")
        col_c.metric("표준편차", f"{valid_ratings['rating_numeric'].std():.2f}")
    
    with col2:
        st.subheader("평점별 리뷰 수")
        
        # 평점별 카운트 (정수 평점으로 그룹화)
        rating_counts = valid_ratings['rating_numeric'].round().value_counts().sort_index()
        
        if not rating_counts.empty:
            fig2 = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                title="평점별 리뷰 개수",
                labels={'x': '평점', 'y': '리뷰 수'}
            )
            st.plotly_chart(fig2, use_container_width=True)

def show_time_analysis(df):
    """시간 분석"""
    
    if 'review_date' not in df.columns:
        st.warning("날짜 데이터가 없습니다.")
        return
    
    # 날짜 데이터 처리
    try:
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        time_df = df.dropna(subset=['review_date'])
        
        if time_df.empty:
            st.warning("유효한 날짜 데이터가 없습니다.")
            return
        
        # 시간 단위 선택
        time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True)
        
        if time_unit == "일별":
            time_df['period'] = time_df['review_date'].dt.date
            period_counts = time_df.groupby('period').size()
            title = "일별 리뷰 수"
            x_label = "날짜"
            
        elif time_unit == "주별":
            time_df['period'] = time_df['review_date'].dt.to_period('W')
            period_counts = time_df.groupby('period').size()
            title = "주별 리뷰 수"
            x_label = "주"
            
        else:  # 월별
            time_df['period'] = time_df['review_date'].dt.to_period('M')
            period_counts = time_df.groupby('period').size()
            title = "월별 리뷰 수"
            x_label = "월"
        
        if not period_counts.empty:
            fig = px.line(
                x=[str(p) for p in period_counts.index],
                y=period_counts.values,
                title=title,
                labels={'x': x_label, 'y': '리뷰 수'}
            )
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # 기간 통계
            col1, col2, col3 = st.columns(3)
            col1.metric("총 기간", f"{len(period_counts)}개 기간")
            col2.metric("기간당 평균", f"{period_counts.mean():.1f}개")
            col3.metric("최대 리뷰", f"{period_counts.max()}개")
    
    except Exception as e:
        st.error(f"시간 분석 중 오류가 발생했습니다: {e}")

def load_channel_data(channel):
    """특정 채널의 모든 데이터 로드"""
    if channel not in DATA_PATHS:
        return pd.DataFrame()
    
    data_path = DATA_PATHS[channel]
    csv_files = glob.glob(str(data_path / "*.csv"))
    
    all_reviews = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            df['channel'] = channel
            all_reviews.append(df)
        except:
            try:
                df = pd.read_csv(file, encoding='cp949')
                df['channel'] = channel
                all_reviews.append(df)
            except:
                continue
    
    if all_reviews:
        combined_df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in combined_df.columns:
            combined_df['review_date'] = pd.to_datetime(combined_df['review_date'], errors='coerce')
        return combined_df
    return pd.DataFrame()