"""
제품 분석 페이지
"""
import streamlit as st
import sys
import os

# 경로 설정
dashboard_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(dashboard_dir)
sys.path.insert(0, dashboard_dir)
sys.path.insert(0, project_root)

from dashboard_config import (
    get_available_channels,
    get_brand_list,
    get_product_list,
    get_selected_options,
    load_filtered_data,
    PERIOD_OPTIONS
)

from analyzer.statistics import (
    calculate_basic_metrics,
    calculate_rating_distribution,
    calculate_time_series,
    create_rating_histogram,
    create_rating_bar_chart,
    create_trend_chart
)

from analyzer.txt_mining import (
    extract_keywords_tfidf,
    add_stopword,
    create_keyword_wordcloud,
    create_keyword_table,
    create_keyword_trend_chart,
)

from pages.analysis_helpers import (
    show_breadcrumb,
    initialize_filter_states
)


def main():
    """제품 분석 메인"""
    
    st.header("📦 제품 분석")
    st.caption("제품별 상세 리뷰 분석")
    
    # 필터 초기화
    initialize_filter_states()
    
    # 필터 UI
    show_filters()
    
    # 분석 결과 표시
    if st.session_state.get('product_analysis_done', False):
        df = st.session_state.get('product_analysis_df')
        if df is not None and not df.empty:
            show_analysis_results(df)


