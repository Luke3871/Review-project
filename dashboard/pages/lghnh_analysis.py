"""
LG생활건강 분석 페이지
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
    get_category_list,
    load_filtered_data,
    PERIOD_OPTIONS,
    LGHH_BRANDS
)

from analyzer.statistics import (
    calculate_basic_metrics,
    calculate_product_stats,
    calculate_brand_stats,
    calculate_rating_distribution,
    calculate_time_series,
    create_product_chart,
    create_brand_chart,
    create_rating_histogram,
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
    switch_to_page,
    show_clickable_chart,
    initialize_filter_states
)


def main():
    """LG생활건강 분석 메인"""
    
    st.header("⭐ LG생활건강 제품 분석")
    st.caption("LG생건 브랜드 제품 집중 분석")
    
    # 필터 초기화
    initialize_filter_states()
    
    # 필터 UI
    show_filters()
    
    # 분석 결과 표시
    if st.session_state.get('lghh_analysis_done', False):
        df = st.session_state.get('lghh_analysis_df')
        if df is not None and not df.empty:
            show_analysis_results(df)


def show_filters():
    """필터 UI"""
    
    st.subheader("🔍 필터 설정")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        channels = ["전체"] + get_available_channels()
        selected_channel = st.selectbox(
            "채널",
            channels,
            index=channels.index(st.session_state.selected_channel) if st.session_state.selected_channel in channels else 0,
            key="lghh_channel_filter"
        )
    
    with col2:
        categories = ["전체"] + get_category_list(selected_channel if selected_channel != "전체" else None)
        selected_category = st.selectbox(
            "카테고리",
            categories,
            index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0,
            key="lghh_category_filter"
        )
    
    with col3:
        selected_period = st.selectbox(
            "기간",
            PERIOD_OPTIONS,
            index=PERIOD_OPTIONS.index(st.session_state.selected_period) if st.session_state.selected_period in PERIOD_OPTIONS else 0,
            key="lghh_period_filter"
        )
    
    # 분석 실행 버튼
    if st.button("🚀 분석 실행", type="primary", use_container_width=True):
        
        with st.spinner("데이터 분석 중..."):
            df = load_filtered_data(
                channel=selected_channel if selected_channel != "전체" else None,
                category=selected_category if selected_category != "전체" else None,
                period=selected_period
            )
            
            if df.empty:
                st.error("데이터를 불러올 수 없습니다.")
                st.session_state.lghh_analysis_done = False
                return
            
            # LG생건 필터링
            lghh_df = df[df['brand'].isin(LGHH_BRANDS)]
            
            if lghh_df.empty:
                st.warning("LG생활건강 제품 데이터가 없습니다.")
                st.session_state.lghh_analysis_done = False
                return
            
            # DataFrame을 Session State에 저장
            st.session_state.lghh_analysis_df = lghh_df
            st.session_state.lghh_analysis_done = True

            # 선택값 저장
            st.session_state.selected_channel = selected_channel
            st.session_state.selected_category = selected_category
            st.session_state.selected_period = selected_period

            # 분석 결과 자동 저장 (북마크)
            from utils.analysis_bookmark import save_analysis

            # 북마크 제목 생성
            title_parts = ["LG생활건강"]
            if selected_channel != "전체":
                title_parts.append(selected_channel)
            if selected_category != "전체":
                title_parts.append(selected_category)
            bookmark_title = " > ".join(title_parts)

            # 필터 조건 저장
            filters = {
                'selected_channel': selected_channel,
                'selected_category': selected_category,
                'selected_period': selected_period
            }

            # 자동 저장
            save_analysis('lghnh', bookmark_title, filters, lghh_df)

            st.rerun()


def show_analysis_results(df):
    """분석 결과 표시"""
    
    st.success(f"✅ LG생활건강 {len(df):,}개 리뷰 분석 완료")
    
    st.markdown("---")
    
    # 분석 유형 탭
    tab1, tab2 = st.tabs(["📊 기본 통계", "📝 키워드 분석"])

    with tab1:
        show_basic_statistics(df)

    with tab2:
        show_text_mining_analysis(df)


def show_basic_statistics(df):
    """기본 통계 분석"""
    
    # 기본 메트릭
    st.subheader("📈 기본 지표")
    
    metrics = calculate_basic_metrics(df)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("LG생건 리뷰", f"{metrics['total_reviews']:,}개")
    with col2:
        st.metric("제품 수", f"{metrics['unique_products']:,}개")
    with col3:
        if metrics['avg_rating']:
            st.metric("평균 평점", f"{metrics['avg_rating']:.2f}점")
        else:
            st.metric("평균 평점", "N/A")
    with col4:
        st.metric("브랜드 수", f"{metrics['unique_brands']:,}개")
    
    st.markdown("---")
    
    # LG생건 브랜드별
    st.subheader("🏷️ LG생활건강 브랜드별 리뷰 수")
    
    brand_stats = calculate_brand_stats(df, top_n=15)
    
    if brand_stats and not brand_stats['review_counts'].empty:
        fig = create_brand_chart(brand_stats['review_counts'], "LG생건 브랜드별 리뷰 수")
        
        # 클릭 가능한 차트
        show_clickable_chart(
            fig,
            "lghh_brand_chart",
            lambda brand: switch_to_page(
                'brand',
                selected_channel=st.session_state.get('selected_channel', '전체'),
                selected_brand=brand,
                selected_category=st.session_state.get('selected_category', '전체'),
                selected_period=st.session_state.get('selected_period', '전체')
            )
        )
        
        st.caption("💡 차트를 클릭하면 해당 브랜드 상세 분석으로 이동합니다")
    else:
        st.warning("브랜드 데이터가 없습니다.")
    
    st.markdown("---")
    
    # LG생건 제품별
    st.subheader("📦 LG생활건강 제품별 리뷰 수 TOP 15")
    
    product_stats = calculate_product_stats(df, top_n=15)
    
    if product_stats and not product_stats['review_counts'].empty:
        fig = create_product_chart(product_stats['review_counts'], "LG생건 제품별 리뷰 수")
        
        # 클릭 가능한 차트
        show_clickable_chart(
            fig,
            "lghh_product_chart",
            lambda product: handle_product_click(df, product)
        )
        
        st.caption("💡 차트를 클릭하면 해당 제품 상세 분석으로 이동합니다")
    else:
        st.warning("제품 데이터가 없습니다.")
    
    st.markdown("---")
    
    # 평점 & 트렌드
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⭐ 평점 분포")
        rating_dist = calculate_rating_distribution(df)
        if rating_dist:
            fig = create_rating_histogram(rating_dist['valid_ratings'], "LG생건 평점 분포")
            st.plotly_chart(fig, use_container_width=True, key="lghh_rating_hist")
    
    with col2:
        st.subheader("📈 트렌드")
        time_series = calculate_time_series(df, 'M')
        if time_series is not None and not time_series.empty:
            fig = create_trend_chart(time_series, "LG생건 월별 리뷰 수", "월")
            st.plotly_chart(fig, use_container_width=True, key="lghh_trend")


def handle_product_click(df, product_name):
    """제품 클릭 처리 - 브랜드 정보 포함"""
    
    # 해당 제품의 브랜드 찾기
    product_brand = None
    if 'brand' in df.columns:
        product_df = df[df['product_name'] == product_name]
        if not product_df.empty:
            product_brand = product_df['brand'].iloc[0]
    
    switch_to_page(
        'product',
        selected_channel=st.session_state.get('selected_channel', '전체'),
        selected_brand=product_brand,
        selected_product=product_name,
        selected_category=st.session_state.get('selected_category', '전체'),
        selected_period=st.session_state.get('selected_period', '전체')
    )


def show_text_mining_analysis(df):
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
    wordcloud_fig = create_keyword_wordcloud(keyword_df, title="LG생활건강 주요 키워드")
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
                "LG생활건강",
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
                st.session_state['show_stopwords_lghnh'] = not st.session_state.get('show_stopwords_lghnh', False)

        # 불용어 목록 표시 (토글)
        if st.session_state.get('show_stopwords_lghnh', False):
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
