import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime, timedelta

def load_existing_newwords(category):
    """기존 신조어 사전 로딩"""
    file_path = f"../analyzer/txt_mining/words_dictionary/newwords/newwords_{category}.txt"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        return set(words)
    except FileNotFoundError:
        return set()

def save_newword_to_file(word, category):
    """신조어를 해당 카테고리 파일에 저장"""
    file_path = f"../analyzer/txt_mining/words_dictionary/newwords/newwords_{category}.txt"
    
    # 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # 기존 단어 목록 불러오기
    existing_words = load_existing_newwords(category)
    
    # 중복 체크
    if word not in existing_words:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{word}\n")
        return True
    return False

def search_word_in_reviews(word, filtered_df):
    """리뷰 데이터에서 특정 단어 검색"""
    if filtered_df.empty or 'review_text' not in filtered_df.columns:
        return pd.DataFrame(), 0
    
    # 대소문자 구분 없이 검색
    pattern = re.compile(re.escape(word), re.IGNORECASE)
    
    # 해당 단어가 포함된 리뷰 찾기
    matching_reviews = filtered_df[
        filtered_df['review_text'].fillna('').str.contains(pattern, na=False)
    ].copy()
    
    if not matching_reviews.empty:
        # 해당 단어가 포함된 부분 하이라이팅을 위한 컨텍스트 추출
        matching_reviews['highlighted_text'] = matching_reviews['review_text'].apply(
            lambda x: highlight_word_in_text(x, word) if pd.notna(x) else ""
        )
    
    return matching_reviews, len(matching_reviews)

def highlight_word_in_text(text, word, context_length=50):
    """텍스트에서 단어 주변 문맥과 함께 하이라이팅"""
    if not text or pd.isna(text):
        return ""
    
    text = str(text)
    pattern = re.compile(re.escape(word), re.IGNORECASE)
    
    # 첫 번째 매치 찾기
    match = pattern.search(text)
    if match:
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        
        context = text[start:end]
        # 하이라이팅된 단어로 교체
        highlighted = pattern.sub(f"**{word}**", context)
        
        # 앞뒤가 잘렸으면 ... 추가
        if start > 0:
            highlighted = "..." + highlighted
        if end < len(text):
            highlighted = highlighted + "..."
            
        return highlighted
    
    return text[:100] + "..." if len(text) > 100 else text

def analyze_word_by_products(word, matching_reviews):
    """제품별 신조어 사용 현황 분석"""
    if matching_reviews.empty or 'product_name' not in matching_reviews.columns:
        return []
    
    product_analysis = []
    
    # 제품별 그룹화
    for product_name in matching_reviews['product_name'].unique():
        product_reviews = matching_reviews[matching_reviews['product_name'] == product_name]
        
        # 기본 정보
        usage_count = len(product_reviews)
        
        # 평균 평점 계산
        if 'rating' in product_reviews.columns:
            rating_values = []
            for rating in product_reviews['rating']:
                try:
                    # "5점" -> 5로 변환
                    rating_num = float(str(rating).replace('점', ''))
                    rating_values.append(rating_num)
                except:
                    continue
            avg_rating = sum(rating_values) / len(rating_values) if rating_values else 0
        else:
            avg_rating = 0
        
        # 카테고리 정보
        category = product_reviews['category'].iloc[0] if 'category' in product_reviews.columns else 'Unknown'
        
        # 최근 사용일
        if 'review_date' in product_reviews.columns:
            recent_date = product_reviews['review_date'].max()
            recent_date_str = recent_date.strftime('%Y-%m-%d') if pd.notna(recent_date) else 'N/A'
        else:
            recent_date_str = 'N/A'
        
        product_analysis.append({
            '제품명': product_name,
            '사용횟수': usage_count,
            '평균평점': f"{avg_rating:.2f}점" if avg_rating > 0 else "N/A",
            '카테고리': category,
            '최근사용일': recent_date_str
        })
    
    # 사용 횟수 기준으로 정렬
    product_analysis.sort(key=lambda x: x['사용횟수'], reverse=True)
    
    return product_analysis