def show_filters():
    """필터 UI"""
    
    st.subheader("🔍 필터 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        channels = get_available_channels()
        if not channels:
            st.error("채널 데이터를 불러올 수 없습니다.")
            return
        
        if st.session_state.selected_channel not in channels:
            st.session_state.selected_channel = channels[0]
        
        selected_channel = st.selectbox(
            "채널",
            channels,
            index=channels.index(st.session_state.selected_channel),
            key="product_channel_filter"
        )
    
    with col2:
        brands = get_brand_list(selected_channel)
        if not brands:
            st.warning("브랜드 데이터가 없습니다.")
            return
        
        if st.session_state.selected_brand not in brands:
            st.session_state.selected_brand = brands[0]
        
        selected_brand = st.selectbox(
            "브랜드",
            brands,
            index=brands.index(st.session_state.selected_brand),
            key="product_brand_filter"
        )
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        products = get_product_list(selected_channel, selected_brand)
        if not products:
            st.warning("제품 데이터가 없습니다.")
            return
        
        if st.session_state.selected_product not in products:
            st.session_state.selected_product = products[0]
        
        selected_product = st.selectbox(
            "제품",
            products,
            index=products.index(st.session_state.selected_product),
            key="product_filter"
        )
    
    with col4:
        options = ["전체"] + get_selected_options(selected_channel, selected_brand, None, selected_product)
        selected_option = st.selectbox(
            "기획(옵션)",
            options,
            index=options.index(st.session_state.selected_option) if st.session_state.selected_option in options else 0,
            key="product_option_filter"
        )
    
    with col5:
        selected_period = st.selectbox(
            "기간",
            PERIOD_OPTIONS,
            index=PERIOD_OPTIONS.index(st.session_state.selected_period) if st.session_state.selected_period in PERIOD_OPTIONS else 0,
            key="product_period_filter"
        )
    
    # 분석 실행 버튼
    if st.button("🚀 분석 실행", type="primary", use_container_width=True):
        
        # 선택값 저장
        st.session_state.selected_channel = selected_channel
        st.session_state.selected_brand = selected_brand
        st.session_state.selected_product = selected_product
        st.session_state.selected_option = selected_option
        st.session_state.selected_period = selected_period
        
        with st.spinner("데이터 분석 중..."):
            df = load_filtered_data(
                channel=selected_channel,
                brand=selected_brand,
                product=selected_product,
                option=selected_option if selected_option != "전체" else None,
                period=selected_period
            )
            
            if df.empty:
                st.error("선택한 조건에 맞는 데이터가 없습니다.")
                st.session_state.product_analysis_done = False
                return
            
            # DataFrame을 Session State에 저장
            st.session_state.product_analysis_df = df
            st.session_state.product_analysis_done = True

            # 분석 결과 자동 저장 (북마크)
            from utils.analysis_bookmark import save_analysis

            # 북마크 제목 생성
            title_parts = [selected_channel, selected_brand, selected_product]
            bookmark_title = " > ".join(title_parts)

            # 필터 조건 저장
            filters = {
                'selected_channel': selected_channel,
                'selected_brand': selected_brand,
                'selected_product': selected_product,
                'selected_option': selected_option,
                'selected_period': selected_period
            }

            # 자동 저장
            save_analysis('product', bookmark_title, filters, df)

            st.rerun()


def show_analysis_results(df):
    """분석 결과 표시"""
    
    channel_name = st.session_state.selected_channel
    brand_name = st.session_state.selected_brand
    product_name = st.session_state.selected_product
    
    # Breadcrumb
    breadcrumb_items = [channel_name, brand_name, product_name]
    if st.session_state.selected_option != "전체":
        breadcrumb_items.append(st.session_state.selected_option)
    
    show_breadcrumb(breadcrumb_items)
    
    st.success(f"✅ 총 {len(df):,}개 리뷰 분석 완료")
    
    st.markdown("---")
    
    # 분석 유형 탭
    tab1, tab2 = st.tabs(["📊 기본 통계", "📝 키워드 분석"])

    with tab1:
        show_basic_statistics(df, product_name)

    with tab2:
        show_text_mining_analysis(df, product_name)


def show_basic_statistics(df, product_name):
    """기본 통계 분석"""
    
    # 기본 메트릭
    st.subheader("📈 기본 지표")
    
    metrics = calculate_basic_metrics(df)
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("총 리뷰", f"{metrics['total_reviews']:,}개")
    with col2:
        if metrics['avg_rating']:
            st.metric("평균 평점", f"{metrics['avg_rating']:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    
    st.markdown("---")
    
    # 평점 분포
    st.subheader("⭐ 평점 분포")
    
    rating_dist = calculate_rating_distribution(df)
    
    if rating_dist:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = create_rating_histogram(rating_dist['valid_ratings'], "평점 히스토그램")
            st.plotly_chart(fig, use_container_width=True, key="product_rating_hist")
        
        with col2:
            fig = create_rating_bar_chart(rating_dist['distribution'], "평점별 리뷰 수")
            st.plotly_chart(fig, use_container_width=True, key="product_rating_bar")
        
        # 통계
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("평균", f"{rating_dist['stats']['mean']:.2f}")
        col_b.metric("중앙값", f"{rating_dist['stats']['median']:.2f}")
        col_c.metric("표준편차", f"{rating_dist['stats']['std']:.2f}")
    
    st.markdown("---")
    
    # 트렌드
    st.subheader("📈 시간별 리뷰 트렌드")
    
    time_series = calculate_time_series(df, 'M')
    
    if time_series is not None and not time_series.empty:
        fig = create_trend_chart(time_series, "월별 리뷰 수", "월")
        st.plotly_chart(fig, use_container_width=True, key="product_trend")
        
        # 통계
        col1, col2, col3 = st.columns(3)
        col1.metric("총 기간", f"{len(time_series)}개월")
        col2.metric("월평균", f"{time_series.mean():.1f}개")
        col3.metric("최대", f"{time_series.max()}개")
    
    st.markdown("---")
    
    # 최근 리뷰 샘플
    st.subheader("📝 최근 리뷰 10개")
    
    if 'review_text' in df.columns and 'review_date' in df.columns:
        # review_date로 정렬 가능한지 확인
        df_sorted = df.copy()
        
        # review_date가 datetime이 아니면 변환
        if df_sorted['review_date'].dtype == 'object':
            import pandas as pd
            df_sorted['review_date'] = pd.to_datetime(df_sorted['review_date'], errors='coerce')
        
        # 정렬 후 상위 10개
        recent_reviews = df_sorted.nlargest(10, 'review_date')
        
        # 표시할 컬럼 선택
        display_columns = ['review_date', 'review_text']
        if 'rating' in recent_reviews.columns:
            display_columns.append('rating')
        
        st.dataframe(
            recent_reviews[display_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("리뷰 텍스트 데이터가 없습니다.")


def show_text_mining_analysis(df, product_name):
    """텍스트 마이닝 분석 (키워드)"""

    st.subheader("📝 키워드 분석")

    # 최소 데이터 검증
    if len(df) < 50:
        st.warning("⚠️ 분석 가능한 데이터가 너무 적습니다 (최소 50개 리뷰 필요)")
        st.info(f"현재 리뷰 수: {len(df)}개")
        return

    # 채널명 추출 (키워드 추출에 사용)
    channel_name = df['channel'].iloc[0] if 'channel' in df.columns else None

    # 키워드 추출
    with st.spinner("키워드 분석 중..."):
        keyword_df, keyword_to_indices = extract_keywords_tfidf(df, channel_name, top_n=30)

    if keyword_df.empty:
        st.warning("추출된 키워드가 없습니다.")
        return

    # 1. 워드클라우드
    st.markdown("### 📊 키워드 워드클라우드")
    wordcloud_fig = create_keyword_wordcloud(keyword_df, title=f"{product_name} 주요 키워드")
    if wordcloud_fig:
        # 표시 크기를 살짝 작게 조절 (원본 해상도는 유지)
        col1, col2, col3 = st.columns([1.5, 3, 1.5])
        with col2:
            st.pyplot(wordcloud_fig, use_container_width=False)

    st.markdown("---")

    # 2. 키워드 시간대별 트렌드
    st.markdown("### 📈 키워드 트렌드 분석")

    # 키워드 선택 UI
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_keywords = st.multiselect(
            "비교할 키워드를 선택하세요 (최대 5개)",
            options=keyword_df['키워드'].tolist(),
            default=keyword_df['키워드'].tolist()[:3],  # 기본으로 상위 3개 선택
            max_selections=5
        )
    with col2:
        time_unit = st.radio("시간 단위", ["월별", "주별"], horizontal=True)

    if selected_keywords:
        with st.spinner("트렌드 차트 생성 중..."):
            trend_fig = create_keyword_trend_chart(
                df,
                selected_keywords,
                time_unit,
                product_name,
                keyword_to_indices
            )
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.warning("트렌드 차트를 생성할 수 없습니다.")

    st.markdown("---")

    # 3. 키워드 테이블
    st.markdown("### 📋 TOP 30 키워드 상세")

    keyword_table_df = create_keyword_table(keyword_df)

    st.dataframe(
        keyword_table_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # 3. 불용어 관리 (expander)
    show_stopwords_manager(channel_name)


def show_stopwords_manager(channel_name):
    """불용어 관리 UI"""

    with st.expander("⚙️ 불용어 관리"):
        st.caption("새로운 불용어를 추가하여 키워드 분석 품질을 높일 수 있습니다")

        from analyzer.txt_mining import get_category_options, load_stopwords

        col1, col2 = st.columns([3, 1])

        with col1:
            new_stopword = st.text_input(
                "추가할 불용어",
                placeholder="예: 구매, 제품, 사용",
                key="new_stopword_input"
            )

        with col2:
            # 동적 카테고리 옵션 가져오기
            category_options = get_category_options(channel_name)

            # 기본값: 현재 채널 (있으면) 또는 common
            default_idx = 0
            if channel_name and channel_name.lower() in category_options:
                default_idx = list(category_options.keys()).index(channel_name.lower())

            selected_display = st.selectbox(
                "카테고리",
                options=list(category_options.values()),
                index=default_idx,
                key="stopword_category"
            )

            # 표시 텍스트에서 실제 카테고리 키 추출
            category = list(category_options.keys())[
                list(category_options.values()).index(selected_display)
            ]

        # 선택된 카테고리의 현재 불용어 수 표시
        current_stopwords = load_stopwords(f"stopwords_{category}.txt")
        st.caption(f"현재 {len(current_stopwords)}개의 불용어가 등록되어 있습니다")

        memo = st.text_input(
            "메모 (선택사항)",
            placeholder="예: 일반적인 구매 관련 단어",
            key="stopword_memo"
        )

        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

        with col_btn1:
            if st.button("➕ 불용어 추가", use_container_width=True):
                if new_stopword and new_stopword.strip():
                    add_stopword(
                        category=category,
                        word=new_stopword.strip(),
                        user=st.session_state.get('username', 'unknown'),
                        memo=memo
                    )
                    st.success(f"✅ '{new_stopword}' → {category} 추가 완료!")
                    st.info("💡 재분석 버튼을 눌러 새로운 불용어를 적용하세요")
                else:
                    st.warning("불용어를 입력해주세요")

        with col_btn2:
            if st.button("🔄 재분석", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        with col_btn3:
            if st.button("📋 불용어 보기", use_container_width=True):
                st.session_state['show_stopwords_product'] = not st.session_state.get('show_stopwords_product', False)

        # 불용어 목록 표시 (토글)
        if st.session_state.get('show_stopwords_product', False):
            st.markdown(f"**{category} 카테고리 불용어 목록 ({len(current_stopwords)}개)**")

            # 3열로 표시
            stopwords_list = sorted(current_stopwords)
            if stopwords_list:
                cols = st.columns(3)
                for idx, word in enumerate(stopwords_list[:100]):  # 최대 100개만 표시
                    cols[idx % 3].text(f"• {word}")

                if len(stopwords_list) > 100:
                    st.caption(f"... 외 {len(stopwords_list) - 100}개")
            else:
                st.info("등록된 불용어가 없습니다")


if __name__ == "__main__":
    main()