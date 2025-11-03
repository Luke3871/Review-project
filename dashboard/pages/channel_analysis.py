"""
채널 분석 페이지
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
    PERIOD_OPTIONS
)

from analyzer.statistics import (
    calculate_basic_metrics,
    calculate_product_stats,
    calculate_brand_stats,
    calculate_rating_distribution,
    calculate_time_series,
    get_product_ranking,                          
)
from pages.analysis_helpers import (
    switch_to_page,
    show_clickable_chart,
    show_breadcrumb,
    initialize_filter_states
)

from analyzer.statistics.visualizations import (
    create_product_chart,
    create_brand_chart,
    create_rating_histogram,
    create_trend_chart,
)

from analyzer.txt_mining import (
    extract_keywords_tfidf,
    add_stopword,
    create_keyword_wordcloud,
    create_keyword_table,
    create_keyword_trend_chart,
)
def main():
    """채널 분석 메인"""
    
    st.header("📱 채널 분석")
    st.caption("채널별 리뷰 현황 및 상세 분석")
    
    # 필터 초기화
    initialize_filter_states()
    
    # 필터 UI
    show_filters()
    
    # 분석 결과 표시
    if st.session_state.get('channel_analysis_done', False):
        df = st.session_state.get('channel_analysis_df')
        if df is not None and not df.empty:
            show_analysis_results(df)


def show_filters():
    """필터 UI"""
    
    st.subheader("🔍 필터 설정")
    
    col1, col2, col3 = st.columns(3)
    
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
            key="channel_filter"
        )
    
    with col2:
        # "전체" 제거, 기본값 skincare
        categories = get_category_list(selected_channel)
        
        if not categories:
            st.error("카테고리 데이터가 없습니다.")
            return
        
        # 기본값 설정
        if st.session_state.selected_category not in categories:
            st.session_state.selected_category = 'skincare' if 'skincare' in categories else categories[0]
        
        selected_category = st.selectbox(
            "카테고리",
            categories,
            index=categories.index(st.session_state.selected_category),
            key="category_filter"
        )
    
    with col3:
        selected_period = st.selectbox(
            "기간",
            PERIOD_OPTIONS,
            index=PERIOD_OPTIONS.index(st.session_state.selected_period) if st.session_state.selected_period in PERIOD_OPTIONS else 0,
            key="period_filter"
        )
    
    # 분석 실행 버튼
    if st.button("🚀 분석 실행", type="primary", use_container_width=True):
        
        # 선택값 저장
        st.session_state.selected_channel = selected_channel
        st.session_state.selected_category = selected_category
        st.session_state.selected_period = selected_period
        
        with st.spinner("데이터 분석 중..."):
            df = load_filtered_data(
                channel=selected_channel,
                category=selected_category,
                period=selected_period
            )
            
            if df.empty:
                st.error("선택한 조건에 맞는 데이터가 없습니다.")
                st.session_state.channel_analysis_done = False
                return
            
            # DataFrame을 Session State에 저장
            st.session_state.channel_analysis_df = df
            st.session_state.channel_analysis_done = True

            # 분석 결과 자동 저장 (북마크)
            from utils.analysis_bookmark import save_analysis

            # 북마크 제목 생성
            title_parts = [selected_channel]
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
            save_analysis('channel', bookmark_title, filters, df)

            st.rerun()


def show_analysis_results(df):
    """분석 결과 표시"""
    
    channel_name = st.session_state.selected_channel
    
    # Breadcrumb
    show_breadcrumb([channel_name])
    
    st.success(f"✅ 총 {len(df):,}개 리뷰 분석 완료")
    
    st.markdown("---")
    
    # 분석 유형 탭
    tab1, tab2 = st.tabs(["📊 기본 통계", "📝 리뷰 분석"])

    with tab1:
        show_basic_statistics(df, channel_name)

    with tab2:
        show_text_mining_analysis(df, channel_name)


def show_basic_statistics(df, channel_name):
    """기본 통계 분석"""
    
    # ========== TOP 3 제품 카드 ==========
    st.subheader("🏆 제품 랭킹 TOP 20")
    
    ranking = get_product_ranking(df, top_n=20)
    
    if ranking.empty:
        st.warning("제품 데이터가 없습니다.")
        return
    
    # TOP 3 카드
    st.markdown("### TOP 3")
    col1, col2, col3 = st.columns(3)
    
    medals = ['🥇', '🥈', '🥉']
    
    for i, col in enumerate([col1, col2, col3]):
        if i >= len(ranking):
            break
        
        with col:
            product_row = ranking.iloc[i]
            rank = product_row['순위']
            
            # 정보 표시
            st.markdown(f"#### {medals[i]} {rank}위")
            st.markdown(f"**{product_row['제품명'][:40]}...**")  # ← 40자 + ...
            st.caption(f"🏷️ {product_row['브랜드']}")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("리뷰", f"{product_row['리뷰 수']:,}")
            with col_b:
                st.metric("평점", f"{product_row['평균 평점']}⭐")
            
            # 클릭 버튼
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("제품 분석", key=f"product_top{i}", use_container_width=True):
                    switch_to_page(
                        'product',
                        selected_channel=st.session_state.selected_channel,
                        selected_brand=product_row['브랜드'],
                        selected_product=product_row['제품명'],
                        selected_category=st.session_state.selected_category,
                        selected_period=st.session_state.selected_period
                    )
            with col_btn2:
                if st.button("브랜드 분석", key=f"brand_top{i}", use_container_width=True):
                    switch_to_page(
                        'brand',
                        selected_channel=st.session_state.selected_channel,
                        selected_brand=product_row['브랜드'],
                        selected_category=st.session_state.selected_category,
                        selected_period=st.session_state.selected_period
                    )
    
    st.markdown("---")
    
    # ========== 4~20위 테이블 (클릭 가능) ==========
    st.markdown("### 4위 ~ 20위")
    st.caption("💡 표에서 행을 클릭하면 상세 분석으로 이동할 수 있습니다")
    
    if len(ranking) > 3:
        # 표시용 데이터프레임 (제품명 축약)
        ranking_display = ranking.iloc[3:].copy()
        ranking_display['제품명_축약'] = ranking_display['제품명'].str[:60] + '...'  # ← 60자로 축약
        
        event = st.dataframe(
            ranking_display[['순위', '제품명_축약', '브랜드', '리뷰 수', '평균 평점']].rename(columns={'제품명_축약': '제품명'}),
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # 행 선택 시
        if event.selection.rows:
            selected_idx = event.selection.rows[0] + 3  # 3부터 시작이니까
            selected_product = ranking.iloc[selected_idx]
            
            # 전체 제품명 표시
            st.success(f"✅ 선택: {selected_product['제품명']}")
            st.caption(f"브랜드: {selected_product['브랜드']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 제품 분석 보기", key="goto_product", use_container_width=True, type="primary"):
                    switch_to_page(
                        'product',
                        selected_channel=st.session_state.selected_channel,
                        selected_brand=selected_product['브랜드'],
                        selected_product=selected_product['제품명'],
                        selected_category=st.session_state.selected_category,
                        selected_period=st.session_state.selected_period
                    )
            with col2:
                if st.button("🏷️ 브랜드 분석 보기", key="goto_brand", use_container_width=True):
                    switch_to_page(
                        'brand',
                        selected_channel=st.session_state.selected_channel,
                        selected_brand=selected_product['브랜드'],
                        selected_category=st.session_state.selected_category,
                        selected_period=st.session_state.selected_period
                    )
    
    st.markdown("---")
    
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
        selected_channel=st.session_state.selected_channel,
        selected_brand=product_brand,
        selected_product=product_name,
        selected_category=st.session_state.selected_category,
        selected_period=st.session_state.selected_period
    )

def show_text_mining_analysis(df, channel_name):
    """텍스트 마이닝 분석 (키워드)"""

    st.subheader("📝 키워드 분석")

    # 최소 데이터 검증
    if len(df) < 50:
        st.warning("⚠️ 분석 가능한 데이터가 너무 적습니다 (최소 50개 리뷰 필요)")
        st.info(f"현재 리뷰 수: {len(df)}개")
        return

    # 샘플링 (전체의 10%)
    total_reviews = len(df)
    sample_size = max(int(total_reviews * 0.1), 50)  # 최소 50개 보장

    if total_reviews > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42)
        st.info(f"📊 전체 {total_reviews:,}개 리뷰 중 {sample_size:,}개({(sample_size/total_reviews*100):.1f}%)를 랜덤 샘플링하여 분석합니다.")
    else:
        df_sample = df
        st.info(f"📊 전체 {total_reviews:,}개 리뷰를 분석합니다.")

    # 키워드 추출
    with st.spinner("키워드 분석 중..."):
        keyword_df, keyword_to_indices = extract_keywords_tfidf(df_sample, channel_name, top_n=30)

    if keyword_df.empty:
        st.warning("추출된 키워드가 없습니다.")
        return
    
    # 1. 워드클라우드
    st.markdown("### 📊 키워드 워드클라우드")
    wordcloud_fig = create_keyword_wordcloud(keyword_df, title=f"{channel_name} 주요 키워드")
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
                df_sample,
                selected_keywords,
                time_unit,
                channel_name,
                keyword_to_indices
            )
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)
            else:
                st.warning("트렌드 차트를 생성할 수 없습니다.")

    st.markdown("---")

    # 3. 키워드 테이블 (클릭 가능)
    st.markdown("### 📋 TOP 30 키워드 상세")
    st.caption("💡 키워드를 클릭하면 속성 분석 페이지로 이동합니다")
    
    keyword_table_df = create_keyword_table(keyword_df)
    
    event = st.dataframe(
        keyword_table_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # 클릭 이벤트 처리
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_keyword = keyword_df.iloc[selected_idx]['키워드']
        
        st.success(f"✅ 선택된 키워드: **{selected_keyword}**")
        
        if st.button("🔍 속성 분석 페이지로 이동", type="primary", use_container_width=True):
            switch_to_page(
                'attribute',
                selected_channel=st.session_state.selected_channel,
                selected_category=st.session_state.selected_category,
                selected_period=st.session_state.selected_period,
                selected_keyword=selected_keyword
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
                    from analyzer.txt_mining import add_stopword

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
                st.session_state['show_stopwords_channel'] = not st.session_state.get('show_stopwords_channel', False)

        # 불용어 목록 표시 (토글)
        if st.session_state.get('show_stopwords_channel', False):
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