def analyze_word_statistics(word, matching_reviews):
    """단어 사용 통계 분석"""
    if matching_reviews.empty:
        return {}
    
    # 기본 통계
    total_mentions = len(matching_reviews)
    
    # 카테고리별 분포
    category_dist = matching_reviews['category'].value_counts().to_dict() if 'category' in matching_reviews.columns else {}
    
    # 평점별 분포
    if 'rating' in matching_reviews.columns:
        rating_dist = matching_reviews['rating'].value_counts().to_dict()
    else:
        rating_dist = {}
    
    # 시간별 분포 (월별)
    if 'review_date' in matching_reviews.columns:
        matching_reviews['month'] = pd.to_datetime(matching_reviews['review_date'], errors='coerce').dt.to_period('M')
        monthly_dist = matching_reviews['month'].value_counts().sort_index().to_dict()
        monthly_dist = {str(k): v for k, v in monthly_dist.items() if pd.notna(k)}
    else:
        monthly_dist = {}
    
    return {
        'total_mentions': total_mentions,
        'category_distribution': category_dist,
        'rating_distribution': rating_dist,
        'monthly_distribution': monthly_dist
    }

def render_newword_analysis_tab():
    """신조어 분석 탭 렌더링"""
    st.header("신조어 분석")
    st.caption("사용자 입력 단어의 리뷰 내 사용 현황 분석 및 신조어 사전 관리")
    
    # 데이터 로딩
    from tab1_daiso_section import load_daiso_data
    
    daiso_df = load_daiso_data()
    
    if daiso_df.empty:
        st.error("다이소 데이터를 로딩할 수 없습니다.")
        return
    
    # 기본 필터링
    col1, col2 = st.columns(2)
    
    with col1:
        if 'category' in daiso_df.columns:
            categories = ['전체'] + list(daiso_df['category'].unique())
            selected_category = st.selectbox("분석 카테고리", categories, key="newword_category")
        else:
            selected_category = '전체'
    
    with col2:
        date_filter = st.selectbox(
            "기간 필터", 
            ["전체", "최근 1개월", "최근 3개월", "최근 6개월"],
            key="newword_date_filter"
        )
    
    # 데이터 필터링
    filtered_df = daiso_df.copy()
    
    # SALES 정렬만 필터링 (기본)
    if 'sort_type' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['sort_type'] == 'SALES']
    
    if selected_category != '전체':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # 날짜 필터링
    if date_filter != "전체" and 'review_date' in filtered_df.columns:
        today = datetime.now()
        
        if date_filter == "최근 1개월":
            cutoff_date = today - timedelta(days=30)
        elif date_filter == "최근 3개월":
            cutoff_date = today - timedelta(days=90)
        else:  # 최근 6개월
            cutoff_date = today - timedelta(days=180)
        
        filtered_df = filtered_df[filtered_df['review_date'] >= cutoff_date]
    
    st.info(f"분석 대상: {len(filtered_df):,}개 리뷰")
    
    st.markdown("---")
    
    # 메인 기능들
    tab1, tab2, tab3 = st.tabs(["단어 검색", "신조어 사전 관리", "통계 분석"])
    
    with tab1:
        st.subheader("단어 검색 및 분석")
        
        # 검색어 입력
        search_word = st.text_input(
            "검색할 단어를 입력하세요",
            placeholder="예: 갓템, 핫템, 꿀템, 레전드, 쫀득, 촉촉 등",
            key="search_word_input"
        )
        
        if search_word:
            with st.spinner(f"'{search_word}' 검색 중..."):
                matching_reviews, total_count = search_word_in_reviews(search_word, filtered_df)
                
                if total_count > 0:
                    st.success(f"**'{search_word}'**가 포함된 리뷰 **{total_count:,}개** 발견!")
                    
                    # 통계 분석
                    stats = analyze_word_statistics(search_word, matching_reviews)
                    
                    # 기본 통계 표시
                    col1, col2, col3 = st.columns(3)
                    col1.metric("총 언급 횟수", f"{stats['total_mentions']:,}개")
                    
                    if stats['rating_distribution']:
                        avg_rating = sum(float(k.replace('점', '')) * v for k, v in stats['rating_distribution'].items() if '점' in str(k)) / stats['total_mentions']
                        col2.metric("평균 평점", f"{avg_rating:.2f}점")
                    
                    # 가장 많이 사용한 카테고리
                    if stats['category_distribution']:
                        top_category = max(stats['category_distribution'], key=stats['category_distribution'].get)
                        col3.metric("주 사용 카테고리", top_category)
                    
                    # 상세 분석
                    if st.checkbox("상세 분석 보기"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if stats['category_distribution']:
                                st.write("**카테고리별 사용**")
                                for cat, count in stats['category_distribution'].items():
                                    percentage = count / stats['total_mentions'] * 100
                                    st.write(f"- {cat}: {count}개 ({percentage:.1f}%)")
                        
                        with col2:
                            if stats['rating_distribution']:
                                st.write("**평점별 사용**")
                                for rating, count in sorted(stats['rating_distribution'].items()):
                                    percentage = count / stats['total_mentions'] * 100
                                    st.write(f"- {rating}: {count}개 ({percentage:.1f}%)")
                    
                    # 제품별 신조어 사용 현황
                    st.subheader(f"제품별 '{search_word}' 사용 현황")
                    
                    if 'product_name' in matching_reviews.columns:
                        product_analysis = analyze_word_by_products(search_word, matching_reviews)
                        
                        if product_analysis:
                            # 제품별 사용 횟수 차트
                            import plotly.express as px
                            
                            chart_data = pd.DataFrame(product_analysis)
                            fig = px.bar(
                                chart_data.head(10),
                                x='사용횟수',
                                y='제품명',
                                orientation='h',
                                title=f"제품별 '{search_word}' 사용 횟수 TOP 10",
                                text='사용횟수'
                            )
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            fig.update_traces(textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 제품별 상세 테이블
                            st.subheader("제품별 상세 정보")
                            
                            # 테이블 형태로 표시
                            display_df = pd.DataFrame(product_analysis)
                            st.dataframe(display_df, use_container_width=True)
                            
                            # 제품별 리뷰 샘플 보기
                            st.subheader("제품별 리뷰 샘플")
                            
                            # 상위 5개 제품만 표시
                            top_products = display_df.head(5)['제품명'].tolist()
                            
                            for product_name in top_products:
                                product_reviews = matching_reviews[matching_reviews['product_name'] == product_name]
                                review_count = len(product_reviews)
                                
                                with st.expander(f"{product_name} ({review_count}개 리뷰)"):
                                    # 최대 3개 리뷰만 표시
                                    sample_reviews = product_reviews.head(3)
                                    
                                    for i, (idx, review) in enumerate(sample_reviews.iterrows()):
                                        st.markdown(f"**리뷰 {i+1}:** {review.get('rating', 'N/A')}")
                                        st.markdown(review.get('highlighted_text', review.get('review_text', '')))
                                        if 'review_date' in review:
                                            st.caption(f"작성일: {review['review_date']}")
                                        st.markdown("---")
                        else:
                            st.info("제품별 분석 데이터가 없습니다.")
                    else:
                        st.warning("제품명 정보가 없어 제품별 분석을 할 수 없습니다.")
                    
                    # 전체 리뷰 샘플
                    st.subheader("전체 리뷰 샘플")
                    
                    sample_count = min(5, len(matching_reviews))
                    sample_reviews = matching_reviews.head(sample_count)
                    
                    for i, (idx, review) in enumerate(sample_reviews.iterrows()):
                        with st.expander(f"리뷰 {i+1}: {review.get('rating', 'N/A')} - {review.get('product_name', 'Unknown')[:30]}..."):
                            st.markdown(review.get('highlighted_text', review.get('review_text', '')))
                            if 'review_date' in review:
                                st.caption(f"작성일: {review['review_date']}")
                    
                    # 신조어 저장 기능
                    st.markdown("---")
                    st.subheader("신조어 사전에 추가")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        save_category = st.selectbox(
                            "저장할 카테고리 선택",
                            ["makeup", "skincare"],
                            key="save_category"
                        )
                    
                    with col2:
                        if st.button(f"'{search_word}'를 {save_category} 신조어 사전에 추가", type="primary"):
                            if save_newword_to_file(search_word, save_category):
                                st.success(f"'{search_word}'가 {save_category} 신조어 사전에 추가되었습니다!")
                            else:
                                st.warning(f"'{search_word}'는 이미 {save_category} 신조어 사전에 있습니다.")
                
                else:
                    st.warning(f"'{search_word}'가 포함된 리뷰를 찾을 수 없습니다.")
                    
                    # 신조어 추가 제안
                    st.info("새로운 단어인 것 같습니다. 아래에서 신조어 사전에 추가할 수 있습니다.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        save_category = st.selectbox(
                            "저장할 카테고리 선택",
                            ["makeup", "skincare"],
                            key="save_category_new"
                        )
                    
                    with col2:
                        if st.button(f"'{search_word}'를 {save_category} 신조어 사전에 추가", type="secondary"):
                            if save_newword_to_file(search_word, save_category):
                                st.success(f"'{search_word}'가 {save_category} 신조어 사전에 추가되었습니다!")
                            else:
                                st.warning(f"'{search_word}'는 이미 {save_category} 신조어 사전에 있습니다.")
    
    with tab2:
        st.subheader("신조어 사전 관리")
        
        # 기존 신조어 목록 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**메이크업 신조어 사전**")
            makeup_words = load_existing_newwords("makeup")
            if makeup_words:
                st.write(f"총 {len(makeup_words)}개 단어")
                for word in sorted(makeup_words):
                    st.write(f"- {word}")
            else:
                st.write("등록된 신조어가 없습니다.")
        
        with col2:
            st.write("**스킨케어 신조어 사전**")
            skincare_words = load_existing_newwords("skincare")
            if skincare_words:
                st.write(f"총 {len(skincare_words)}개 단어")
                for word in sorted(skincare_words):
                    st.write(f"- {word}")
            else:
                st.write("등록된 신조어가 없습니다.")
        
        # 수동 추가 기능
        st.markdown("---")
        st.subheader("수동으로 신조어 추가")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            manual_word = st.text_input("추가할 단어", key="manual_word")
        
        with col2:
            manual_category = st.selectbox("카테고리", ["makeup", "skincare"], key="manual_category")
        
        with col3:
            if st.button("추가", type="primary") and manual_word:
                if save_newword_to_file(manual_word.strip(), manual_category):
                    st.success(f"'{manual_word}'가 추가되었습니다!")
                    st.rerun()
                else:
                    st.warning(f"'{manual_word}'는 이미 존재합니다.")
    
    with tab3:
        st.subheader("신조어 사용 통계")
        
        # 등록된 모든 신조어에 대한 사용 통계
        all_words = list(load_existing_newwords("makeup")) + list(load_existing_newwords("skincare"))
        
        if all_words:
            st.write(f"등록된 신조어 {len(all_words)}개에 대한 사용 현황 분석")
            
            # 사용 빈도 분석
            word_stats = []
            
            for word in all_words:
                matching_reviews, count = search_word_in_reviews(word, filtered_df)
                if count > 0:
                    stats = analyze_word_statistics(word, matching_reviews)
                    word_stats.append({
                        '신조어': word,
                        '사용횟수': count,
                        '평균평점': calculate_avg_rating(stats['rating_distribution'], count)
                    })
            
            if word_stats:
                stats_df = pd.DataFrame(word_stats)
                stats_df = stats_df.sort_values('사용횟수', ascending=False)
                
                st.dataframe(stats_df, use_container_width=True)
                
                # 차트로 시각화
                if len(stats_df) > 0:
                    import plotly.express as px
                    
                    fig = px.bar(
                        stats_df.head(10), 
                        x='신조어', 
                        y='사용횟수',
                        title="신조어 사용 빈도 TOP 10"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("현재 필터 조건에서 신조어 사용 데이터가 없습니다.")
        else:
            st.info("등록된 신조어가 없습니다. 먼저 신조어를 등록해주세요.")

def calculate_avg_rating(rating_dist, total_count):
    """평점 분포에서 평균 평점 계산"""
    if not rating_dist or total_count == 0:
        return "N/A"
    
    total_score = 0
    for rating, count in rating_dist.items():
        try:
            # "5점" -> 5로 변환
            score = float(str(rating).replace('점', ''))
            total_score += score * count
        except:
            continue
    
    return f"{total_score / total_count:.2f}점" if total_count > 0 else "N/A"

if __name__ == "__main__":
    render_newword_analysis_tab()