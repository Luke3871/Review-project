"""
다이소 채널 전용 분석 모듈 - AI Insights 포함
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import glob
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

# dashboard_config import
try:
    from dashboard_config import DATA_PATHS
except ImportError:
    try:
        from dashboard.dashboard_config import DATA_PATHS
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from dashboard_config import DATA_PATHS

def show_analysis():
    """다이소 분석 메인 함수"""
    
    st.subheader("다이소 리뷰 분석")
    
    # 데이터 선택
    col1, col2 = st.columns(2)
    
    with col1:
        category_options = ["전체", "skincare", "makeup"]
        selected_category = st.selectbox(
            "카테고리 선택", 
            category_options, 
            key="daiso_category"
        )
    
    with col2:
        sort_options = ["리뷰많은순", "판매순", "좋아요순"]
        selected_sort = st.selectbox(
            "정렬 방식 (데이터셋)",
            sort_options,
            key="daiso_sort",
            help="선택한 정렬방식의 TOP100 데이터만 로딩됩니다"
        )
    
    # 데이터 로딩
    with st.spinner(f"다이소 {selected_sort} 데이터를 로딩중입니다..."):
        df = load_daiso_data_by_sort(selected_category, selected_sort)
        
        if df.empty:
            st.error(f"다이소 {selected_sort} 데이터를 불러올 수 없습니다.")
            return
        
        # 데이터셋 기본 정보
        show_dataset_info(df, selected_category, selected_sort)
        
        # 기본 통계량
        show_detailed_analysis(df, selected_category, selected_sort)
        
        # 히스토리 추가
        add_to_history(f"다이소 {selected_category} ({selected_sort})")

def load_daiso_data_by_sort(category, sort_method):
    """정렬방식별 다이소 데이터 로딩"""
    
    if "다이소" not in DATA_PATHS:
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
        st.warning(f"다이소 {sort_method} 데이터를 찾을 수 없습니다.")
        return pd.DataFrame()
    
    # 카테고리 필터링
    if category != "전체":
        category_files = [f for f in csv_files if category.lower() in Path(f).name.lower()]
        csv_files = category_files
    
    if not csv_files:
        st.warning(f"다이소 {category} {sort_method} 데이터를 찾을 수 없습니다.")
        return pd.DataFrame()
    
    # 파일 로딩
    all_reviews = []
    successful_files = 0
    
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            df['channel'] = '다이소'
            all_reviews.append(df)
            successful_files += 1
        except:
            try:
                df = pd.read_csv(file, encoding='cp949')
                df['channel'] = '다이소'
                all_reviews.append(df)
                successful_files += 1
            except:
                continue
    
    if all_reviews:
        combined_df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in combined_df.columns:
            combined_df['review_date'] = pd.to_datetime(combined_df['review_date'], errors='coerce')
        
        st.info(f"로딩 완료: {successful_files}개 파일, {len(combined_df):,}개 리뷰")
        return combined_df
    
    return pd.DataFrame()

def show_dataset_info(df, category, sort_method):
    """데이터셋 기본 정보"""
    
    st.markdown("### 데이터셋 정보")
    
    # 기본 통계
    total_reviews = len(df)
    unique_products = df['product_name'].nunique() if 'product_name' in df.columns else 0
    
    # 평균 평점
    avg_rating = None
    if 'rating_numeric' in df.columns:
        avg_rating = df['rating_numeric'].mean()
    
    # 평균 리뷰 길이
    avg_length = None
    if 'text_length' in df.columns:
        avg_length = df['text_length'].mean()
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 리뷰 수", f"{total_reviews:,}개")
    
    with col2:
        st.metric("제품 수", f"{unique_products:,}개")
    
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
    
    # 데이터 범위
    if 'review_date' in df.columns:
        valid_dates = df['review_date'].dropna()
        if not valid_dates.empty:
            date_range = f"{valid_dates.min().strftime('%Y-%m-%d')} ~ {valid_dates.max().strftime('%Y-%m-%d')}"
            st.info(f"데이터 기간: {date_range}")
    
    # 데이터 특징 설명
    st.markdown(f"""
    **📋 데이터 특징**  
    {category} 카테고리에서 다이소 **{sort_method}** 기준으로 크롤링된 TOP 100 제품들의 리뷰 데이터입니다.  
    이 데이터는 실제 소비자들이 해당 정렬 조건에서 상위에 노출된 제품들에 대해 작성한 리뷰들을 포함하고 있어, 
    {sort_method.replace('순', '')} 기준의 인기 제품 트렌드와 소비자 반응을 분석할 수 있습니다.
    """)

def show_detailed_analysis(df, category, sort_method):
    """기본 통계량"""
    
    st.markdown("---")
    st.subheader("기본 통계량")
    
    # 탭 생성
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["랭킹 분석", "제품별 분석", "시계열 분석", "AI Insights", "요약 리포트"])
    
    with tab1:
        show_ranking_tab(df)
    
    with tab2:
        show_product_analysis_tab(df)
    
    with tab3:
        show_timeseries_tab(df)
    
    with tab4:
        show_ai_insights_tab(df, category, sort_method)
    
    with tab5:
        show_summary_report_tab(df, category, sort_method)

def show_ranking_tab(df):
    """랭킹 분석 탭"""
    
    # 기간 필터
    period_options = ["전체", "1주일", "1개월", "3개월", "6개월", "1년"]
    selected_period = st.selectbox(
        "분석 기간",
        period_options,
        key="ranking_period"
    )
    
    # 기간 필터링
    filtered_df = filter_by_period(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"선택한 기간({selected_period})에 해당하는 데이터가 없습니다.")
        return
    
    # 필터링 결과
    if selected_period != "전체":
        st.caption(f"기간 필터링: {len(df):,}개 → {len(filtered_df):,}개 리뷰")
    
    if 'product_name' not in filtered_df.columns:
        st.warning("제품명 데이터가 없습니다.")
        return
    
    # LG 제품 현황 표시
    if 'is_lg_product' in filtered_df.columns:
        lg_count = filtered_df['is_lg_product'].sum()
        total_products = filtered_df['product_name'].nunique()
        st.info(f"LG 생활건강 제품: {lg_count:,}개 리뷰 (전체 {total_products:,}개 제품 중)")
    
    # 제품별 분석
    product_counts = filtered_df['product_name'].value_counts().head(20)
    
    if not product_counts.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("리뷰 많은 제품 TOP 20")
            
            # LG 제품 구분을 위한 라벨 준비 (HTML 스타일링 사용)
            y_labels = []
            
            for product in product_counts.index:
                # LG 제품 여부 확인
                is_lg = filtered_df[filtered_df['product_name'] == product]['is_lg_product'].iloc[0] if 'is_lg_product' in filtered_df.columns else False
                
                # 라벨에 [LG] 태그 추가
                if is_lg:
                    label = f"<span style='color: #FF6B6B; font-weight: bold;'>[LG]</span> {product}"
                else:
                    label = product
                y_labels.append(label)
            
            fig1 = px.bar(
                x=product_counts.values,
                y=y_labels,
                orientation='h',
                title="제품별 리뷰 수",
                labels={'x': '리뷰 수', 'y': '제품명'},
                color_discrete_sequence=['#ff6b6b']
            )
            fig1.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("평점 높은 제품 TOP 20")
            
            if 'rating_numeric' in filtered_df.columns:
                product_ratings = filtered_df.groupby('product_name')['rating_numeric'].agg(['count', 'mean']).round(2)
                product_ratings = product_ratings[product_ratings['count'] >= 3]
                product_ratings = product_ratings.sort_values('mean', ascending=False).head(20)
                
                if not product_ratings.empty:
                    # LG 제품 구분을 위한 라벨 준비 (HTML 스타일링 사용)
                    y_labels_rating = []
                    
                    for product in product_ratings.index:
                        # LG 제품 여부 확인
                        is_lg = filtered_df[filtered_df['product_name'] == product]['is_lg_product'].iloc[0] if 'is_lg_product' in filtered_df.columns else False
                        
                        # 라벨에 [LG] 태그 + 평점 표시
                        rating = product_ratings.loc[product, 'mean']
                        if is_lg:
                            label = f"<span style='color: #FF6B6B; font-weight: bold;'>[LG]</span> {product} ({rating:.2f}점)"
                        else:
                            label = f"{product} ({rating:.2f}점)"
                        y_labels_rating.append(label)
                    
                    fig2 = px.bar(
                        x=product_ratings['mean'],
                        y=y_labels_rating,
                        orientation='h',
                        title="평점 높은 제품 TOP 20 (최소 3개 리뷰)",
                        labels={'x': '평균 평점', 'y': '제품명'},
                        color_discrete_sequence=['#4ecdc4']
                    )
                    fig2.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("평점 데이터가 없습니다.")

def show_product_analysis_tab(df):
    """제품별 분석 탭"""
    
    # 기간 필터
    period_options = ["전체", "1주일", "1개월", "3개월", "6개월", "1년"]
    selected_period = st.selectbox(
        "분석 기간",
        period_options,
        key="product_analysis_period"
    )
    
    # 기간 필터링
    filtered_df = filter_by_period(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"선택한 기간({selected_period})에 해당하는 데이터가 없습니다.")
        return
    
    # 필터링 결과
    if selected_period != "전체":
        st.caption(f"기간 필터링: {len(df):,}개 → {len(filtered_df):,}개 리뷰")
    
    if 'product_name' not in filtered_df.columns:
        st.warning("제품명 데이터가 없습니다.")
        return
    
    # 비교 분석 모드 선택
    compare_mode = st.checkbox("다른 제품과 비교하기", key="compare_mode")
    
    if compare_mode:
        show_product_comparison(filtered_df)
    else:
        show_single_product_analysis(filtered_df)

def show_single_product_analysis(df):
    """단일 제품 분석"""
    
    # 제품 목록 준비 (LG 제품 구분)
    product_options = prepare_product_options(df)
    
    if not product_options:
        st.warning("분석할 제품이 없습니다.")
        return
    
    # 제품 선택
    selected_product_display = st.selectbox(
        "분석할 제품 선택",
        product_options,
        key="single_product_select"
    )
    
    # 실제 제품명 추출 (LG 태그 제거)
    selected_product = selected_product_display.replace("[LG] ", "")
    
    # 제품 데이터 추출
    product_df = df[df['product_name'] == selected_product]
    
    if product_df.empty:
        st.warning("선택한 제품의 데이터가 없습니다.")
        return
    
    # 제품 분석 표시
    show_product_stats(product_df, selected_product_display, max_y_value=None)

def show_product_comparison(df):
    """제품 비교 분석"""
    
    # 제품 목록 준비
    product_options = prepare_product_options(df)
    
    if len(product_options) < 2:
        st.warning("비교할 제품이 부족합니다. 최소 2개 제품이 필요합니다.")
        return
    
    # 제품 선택
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("제품 A")
        product_a_display = st.selectbox(
            "첫 번째 제품 선택",
            product_options,
            key="product_a_select"
        )
    
    with col2:
        st.subheader("제품 B")
        # 제품 A와 다른 제품만 선택 가능
        product_b_options = [p for p in product_options if p != product_a_display]
        product_b_display = st.selectbox(
            "두 번째 제품 선택",
            product_b_options,
            key="product_b_select"
        )
    
    # 실제 제품명 추출
    product_a = product_a_display.replace("[LG] ", "")
    product_b = product_b_display.replace("[LG] ", "")
    
    # 제품 데이터 추출
    product_a_df = df[df['product_name'] == product_a]
    product_b_df = df[df['product_name'] == product_b]
    
    if product_a_df.empty or product_b_df.empty:
        st.warning("선택한 제품의 데이터가 없습니다.")
        return
    
    # Y축 범위 통일을 위한 최대값 계산
    max_monthly_reviews = 0
    if 'review_date' in df.columns:
        # 두 제품의 월별 리뷰 수 최대값 계산
        for product_data in [product_a_df, product_b_df]:
            product_data_copy = product_data.copy()
            product_data_copy['review_date'] = pd.to_datetime(product_data_copy['review_date'], errors='coerce')
            monthly_reviews = product_data_copy.groupby(product_data_copy['review_date'].dt.to_period('M')).size()
            if not monthly_reviews.empty:
                max_monthly_reviews = max(max_monthly_reviews, monthly_reviews.max())
    
    # 비교 분석 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {product_a_display}")
        show_product_stats(product_a_df, product_a_display, max_y_value=max_monthly_reviews)
    
    with col2:
        st.markdown(f"### {product_b_display}")
        show_product_stats(product_b_df, product_b_display, max_y_value=max_monthly_reviews)

def prepare_product_options(df):
    """제품 선택 옵션 준비 (LG 제품 구분하여 상단 배치)"""
    
    if 'product_name' not in df.columns:
        return []
    
    products = df['product_name'].unique()
    lg_products = []
    other_products = []
    
    for product in products:
        # LG 제품 여부 확인
        is_lg = df[df['product_name'] == product]['is_lg_product'].iloc[0] if 'is_lg_product' in df.columns else False
        
        if is_lg:
            lg_products.append(f"[LG] {product}")
        else:
            other_products.append(product)
    
    # LG 제품을 상단에, 나머지를 하단에 배치
    return sorted(lg_products) + sorted(other_products)

def show_product_stats(product_df, product_display_name, max_y_value=None):
    """제품 통계 표시"""
    
    # 핵심 기본 지표
    total_reviews = len(product_df)
    avg_rating = product_df['rating_numeric'].mean() if 'rating_numeric' in product_df.columns else None
    
    # 평점 분포
    rating_dist = {}
    if 'rating_numeric' in product_df.columns:
        rating_counts = product_df['rating_numeric'].value_counts().sort_index()
        for i in range(1, 6):
            rating_dist[i] = rating_counts.get(float(i), 0)
    
    # 메트릭 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("총 리뷰 수", f"{total_reviews:,}개")
    
    with col2:
        if avg_rating is not None:
            st.metric("평균 평점", f"{avg_rating:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    
    # 평점 분포 표시
    if rating_dist:
        st.markdown("#### 평점 분포")
        rating_col1, rating_col2, rating_col3, rating_col4, rating_col5 = st.columns(5)
        
        with rating_col1:
            st.metric("5점", f"{rating_dist[5]}개")
        with rating_col2:
            st.metric("4점", f"{rating_dist[4]}개")
        with rating_col3:
            st.metric("3점", f"{rating_dist[3]}개")
        with rating_col4:
            st.metric("2점", f"{rating_dist[2]}개")
        with rating_col5:
            st.metric("1점", f"{rating_dist[1]}개")
    
    # 평점 히스토그램
    if 'rating_numeric' in product_df.columns:
        st.markdown("#### 평점 히스토그램")
        fig_hist = px.bar(
            x=list(rating_dist.keys()),
            y=list(rating_dist.values()),
            title=f"{product_display_name} 평점 분포",
            labels={'x': '평점', 'y': '리뷰 수'},
            color_discrete_sequence=['#4ecdc4']
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    # 월별 리뷰 수 추이
    if 'review_date' in product_df.columns:
        st.markdown("#### 월별 리뷰 수 추이")
        product_df_copy = product_df.copy()
        product_df_copy['review_date'] = pd.to_datetime(product_df_copy['review_date'], errors='coerce')
        monthly_reviews = product_df_copy.groupby(product_df_copy['review_date'].dt.to_period('M')).size()
        
        if not monthly_reviews.empty:
            fig_trend = px.line(
                x=[str(month) for month in monthly_reviews.index],
                y=monthly_reviews.values,
                title=f"{product_display_name} 월별 리뷰 수",
                labels={'x': '월', 'y': '리뷰 수'},
                color_discrete_sequence=['#ff6b6b']
            )
            fig_trend.update_traces(mode='lines+markers')
            
            # 비교 모드일 때 Y축 범위 통일
            if max_y_value is not None and max_y_value > 0:
                fig_trend.update_yaxes(range=[0, max_y_value * 1.1])
            
            st.plotly_chart(fig_trend, use_container_width=True)
    
    # 평점별 샘플 리뷰
    show_sample_reviews_by_rating(product_df, product_display_name)

def show_sample_reviews_by_rating(product_df, product_name):
    """평점별 샘플 리뷰 표시"""
    
    if 'rating_numeric' not in product_df.columns or 'review_text' not in product_df.columns:
        return
    
    st.markdown("#### 평점별 샘플 리뷰")
    
    for rating in [5, 4, 3, 2, 1]:
        rating_reviews = product_df[product_df['rating_numeric'] == rating]['review_text'].dropna()
        
        if not rating_reviews.empty:
            sample_count = min(5, len(rating_reviews))
            sample_reviews = rating_reviews.sample(n=sample_count) if len(rating_reviews) >= sample_count else rating_reviews
            
            with st.expander(f"{rating}점 리뷰 ({len(rating_reviews)}개 중 {len(sample_reviews)}개 샘플)"):
                for i, review in enumerate(sample_reviews.values, 1):
                    st.markdown(f"**리뷰 {i}:**")
                    st.markdown(f"> {review}")
                    st.markdown("---")

def show_timeseries_tab(df):
    """시계열 분석 탭"""
    
    # 기간 필터
    period_options = ["전체", "1주일", "1개월", "3개월", "6개월", "1년"]
    selected_period = st.selectbox(
        "분석 기간",
        period_options,
        key="timeseries_period"
    )
    
    # 기간 필터링
    filtered_df = filter_by_period(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"선택한 기간({selected_period})에 해당하는 데이터가 없습니다.")
        return
    
    # 필터링 결과
    if selected_period != "전체":
        st.caption(f"기간 필터링: {len(df):,}개 → {len(filtered_df):,}개 리뷰")
    
    if 'review_date' not in filtered_df.columns:
        st.warning("날짜 데이터가 없습니다.")
        return
    
    try:
        filtered_df['review_date'] = pd.to_datetime(filtered_df['review_date'], errors='coerce')
        time_df = filtered_df.dropna(subset=['review_date'])
        
        if time_df.empty:
            st.warning("유효한 날짜 데이터가 없습니다.")
            return
        
        # 시간 단위
        time_unit = st.radio(
            "시간 단위", 
            ["주별", "월별"], 
            horizontal=True,
            key="timeseries_unit"
        )
        
        if time_unit == "주별":
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
                labels={'x': x_label, 'y': '리뷰 수'},
                color_discrete_sequence=['#26a69a']
            )
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
            
            # 통계
            col1, col2, col3 = st.columns(3)
            col1.metric("총 기간", f"{len(period_counts)}개 기간")
            col2.metric("기간당 평균", f"{period_counts.mean():.1f}개")
            col3.metric("최대 리뷰", f"{period_counts.max()}개")
    
    except Exception as e:
        st.error(f"시계열 분석 중 오류: {e}")

def show_ai_insights_tab(df, category, sort_method):
    """AI Insights 탭"""
    
    st.subheader("AI 인사이트")
    st.caption("GPT를 활용한 데이터 분석 및 비즈니스 인사이트")
    
    # 기간 필터
    period_options = ["전체", "1주일", "1개월", "3개월", "6개월", "1년"]
    selected_period = st.selectbox(
        "분석 기간",
        period_options,
        key="ai_period"
    )
    
    # 기간 필터링
    filtered_df = filter_by_period(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"선택한 기간({selected_period})에 해당하는 데이터가 없습니다.")
        return
    
    # 필터링 결과
    if selected_period != "전체":
        st.caption(f"기간 필터링: {len(df):,}개 → {len(filtered_df):,}개 리뷰")
    
    # API 키 입력
    api_key = st.text_input(
        "OpenAI API Key 입력",
        type="password",
        help="GPT 분석을 위해 OpenAI API 키가 필요합니다"
    )
    
    if st.button("AI 인사이트 생성", type="primary"):
        if not api_key:
            st.error("API 키를 입력해주세요.")
            return
            
        with st.spinner("AI가 데이터를 분석중입니다..."):
            insights = generate_ai_insights(filtered_df, category, sort_method, selected_period, api_key)
            
            if insights:
                st.markdown("### 📊 AI 분석 결과")
                st.markdown(insights)
            else:
                st.error("AI 분석 중 오류가 발생했습니다.")

def generate_ai_insights(df, category, sort_method, period, api_key):
    """GPT를 사용한 인사이트 생성"""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # 데이터 요약 생성
        summary = create_data_summary(df, category, sort_method, period)
        
        # GPT 프롬프트
        prompt = f"""
다음은 다이소 {category} 카테고리의 {sort_method} 기준 TOP 100 제품 리뷰 데이터({period} 기간)입니다.

{summary}

위 데이터를 바탕으로 다음 관점에서 비즈니스 인사이트를 제공해주세요:

1. **제품 트렌드 분석**: 인기 제품들의 공통점과 특징
2. **고객 만족도 패턴**: 평점 분포와 고평점/저평점 제품의 특징  
3. **시장 기회**: 개선점이나 새로운 기회 영역
4. **리뷰 트렌드**: 시간별 리뷰 패턴의 의미

마크다운 형식으로 구조화하여 작성하고, 구체적인 수치를 인용하며 실용적인 비즈니스 제안을 포함해주세요.
"""
        
        # GPT API 호출 (신버전 문법)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 데이터 분석 전문가입니다. 제공된 리뷰 데이터를 분석하여 실용적인 비즈니스 인사이트를 제공합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"AI 분석 오류: {str(e)}")
        return None

def show_summary_report_tab(df, category, sort_method):
    """요약 리포트 탭"""
    
    st.subheader("분석 요약 리포트")
    st.caption("다이소 리뷰 데이터 분석 결과 종합 요약")
    
    # 기간 필터
    period_options = ["전체", "1주일", "1개월", "3개월", "6개월", "1년"]
    selected_period = st.selectbox(
        "리포트 기간",
        period_options,
        key="report_period"
    )
    
    # 기간 필터링
    filtered_df = filter_by_period(df, selected_period)
    
    if filtered_df.empty:
        st.warning(f"선택한 기간({selected_period})에 해당하는 데이터가 없습니다.")
        return
    
    # 리포트 생성
    generate_summary_report(filtered_df, category, sort_method, selected_period)

def generate_summary_report(df, category, sort_method, period):
    """요약 리포트 생성"""
    
    # 1. 리포트 헤더
    st.markdown("---")
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    st.markdown(f"""
    ## 📋 다이소 {category} {sort_method} 리포트
    **생성일시**: {current_time}  
    **분석기간**: {period}  
    **데이터 범위**: TOP 100 제품
    """)
    
    # 2. 핵심 지표 요약
    st.markdown("### 📊 핵심 지표")
    
    total_reviews = len(df)
    unique_products = df['product_name'].nunique() if 'product_name' in df.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 리뷰 수", f"{total_reviews:,}개")
    
    with col2:
        st.metric("분석 제품 수", f"{unique_products:,}개")
    
    with col3:
        if 'rating_numeric' in df.columns:
            avg_rating = df['rating_numeric'].mean()
            st.metric("평균 평점", f"{avg_rating:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    
    with col4:
        if 'text_length' in df.columns:
            avg_length = df['text_length'].mean()
            st.metric("평균 리뷰 길이", f"{avg_length:.0f}자")
        else:
            st.metric("평균 리뷰 길이", "N/A")
    
    # 3. 주요 발견사항
    st.markdown("### 🔍 주요 발견사항")
    
    insights = []
    
    # 제품 관련 인사이트
    if 'product_name' in df.columns:
        top_product = df['product_name'].value_counts().index[0]
        top_product_count = df['product_name'].value_counts().iloc[0]
        insights.append(f"**최다 리뷰 제품**: {top_product} ({top_product_count:,}개 리뷰)")
        
        if len(df['product_name'].value_counts()) >= 10:
            top_10_ratio = df['product_name'].value_counts().head(10).sum() / total_reviews * 100
            insights.append(f"**TOP 10 제품 집중도**: 전체 리뷰의 {top_10_ratio:.1f}%")
    
    # 평점 관련 인사이트
    if 'rating_numeric' in df.columns:
        rating_counts = df['rating_numeric'].value_counts().sort_index()
        if len(rating_counts) > 0:
            most_common_rating = rating_counts.idxmax()
            most_common_ratio = rating_counts.max() / len(df) * 100
            insights.append(f"**가장 빈번한 평점**: {most_common_rating}점 ({most_common_ratio:.1f}%)")
            
            high_rating_ratio = df[df['rating_numeric'] >= 4]['rating_numeric'].count() / len(df) * 100
            insights.append(f"**고평점 비율**: 4점 이상 {high_rating_ratio:.1f}%")
    
    # 시간 관련 인사이트
    if 'review_date' in df.columns:
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        valid_dates = df.dropna(subset=['review_date'])
        if not valid_dates.empty:
            date_range = (valid_dates['review_date'].max() - valid_dates['review_date'].min()).days
            insights.append(f"**데이터 수집 기간**: {date_range}일")
            
            # 최근 1개월 활동
            recent_month = valid_dates[valid_dates['review_date'] >= (datetime.now() - timedelta(days=30))]
            if not recent_month.empty:
                recent_ratio = len(recent_month) / len(valid_dates) * 100
                insights.append(f"**최근 1개월 리뷰 비율**: {recent_ratio:.1f}%")
    
    for insight in insights:
        st.markdown(f"- {insight}")
    
    # 4. 제품 성과 분석
    st.markdown("### 🏆 제품 성과 분석")
    
    if 'product_name' in df.columns and 'rating_numeric' in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 리뷰 활동 TOP 5**")
            top_reviewed = df['product_name'].value_counts().head(5)
            for i, (product, count) in enumerate(top_reviewed.items(), 1):
                st.markdown(f"{i}. {product}: {count:,}개")
        
        with col2:
            st.markdown("**⭐ 평점 우수 TOP 5**")
            product_ratings = df.groupby('product_name')['rating_numeric'].agg(['count', 'mean'])
            product_ratings = product_ratings[product_ratings['count'] >= 5]
            top_rated = product_ratings.sort_values('mean', ascending=False).head(5)
            
            for i, (product, data) in enumerate(top_rated.iterrows(), 1):
                st.markdown(f"{i}. {product}: {data['mean']:.2f}점")
    
    # 5. 시사점 및 제언
    st.markdown("### 💡 시사점 및 제언")
    
    recommendations = generate_recommendations(df, category, sort_method, period)
    for rec in recommendations:
        st.markdown(f"- {rec}")
    
    # 6. 리포트 다운로드
    st.markdown("### 📥 리포트 다운로드")
    
    report_text = create_downloadable_report(df, category, sort_method, period, insights, recommendations)
    
    st.download_button(
        label="📄 리포트 다운로드 (TXT)",
        data=report_text,
        file_name=f"다이소_{category}_{sort_method}_리포트_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

def generate_recommendations(df, category, sort_method, period):
    """제언 생성"""
    
    recommendations = []
    
    # 기본 제언
    if sort_method == "판매순":
        recommendations.append("판매순 상위 제품들의 공통 특징을 파악하여 신제품 기획에 활용")
    elif sort_method == "좋아요순":
        recommendations.append("좋아요순 상위 제품들의 만족 요소를 분석하여 품질 개선 포인트 도출")
    elif sort_method == "리뷰많은순":
        recommendations.append("리뷰가 많은 제품들의 화제성 요인을 분석하여 마케팅 전략 수립")
    
    # 평점 기반 제언
    if 'rating_numeric' in df.columns:
        avg_rating = df['rating_numeric'].mean()
        if avg_rating >= 4.5:
            recommendations.append("전반적으로 높은 고객 만족도를 보이므로 현재 제품 라인업 유지 권장")
        elif avg_rating >= 4.0:
            recommendations.append("양호한 만족도이나 4.5점 이상 달성을 위한 개선점 발굴 필요")
        else:
            recommendations.append("평점 개선을 위한 제품 품질 및 서비스 향상 방안 검토 필요")
    
    # 리뷰 활동 기반 제언
    total_reviews = len(df)
    unique_products = df['product_name'].nunique() if 'product_name' in df.columns else 0
    
    if unique_products > 0:
        avg_reviews_per_product = total_reviews / unique_products
        if avg_reviews_per_product > 100:
            recommendations.append("제품당 리뷰 수가 많아 고객 관심도가 높음. 리뷰 분석을 통한 개선점 도출 권장")
        else:
            recommendations.append("리뷰 참여 증대를 위한 인센티브 프로그램 도입 검토")
    
    return recommendations

def create_downloadable_report(df, category, sort_method, period, insights, recommendations):
    """다운로드 가능한 리포트 텍스트 생성"""
    
    current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    report_lines = [
        f"다이소 {category} {sort_method} 분석 리포트",
        "=" * 50,
        f"생성일시: {current_time}",
        f"분석기간: {period}",
        f"데이터 범위: TOP 100 제품",
        "",
        "핵심 지표",
        "-" * 20,
        f"총 리뷰 수: {len(df):,}개"
    ]
    
    if 'product_name' in df.columns:
        unique_products = df['product_name'].nunique()
        report_lines.append(f"분석 제품 수: {unique_products:,}개")
    
    if 'rating_numeric' in df.columns:
        avg_rating = df['rating_numeric'].mean()
        report_lines.append(f"평균 평점: {avg_rating:.2f}점")
    
    if 'text_length' in df.columns:
        avg_length = df['text_length'].mean()
        report_lines.append(f"평균 리뷰 길이: {avg_length:.0f}자")
    
    report_lines.extend([
        "",
        "주요 발견사항",
        "-" * 20
    ])
    
    for insight in insights:
        report_lines.append(insight.replace("**", "").replace("*", ""))
    
    report_lines.extend([
        "",
        "시사점 및 제언",
        "-" * 20
    ])
    
    for rec in recommendations:
        report_lines.append(rec)
    
    return "\n".join(report_lines)

def create_data_summary(df, category, sort_method, period):
    """데이터 요약 생성"""
    
    summary_parts = []
    
    # 기본 통계
    total_reviews = len(df)
    unique_products = df['product_name'].nunique() if 'product_name' in df.columns else 0
    summary_parts.append(f"- 총 리뷰 수: {total_reviews:,}개")
    summary_parts.append(f"- 제품 수: {unique_products:,}개")
    
    # 평점 정보
    if 'rating_numeric' in df.columns:
        avg_rating = df['rating_numeric'].mean()
        rating_dist = df['rating_numeric'].value_counts().sort_index()
        summary_parts.append(f"- 평균 평점: {avg_rating:.2f}점")
        summary_parts.append(f"- 평점 분포: {dict(rating_dist)}")
    
    # 인기 제품 TOP 5
    if 'product_name' in df.columns:
        top_products = df['product_name'].value_counts().head(5)
        summary_parts.append(f"- 리뷰 많은 제품 TOP 5: {dict(top_products)}")
    
    # 평점 높은 제품 TOP 5
    if 'rating_numeric' in df.columns and 'product_name' in df.columns:
        product_ratings = df.groupby('product_name')['rating_numeric'].agg(['count', 'mean'])
        product_ratings = product_ratings[product_ratings['count'] >= 3]
        top_rated = product_ratings.sort_values('mean', ascending=False).head(5)
        if not top_rated.empty:
            top_rated_dict = {name: f"{rating:.2f}점" for name, rating in top_rated['mean'].items()}
            summary_parts.append(f"- 평점 높은 제품 TOP 5: {top_rated_dict}")
    
    # 텍스트 길이 정보
    if 'text_length' in df.columns:
        avg_length = df['text_length'].mean()
        summary_parts.append(f"- 평균 리뷰 길이: {avg_length:.0f}자")
    
    # 시간 트렌드 (최근 데이터만)
    if 'review_date' in df.columns:
        df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        monthly_trend = df.groupby(df['review_date'].dt.to_period('M')).size().tail(6)
        if not monthly_trend.empty:
            trend_dict = {str(month): count for month, count in monthly_trend.items()}
            summary_parts.append(f"- 최근 6개월 월별 리뷰 수: {trend_dict}")
    
    return "\n".join(summary_parts)

def filter_by_period(df, period):
    """기간별 필터링"""
    
    if period == "전체" or 'review_date' not in df.columns:
        return df
    
    now = datetime.now()
    
    if period == "1주일":
        start_date = now - timedelta(weeks=1)
    elif period == "1개월":
        start_date = now - timedelta(days=30)
    elif period == "3개월":
        start_date = now - timedelta(days=90)
    elif period == "6개월":
        start_date = now - timedelta(days=180)
    elif period == "1년":
        start_date = now - timedelta(days=365)
    else:
        return df
    
    df_copy = df.copy()
    df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
    filtered_df = df_copy[df_copy['review_date'] >= start_date]
    
    return filtered_df

def add_to_history(analysis_text):
    """히스토리 추가"""
    
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    
    if analysis_text not in st.session_state.analysis_history:
        st.session_state.analysis_history.append(analysis_text)