import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import glob
import os
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
import re

def load_daiso_data():
    """다이소 데이터 로딩"""
    daiso_dir = "../data/data_daiso/raw_data/reviews_daiso"
    csv_files = glob.glob(os.path.join(daiso_dir, "*_reviews.csv"))
    
    all_reviews = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            df['channel'] = 'daiso'
            all_reviews.append(df)
        except:
            try:
                df = pd.read_csv(file, encoding='cp949')
                df['channel'] = 'daiso'
                all_reviews.append(df)
            except:
                continue
    
    if all_reviews:
        df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        return df
    return pd.DataFrame()

def extract_rating(rating_str):
    """평점 추출 함수"""
    if pd.isna(rating_str):
        return np.nan
    
    rating_str = str(rating_str)
    
    if '점' in rating_str:
        try:
            return float(rating_str.replace('점', ''))
        except:
            return np.nan
    elif '★' in rating_str:
        return float(rating_str.count('★'))
    
    try:
        return float(rating_str)
    except:
        return np.nan

def load_korean_stopwords():
    """한국어 불용어 로딩"""
    my_stopwords = [
            '것', '수', '있', '하', '되', '그', '이', '저', '때', '더', '또', '같', '좋', 
            '정말', '너무', '진짜', '완전', '그냥', '약간', '조금', '많이', '잘', '안',
            '하지만', '그런데', '그리고', '또한', '그래서', '따라서', '하면', '하니까',
            '입니다', '습니다', '해요', '이에요', '예요', '이죠', '네요', '어요', '재구매',
            '감사합니다', '잘쓸게요', '잘쓸께요', '같아요', "이거", "같이", "사용하기"
        ]
    try:
        with open(r'C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\src\words_dictionary\stopwords\stopwords_origin.txt', 'r', encoding='utf-8') as f:
            stopwords1 = [line.strip() for line in f if line.strip()]
            stopwords_set = set(stopwords1)
            stopwords = stopwords_set.union(my_stopwords)
        return set(stopwords)
    except:
        return set([
            '것', '수', '있', '하', '되', '그', '이', '저', '때', '더', '또', '같', '좋', 
            '정말', '너무', '진짜', '완전', '그냥', '약간', '조금', '많이', '잘', '안',
            '하지만', '그런데', '그리고', '또한', '그래서', '따라서', '하면', '하니까',
            '입니다', '습니다', '해요', '이에요', '예요', '이죠', '네요', '어요', '재구매',
            '감사합니다', '잘쓸게요', '잘쓸께요', '같아요', "이거", "같이", "사용하기"
        ])

def preprocess_korean_text(text):
    """한국어 텍스트 전처리"""
    if not text or pd.isna(text):
        return ''
    
    text = str(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'[^\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318Fa-zA-Z0-9\s.,!?~\-()]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def analyze_product_keywords(product_df, analysis_type="count"):
    """제품 키워드 분석"""
    if product_df.empty or 'review_text' not in product_df.columns:
        return None
    
    reviews = product_df['review_text'].fillna('').apply(preprocess_korean_text)
    reviews = reviews[reviews.str.len() > 0]
    
    if len(reviews) == 0:
        return None
    
    stopwords = load_korean_stopwords()
    
    try:
        if analysis_type == "count":
            vectorizer = CountVectorizer(
                max_features=50,
                min_df=2,
                ngram_range=(1, 2),
                stop_words=list(stopwords)
            )
        else:
            vectorizer = TfidfVectorizer(
                max_features=30,
                min_df=2,
                ngram_range=(1, 2),
                stop_words=list(stopwords)
            )
        
        matrix = vectorizer.fit_transform(reviews)
        feature_names = vectorizer.get_feature_names_out()
        
        if analysis_type == "count":
            scores = matrix.sum(axis=0).A1
        else:
            scores = matrix.mean(axis=0).A1
        
        word_scores = list(zip(feature_names, scores))
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        return word_scores
        
    except Exception as e:
        st.error(f"키워드 분석 중 오류: {e}")
        return None

def analyze_sentiment_keywords(product_df):
    """긍정/부정 키워드 분석"""
    if product_df.empty or 'review_text' not in product_df.columns or 'rating' not in product_df.columns:
        return None, None
    
    product_df['rating_numeric'] = product_df['rating'].apply(extract_rating)
    
    positive_reviews = product_df[product_df['rating_numeric'] >= 4]['review_text'].fillna('')
    negative_reviews = product_df[product_df['rating_numeric'] <= 3]['review_text'].fillna('')
    
    if len(positive_reviews) == 0 or len(negative_reviews) == 0:
        return None, None
    
    stopwords = load_korean_stopwords()
    
    try:
        vectorizer = CountVectorizer(
            max_features=20,
            min_df=1,
            ngram_range=(1, 2),
            stop_words=list(stopwords)
        )
        
        pos_text = ' '.join(positive_reviews.apply(preprocess_korean_text))
        neg_text = ' '.join(negative_reviews.apply(preprocess_korean_text))
        
        pos_matrix = vectorizer.fit_transform([pos_text])
        pos_features = vectorizer.get_feature_names_out()
        pos_scores = pos_matrix.toarray()[0]
        
        neg_matrix = vectorizer.fit_transform([neg_text])
        neg_features = vectorizer.get_feature_names_out()
        neg_scores = neg_matrix.toarray()[0]
        
        positive_keywords = list(zip(pos_features, pos_scores))
        negative_keywords = list(zip(neg_features, neg_scores))
        
        positive_keywords.sort(key=lambda x: x[1], reverse=True)
        negative_keywords.sort(key=lambda x: x[1], reverse=True)
        
        return positive_keywords[:10], negative_keywords[:10]
        
    except Exception as e:
        st.error(f"감정 분석 중 오류: {e}")
        return None, None

def get_product_basic_info(product_df):
    """제품 기본 정보 추출"""
    if product_df.empty:
        return {}
    
    first_row = product_df.iloc[0]
    product_df['rating_numeric'] = product_df['rating'].apply(extract_rating)
    rating_counts = product_df['rating'].value_counts()
    
    text_lengths = product_df['review_text'].fillna('').str.len()
    long_reviews = len(text_lengths[text_lengths > 100])
    negative_reviews = len(product_df[product_df['rating_numeric'] <= 3])
    
    dates = product_df['review_date'].dropna()
    date_range = f"{dates.min().strftime('%Y-%m-%d')} ~ {dates.max().strftime('%Y-%m-%d')}" if not dates.empty else "N/A"
    
    return {
        'product_name': first_row.get('product_name', 'N/A'),
        'price': first_row.get('product_price', 'N/A'),
        'category': first_row.get('category', 'N/A'),
        'sort_type': first_row.get('sort_type', 'N/A'),
        'rank': first_row.get('rank', 'N/A'),
        'total_reviews': len(product_df),
        'rating_counts': rating_counts.to_dict(),
        'avg_length': round(text_lengths.mean()),
        'max_length': text_lengths.max(),
        'min_length': text_lengths.min(),
        'long_reviews': long_reviews,
        'negative_reviews': negative_reviews,
        'date_range': date_range
    }

def render_daiso_section():
    """다이소 분석 섹션 렌더링"""
    st.header("다이소 랭킹 분석")
    
    daiso_df = load_daiso_data()
    
    if daiso_df.empty:
        st.error("다이소 데이터를 로딩할 수 없습니다.")
        return
    
    # 데이터 현황
    total_reviews = len(daiso_df)
    makeup_reviews = len(daiso_df[daiso_df['category'] == 'makeup']) if 'category' in daiso_df.columns else 0
    skincare_reviews = len(daiso_df[daiso_df['category'] == 'skincare']) if 'category' in daiso_df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 리뷰 수", f"{total_reviews:,}")
    col2.metric("메이크업", f"{makeup_reviews:,}")
    col3.metric("스킨케어", f"{skincare_reviews:,}")
    
# 필터링 옵션
    st.subheader("필터 설정")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'category' in daiso_df.columns:
            categories = ['전체'] + list(daiso_df['category'].unique())
            selected_category = st.selectbox("카테고리", categories, key="daiso_category")
        else:
            selected_category = '전체'
    
    with col2:
        if 'sort_type' in daiso_df.columns:
            if selected_category == '전체':
                available_sorts = list(daiso_df['sort_type'].unique())
            else:
                available_sorts = list(daiso_df[daiso_df['category'] == selected_category]['sort_type'].unique())
            
            sort_options = ['전체'] + available_sorts
            selected_sort = st.selectbox("정렬방식", sort_options, key="daiso_sort")
        else:
            selected_sort = '전체'
    
    with col3:
        period_options = ['전체', '1개월', '3개월', '6개월', '1년']
        selected_period = st.selectbox("기간", period_options, key="daiso_period")
    
    # 데이터 필터링
    filtered_df = daiso_df.copy()
    
    # 카테고리 필터링
    if selected_category != '전체' and 'category' in daiso_df.columns:
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # 정렬방식 필터링
    if selected_sort != '전체' and 'sort_type' in daiso_df.columns:
        filtered_df = filtered_df[filtered_df['sort_type'] == selected_sort]
    
    # 기간 필터링
    if selected_period != '전체' and 'review_date' in filtered_df.columns:
        # 현재 날짜에서 선택된 기간만큼 뺀 날짜 계산
        from datetime import datetime, timedelta
        current_date = datetime.now()
        
        if selected_period == '1개월':
            cutoff_date = current_date - timedelta(days=30)
        elif selected_period == '3개월':
            cutoff_date = current_date - timedelta(days=90)
        elif selected_period == '6개월':
            cutoff_date = current_date - timedelta(days=180)
        elif selected_period == '1년':
            cutoff_date = current_date - timedelta(days=365)
        
        # 날짜 데이터가 있는 것만 필터링
        filtered_df = filtered_df.dropna(subset=['review_date'])
        filtered_df = filtered_df[filtered_df['review_date'] >= cutoff_date]
        st.markdown("---")
    
    # 분석 서브탭 - 6개 탭으로 확장
    tab_names = ["전체 트렌드", "제품별 분석", "랭킹 분석", "성과 분석", "제품 상세 분석", "주요 브랜드 분석", "분석 보고서"]
    tabs = st.tabs(tab_names)
    
# subtab1: 전체 트렌드
    with tabs[0]:
        st.subheader("전체 리뷰 트렌드")
        
        if 'review_date' in filtered_df.columns:
            time_df = filtered_df.dropna(subset=['review_date'])
            
            if not time_df.empty:
                time_unit = st.radio("시간 단위", ["주별", "월별"], horizontal=True, key="daiso_time_unit")
                
                if time_unit == "주별":
                    time_df['week'] = time_df['review_date'].dt.to_period('W')
                    weekly_counts = time_df.groupby('week').size()
                    fig = px.bar(x=[str(w) for w in weekly_counts.index], y=weekly_counts.values,
                               title="주별 리뷰 수 변화", labels={'x': '주', 'y': '리뷰 수'})
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:  # 월별
                    time_df['month'] = time_df['review_date'].dt.to_period('M')
                    monthly_counts = time_df.groupby('month').size()
                    fig = px.bar(x=[str(m) for m in monthly_counts.index], y=monthly_counts.values,
                               title="월별 리뷰 수 변화", labels={'x': '월', 'y': '리뷰 수'})
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("시간 데이터가 없습니다.")
        else:
            st.warning("review_date 컬럼이 없습니다.")
    
# subtab2: 제품별 분석
    with tabs[1]:
        st.subheader("제품별 분석")
        
        if 'product_name' in filtered_df.columns:
            products = list(filtered_df['product_name'].unique())
            selected_products = st.multiselect(
                "분석할 제품 선택 (최대 5개)", 
                products, 
                default=products[:3] if len(products) >= 3 else products,
                max_selections=5,
                key="daiso_products"
            )
            
            if selected_products and 'review_date' in filtered_df.columns:
                time_unit = st.radio("시간 단위", ["주별", "월별"], horizontal=True, key="daiso_product_time")
                
                trend_data = []
                for product in selected_products:
                    product_data = filtered_df[filtered_df['product_name'] == product].dropna(subset=['review_date'])
                    
                    if not product_data.empty:
                        if time_unit == "주별":
                            product_data['week'] = product_data['review_date'].dt.to_period('W')
                            counts = product_data.groupby('week').size()
                        else:  # 월별
                            product_data['month'] = product_data['review_date'].dt.to_period('M')
                            counts = product_data.groupby('month').size()
                        
                        for period, count in counts.items():
                            trend_data.append({
                                '기간': str(period),
                                '제품명': product,
                                '리뷰수': count
                            })
                
                if trend_data:
                    trend_df = pd.DataFrame(trend_data)
                    fig = px.bar(trend_df, x='기간', y='리뷰수', color='제품명',
                                title=f"제품별 {time_unit} 리뷰 수 변화", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    product_stats = []
                    for product in selected_products:
                        product_data = filtered_df[filtered_df['product_name'] == product]
                        stats = {
                            '제품명': product,
                            '총리뷰수': len(product_data),
                            '카테고리': product_data['category'].iloc[0] if len(product_data) > 0 and 'category' in product_data.columns else 'Unknown',
                            '정렬방식': product_data['sort_type'].iloc[0] if len(product_data) > 0 and 'sort_type' in product_data.columns else 'Unknown'
                        }
                        
                        if 'rating' in product_data.columns:
                            product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                            valid_ratings = product_data.dropna(subset=['rating_numeric'])
                            if not valid_ratings.empty:
                                stats['평균평점'] = f"{valid_ratings['rating_numeric'].mean():.2f}"
                            else:
                                stats['평균평점'] = "N/A"
                        else:
                            stats['평균평점'] = "N/A"
                        
                        product_stats.append(stats)
                    
                    st.subheader("선택 제품 상세 통계")
                    st.dataframe(pd.DataFrame(product_stats), use_container_width=True)
                else:
                    st.warning("선택된 제품의 시간 데이터가 없습니다.")
            else:
                st.warning("제품을 선택해주세요.")
        else:
            st.warning("제품명 데이터가 없습니다.")
    
    # subtab3: 랭킹 분석
    with tabs[2]:
        st.subheader("랭킹 분석")
        
        if 'sort_type' in filtered_df.columns and 'product_name' in filtered_df.columns:
            for sort_type in filtered_df['sort_type'].unique():
                sort_data = filtered_df[filtered_df['sort_type'] == sort_type]
                
                st.write(f"**{sort_type} TOP 10**")
                
                top_products = sort_data['product_name'].value_counts().head(10)
                
                if not top_products.empty:
                    fig = px.bar(
                        x=top_products.values,
                        y=top_products.index,
                        orientation='h',
                        title=f"{sort_type} 상위 제품",
                        labels={'x': '리뷰 수', 'y': '제품명'},
                        text=top_products.values
                    )
                    fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("데이터가 없습니다.")
                
                st.markdown("---")
        
        if 'category' in filtered_df.columns and 'sort_type' in filtered_df.columns:
            st.subheader("카테고리별 정렬방식 성과 비교")
            
            comparison_data = []
            
            for category in filtered_df['category'].unique():
                cat_data = filtered_df[filtered_df['category'] == category]
                
                for sort_type in cat_data['sort_type'].unique():
                    sort_cat_data = cat_data[cat_data['sort_type'] == sort_type]
                    
                    unique_products = len(sort_cat_data['product_name'].unique()) if 'product_name' in sort_cat_data.columns else 0
                    total_reviews = len(sort_cat_data)
                    avg_reviews = total_reviews / unique_products if unique_products > 0 else 0
                    
                    comparison_data.append({
                        '카테고리': category,
                        '정렬방식': sort_type,
                        '제품수': unique_products,
                        '총리뷰수': total_reviews,
                        '제품당평균리뷰': round(avg_reviews, 1)
                    })
            
            if comparison_data:
                comp_df = pd.DataFrame(comparison_data)
                
                fig = px.bar(comp_df, x='정렬방식', y='총리뷰수', color='카테고리',
                           title="카테고리별 정렬방식 리뷰 수 비교", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(comp_df, use_container_width=True)
    
# subtab4: 성과 분석
    with tabs[3]:
        st.subheader("성과 분석")
        
        if 'rating' in filtered_df.columns and 'product_name' in filtered_df.columns:
            product_performance = []
            
            # 하이라이트할 브랜드 리스트
            highlight_brands = ['CNP', 'TFS', '코드글로컬러', '케어존']
            
            for product in filtered_df['product_name'].unique():
                product_data = filtered_df[filtered_df['product_name'] == product]
                
                product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                valid_ratings = product_data.dropna(subset=['rating_numeric'])
                
                if not valid_ratings.empty:
                    avg_rating = valid_ratings['rating_numeric'].mean()
                    review_count = len(product_data)
                    category = product_data['category'].iloc[0] if 'category' in product_data.columns else 'Unknown'
                    sort_type = product_data['sort_type'].iloc[0] if 'sort_type' in product_data.columns else 'Unknown'
                    
                    # 제품명에 하이라이트 브랜드가 포함되어 있는지 확인
                    is_highlighted = any(brand in product for brand in highlight_brands)
                    brand_type = '주요 브랜드' if is_highlighted else '기타 브랜드'
                    
                    product_performance.append({
                        '제품명': product,
                        '평균평점': avg_rating,
                        '리뷰수': review_count,
                        '카테고리': category,
                        '정렬방식': sort_type,
                        '브랜드구분': brand_type
                    })
            
            if product_performance:
                perf_df = pd.DataFrame(product_performance)
                
                # 브랜드구분에 따라 색상을 다르게 하여 scatter plot 생성
                fig = px.scatter(perf_df, x='리뷰수', y='평균평점', 
                               color='브랜드구분', size='리뷰수',
                               hover_data=['제품명', '정렬방식', '카테고리'],
                               title="제품 성과 분석: 평점 vs 리뷰수",
                               color_discrete_map={
                                   '주요 브랜드': '#FF6B6B',  # 빨간색 계열
                                   '기타 브랜드': '#4ECDC4'   # 청록색 계열
                               })
                
                # 범례 위치 조정 및 마커 크기 설정
                fig.update_layout(
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 주요 브랜드 제품들의 통계 정보 표시
                highlighted_products = perf_df[perf_df['브랜드구분'] == '주요 브랜드']
                if not highlighted_products.empty:
                    st.markdown("### 주요 브랜드 제품 현황")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("주요 브랜드 제품 수", f"{len(highlighted_products)}개")
                    col2.metric("평균 평점", f"{highlighted_products['평균평점'].mean():.2f}")
                    col3.metric("총 리뷰 수", f"{highlighted_products['리뷰수'].sum():,}개")
                    col4.metric("평균 리뷰 수", f"{highlighted_products['리뷰수'].mean():.0f}개")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**평점 높은 제품 TOP 10**")
                    top_rating = perf_df.nlargest(10, '평균평점')[['제품명', '평균평점', '리뷰수', '카테고리', '브랜드구분']]
                    # 주요 브랜드는 굵게 표시
                    for idx, row in top_rating.iterrows():
                        if row['브랜드구분'] == '주요 브랜드':
                            top_rating.loc[idx, '제품명'] = f"**{row['제품명']}**"
                    st.dataframe(top_rating.drop('브랜드구분', axis=1), use_container_width=True)
                
                with col2:
                    st.write("**리뷰 많은 제품 TOP 10**")
                    top_reviews = perf_df.nlargest(10, '리뷰수')[['제품명', '리뷰수', '평균평점', '카테고리', '브랜드구분']]
                    # 주요 브랜드는 굵게 표시
                    for idx, row in top_reviews.iterrows():
                        if row['브랜드구분'] == '주요 브랜드':
                            top_reviews.loc[idx, '제품명'] = f"**{row['제품명']}**"
                    st.dataframe(top_reviews.drop('브랜드구분', axis=1), use_container_width=True)
    # subtab5: 제품 상세 분석
    with tabs[4]:
        st.subheader("제품 상세 분석")
        
        if 'product_name' in filtered_df.columns:
            products = sorted(filtered_df['product_name'].unique())
            selected_product = st.selectbox(
                "분석할 제품을 선택하세요",
                products,
                key="product_detail_select"
            )
            
            if selected_product:
                product_data = filtered_df[filtered_df['product_name'] == selected_product]
                basic_info = get_product_basic_info(product_data)
                
                # 기본 정보
                st.markdown("### 제품 기본 정보")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("총 리뷰", f"{basic_info['total_reviews']:,}개")
                col2.metric("다이소 순위", f"{basic_info['rank']}위")
                col3.metric("가격", basic_info['price'])
                col4.metric("카테고리", basic_info['category'])
                
                # 평점 분포
                st.markdown("### 리뷰 현황")
                
                if basic_info['rating_counts']:
                    rating_df = pd.DataFrame(list(basic_info['rating_counts'].items()), 
                                           columns=['평점', '개수'])
                    
                    fig = px.pie(rating_df, values='개수', names='평점', title="평점 분포")
                    st.plotly_chart(fig, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("평균 리뷰 길이", f"{basic_info['avg_length']}글자")
                col2.metric("긴 리뷰", f"{basic_info['long_reviews']}개 (100글자+)")
                col3.metric("부정 리뷰", f"{basic_info['negative_reviews']}개 (1-3점)")
                
                st.info(f"리뷰 기간: {basic_info['date_range']}")
                
                # 텍스트 분석
                st.markdown("### 텍스트 분석")
                
                analysis_method = st.radio(
                    "분석 방법을 선택하세요",
                    ["기본 키워드 (Count)", "중요 키워드 (TF-IDF)", "평점별 비교"],
                    horizontal=True
                )
                
                if analysis_method == "기본 키워드 (Count)":
                    word_scores = analyze_product_keywords(product_data, "count")
                    
                    if word_scores:
                        st.write("**가장 자주 언급되는 키워드 TOP 20**")
                        keywords_df = pd.DataFrame(word_scores[:20], columns=['키워드', '빈도'])
                        
                        fig = px.bar(keywords_df, x='빈도', y='키워드', 
                                   orientation='h', title="키워드 빈도 분석")
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(keywords_df, use_container_width=True)
                    else:
                        st.warning("분석할 텍스트 데이터가 부족합니다.")
                
                elif analysis_method == "중요 키워드 (TF-IDF)":
                    word_scores = analyze_product_keywords(product_data, "tfidf")
                    
                    if word_scores:
                        st.write("**이 제품에서 특별히 중요한 키워드 TOP 15**")
                        keywords_df = pd.DataFrame(word_scores[:15], columns=['키워드', 'TF-IDF 점수'])
                        
                        fig = px.bar(keywords_df, x='TF-IDF 점수', y='키워드', 
                                   orientation='h', title="TF-IDF 중요도 분석")
                        fig.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(keywords_df, use_container_width=True)
                    else:
                        st.warning("분석할 텍스트 데이터가 부족합니다.")
                
                else:  # 평점별 비교
                    positive_keywords, negative_keywords = analyze_sentiment_keywords(product_data)
                    
                    if positive_keywords and negative_keywords:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**긍정 리뷰 키워드 (4-5점)**")
                            pos_df = pd.DataFrame(positive_keywords, columns=['키워드', '빈도'])
                            st.dataframe(pos_df, use_container_width=True)
                        
                        with col2:
                            st.write("**부정 리뷰 키워드 (1-3점)**")
                            neg_df = pd.DataFrame(negative_keywords, columns=['키워드', '빈도'])
                            st.dataframe(neg_df, use_container_width=True)
                    else:
                        st.warning("평점별 분석을 위한 데이터가 부족합니다.")
                
                # 시간별 트렌드 분석
                st.markdown("### 시간별 트렌드 분석")
                
                if 'review_date' in product_data.columns and not product_data['review_date'].isna().all():
                    trend_data = product_data.dropna(subset=['review_date']).copy()
                    trend_data['rating_numeric'] = trend_data['rating'].apply(extract_rating)
                    
                    if len(trend_data) > 1:
                        # 월별 리뷰수 변화
                        st.markdown("#### 월별 리뷰수 변화")
                        
                        monthly_counts = trend_data.groupby(trend_data['review_date'].dt.to_period('M')).size()
                        
                        if len(monthly_counts) > 1:
                            monthly_change = monthly_counts.pct_change() * 100
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig1 = px.line(
                                    x=[str(m) for m in monthly_counts.index], 
                                    y=monthly_counts.values,
                                    title="월별 리뷰수 추이",
                                    labels={'x': '월', 'y': '리뷰 수'}
                                )
                                fig1.update_traces(mode='lines+markers')
                                st.plotly_chart(fig1, use_container_width=True)
                            
                            with col2:
                                change_data = monthly_change.dropna()
                                if len(change_data) > 0:
                                    colors = ['red' if x < 0 else 'green' for x in change_data.values]
                                    fig2 = px.bar(
                                        x=[str(m) for m in change_data.index],
                                        y=change_data.values,
                                        title="월별 리뷰수 증감률 (%)",
                                        labels={'x': '월', 'y': '증감률 (%)'}
                                    )
                                    fig2.update_traces(marker_color=colors)
                                    st.plotly_chart(fig2, use_container_width=True)
                        
                        # 긍정/부정 비율 변화
                        st.markdown("#### 긍정/부정 비율 변화")
                        
                        def get_sentiment(rating):
                            if pd.isna(rating):
                                return 'unknown'
                            if rating >= 4:
                                return 'positive'
                            elif rating <= 3:
                                return 'negative'
                            else:
                                return 'neutral'
                        
                        trend_data['sentiment'] = trend_data['rating_numeric'].apply(get_sentiment)
                        
                        monthly_sentiment = trend_data.groupby([
                            trend_data['review_date'].dt.to_period('M'), 
                            'sentiment'
                        ]).size().unstack(fill_value=0)
                        
                        if len(monthly_sentiment) > 1 and 'positive' in monthly_sentiment.columns:
                            total_reviews = monthly_sentiment.sum(axis=1)
                            positive_ratio = (monthly_sentiment.get('positive', 0) / total_reviews * 100).fillna(0)
                            negative_ratio = (monthly_sentiment.get('negative', 0) / total_reviews * 100).fillna(0)
                            
                            fig3 = go.Figure()
                            fig3.add_trace(go.Scatter(
                                x=[str(m) for m in positive_ratio.index],
                                y=positive_ratio.values,
                                mode='lines+markers',
                                name='긍정 비율',
                                line=dict(color='green')
                            ))
                            fig3.add_trace(go.Scatter(
                                x=[str(m) for m in negative_ratio.index],
                                y=negative_ratio.values,
                                mode='lines+markers',
                                name='부정 비율',
                                line=dict(color='red')
                            ))
                            fig3.update_layout(
                                title="월별 긍정/부정 비율 추이",
                                xaxis_title="월",
                                yaxis_title="비율 (%)",
                                yaxis=dict(range=[0, 100])
                            )
                            st.plotly_chart(fig3, use_container_width=True)
                            
                            current_sentiment = trend_data['sentiment'].value_counts()
                            total = current_sentiment.sum()
                            
                            col1, col2, col3 = st.columns(3)
                            if 'positive' in current_sentiment:
                                col1.metric("긍정 비율", f"{current_sentiment.get('positive', 0)/total*100:.1f}%")
                            if 'negative' in current_sentiment:
                                col2.metric("부정 비율", f"{current_sentiment.get('negative', 0)/total*100:.1f}%")
                            if 'neutral' in current_sentiment:
                                col3.metric("중립 비율", f"{current_sentiment.get('neutral', 0)/total*100:.1f}%")
                        
                        # 제품 생명주기 분석
                        st.markdown("#### 제품 생명주기 분석")
                        
                        first_review_date = trend_data['review_date'].min()
                        trend_data['days_since_launch'] = (trend_data['review_date'] - first_review_date).dt.days
                        
                        def get_lifecycle_stage(days):
                            if days <= 30:
                                return '출시 1개월'
                            elif days <= 90:
                                return '1-3개월'
                            elif days <= 180:
                                return '3-6개월'
                            elif days <= 365:
                                return '6-12개월'
                            else:
                                return '1년+'
                        
                        trend_data['lifecycle'] = trend_data['days_since_launch'].apply(get_lifecycle_stage)
                        
                        lifecycle_stats = trend_data.groupby('lifecycle').agg({
                            'rating_numeric': ['count', 'mean'],
                            'review_text': lambda x: x.str.len().mean()
                        }).round(2)
                        
                        lifecycle_stats.columns = ['리뷰수', '평균평점', '평균글자수']
                        lifecycle_stats = lifecycle_stats.reset_index()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig4 = px.bar(
                                lifecycle_stats,
                                x='lifecycle',
                                y='리뷰수',
                                title="생명주기별 리뷰수",
                                labels={'lifecycle': '생명주기 단계', '리뷰수': '리뷰 수'}
                            )
                            st.plotly_chart(fig4, use_container_width=True)
                        
                        with col2:
                            fig5 = px.line(
                                lifecycle_stats,
                                x='lifecycle',
                                y='평균평점',
                                title="생명주기별 평균 평점",
                                labels={'lifecycle': '생명주기 단계', '평균평점': '평균 평점'},
                                markers=True
                            )
                            fig5.update_layout(yaxis=dict(range=[1, 5]))
                            st.plotly_chart(fig5, use_container_width=True)
                        
                        st.dataframe(lifecycle_stats, use_container_width=True)
                        
                        max_reviews_stage = lifecycle_stats.loc[lifecycle_stats['리뷰수'].idxmax(), 'lifecycle']
                        best_rating_stage = lifecycle_stats.loc[lifecycle_stats['평균평점'].idxmax(), 'lifecycle']
                        
                        st.info(f"가장 많은 리뷰를 받은 시기는 '{max_reviews_stage}'이고, "
                               f"평점이 가장 높은 시기는 '{best_rating_stage}'입니다.")
                    
                    else:
                        st.warning("시간별 분석을 위한 충분한 데이터가 없습니다.")
                else:
                    st.warning("날짜 데이터가 없어 시간별 분석을 할 수 없습니다.")
                
                # 리뷰 샘플
                st.markdown("### 리뷰 샘플")
                
                sample_type = st.selectbox(
                    "보고 싶은 리뷰 유형",
                    ["최신 리뷰", "긍정 리뷰 (4-5점)", "부정 리뷰 (1-3점)", "긴 리뷰 (100글자+)"]
                )
                
                if sample_type == "최신 리뷰":
                    samples = product_data.sort_values('review_date', ascending=False).head(5)
                elif sample_type == "긍정 리뷰 (4-5점)":
                    product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                    samples = product_data[product_data['rating_numeric'] >= 4].head(5)
                elif sample_type == "부정 리뷰 (1-3점)":
                    product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                    samples = product_data[product_data['rating_numeric'] <= 3].head(5)
                else:
                    product_data['text_length'] = product_data['review_text'].str.len()
                    samples = product_data[product_data['text_length'] > 100].head(5)
                
                for i, (idx, row) in enumerate(samples.iterrows()):
                    with st.expander(f"{i+1}. {row['rating']} - {row.get('review_date', 'N/A')}"):
                        st.write(row['review_text'])
        else:
            st.warning("제품명 데이터가 없습니다.")
    # subtab6: 주요 브랜드 분석 (새로 추가)
    with tabs[5]:
        st.subheader("주요 브랜드 분석")
        
        # 하이라이트할 브랜드 리스트
        highlight_brands = ['CNP', 'TFS', '코드글로컬러', '케어존']
        
        # 주요 브랜드 제품들만 필터링
        brand_filtered_df = filtered_df[
            filtered_df['product_name'].str.contains('|'.join(highlight_brands), case=False, na=False)
        ].copy()
        
        if brand_filtered_df.empty:
            st.warning("현재 필터 조건에서 주요 브랜드 제품이 없습니다.")
            st.info("필터 설정을 조정해보세요. (카테고리: 전체, 정렬방식: 전체, 기간: 전체)")
        else:
            # 브랜드별 통계
            st.markdown("### 브랜드별 현황")
            
            brand_stats = []
            for brand in highlight_brands:
                brand_products = brand_filtered_df[
                    brand_filtered_df['product_name'].str.contains(brand, case=False, na=False)
                ]
                
                if not brand_products.empty:
                    brand_products['rating_numeric'] = brand_products['rating'].apply(extract_rating)
                    valid_ratings = brand_products.dropna(subset=['rating_numeric'])
                    
                    stats = {
                        '브랜드': brand,
                        '제품수': len(brand_products['product_name'].unique()),
                        '총리뷰수': len(brand_products),
                        '평균평점': valid_ratings['rating_numeric'].mean() if not valid_ratings.empty else 0,
                        '평균리뷰길이': brand_products['review_text'].str.len().mean() if 'review_text' in brand_products.columns else 0
                    }
                    brand_stats.append(stats)
            
            if brand_stats:
                brand_stats_df = pd.DataFrame(brand_stats)
                brand_stats_df['평균평점'] = brand_stats_df['평균평점'].round(2)
                brand_stats_df['평균리뷰길이'] = brand_stats_df['평균리뷰길이'].round(0).astype(int)
                
                # 브랜드별 메트릭 표시
                cols = st.columns(len(brand_stats))
                for i, (_, row) in enumerate(brand_stats_df.iterrows()):
                    with cols[i]:
                        st.metric(
                            row['브랜드'],
                            f"{row['제품수']}개 제품",
                            f"평점 {row['평균평점']}"
                        )
                
                # 브랜드별 상세 통계 테이블
                st.dataframe(brand_stats_df, use_container_width=True)
                
                # 브랜드별 비교 차트
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = px.bar(brand_stats_df, x='브랜드', y='총리뷰수',
                                title="브랜드별 총 리뷰 수", text='총리뷰수')
                    fig1.update_traces(textposition='outside')
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    fig2 = px.bar(brand_stats_df, x='브랜드', y='평균평점',
                                title="브랜드별 평균 평점", text='평균평점')
                    fig2.update_traces(textposition='outside')
                    fig2.update_layout(yaxis=dict(range=[0, 5]))
                    st.plotly_chart(fig2, use_container_width=True)
            
            # 브랜드별 제품 성과 분석
            st.markdown("### 브랜드별 제품 성과")
            
            if 'rating' in brand_filtered_df.columns:
                brand_filtered_df['rating_numeric'] = brand_filtered_df['rating'].apply(extract_rating)
                
                product_performance = []
                for product in brand_filtered_df['product_name'].unique():
                    product_data = brand_filtered_df[brand_filtered_df['product_name'] == product]
                    valid_ratings = product_data.dropna(subset=['rating_numeric'])
                    
                    if not valid_ratings.empty:
                        # 어떤 브랜드인지 확인
                        brand_name = '기타'
                        for brand in highlight_brands:
                            if brand in product:
                                brand_name = brand
                                break
                        
                        product_performance.append({
                            '제품명': product,
                            '브랜드': brand_name,
                            '평균평점': valid_ratings['rating_numeric'].mean(),
                            '리뷰수': len(product_data),
                            '카테고리': product_data['category'].iloc[0] if 'category' in product_data.columns else 'Unknown'
                        })
                
                if product_performance:
                    perf_df = pd.DataFrame(product_performance)
                    
                    # 브랜드별 색상으로 scatter plot
                    fig3 = px.scatter(perf_df, x='리뷰수', y='평균평점', 
                                    color='브랜드', size='리뷰수',
                                    hover_data=['제품명', '카테고리'],
                                    title="주요 브랜드 제품 성과 분석")
                    st.plotly_chart(fig3, use_container_width=True)
                    
                    # 브랜드별 TOP 제품
                    st.markdown("### 브랜드별 최고 성과 제품")
                    
                    for brand in highlight_brands:
                        brand_products = perf_df[perf_df['브랜드'] == brand]
                        if not brand_products.empty:
                            top_product = brand_products.loc[brand_products['평균평점'].idxmax()]
                            
                            col1, col2, col3, col4 = st.columns(4)
                            col1.write(f"**{brand}**")
                            col2.write(f"{top_product['제품명'][:30]}...")
                            col3.write(f"평점: {top_product['평균평점']:.2f}")
                            col4.write(f"리뷰: {top_product['리뷰수']}개")
            
            # 브랜드별 키워드 분석
            st.markdown("### 브랜드별 주요 키워드")
            
            if 'review_text' in brand_filtered_df.columns:
                brand_keywords = {}
                
                for brand in highlight_brands:
                    brand_reviews = brand_filtered_df[
                        brand_filtered_df['product_name'].str.contains(brand, case=False, na=False)
                    ]
                    
                    if not brand_reviews.empty:
                        keywords = analyze_product_keywords(brand_reviews, "count")
                        if keywords:
                            brand_keywords[brand] = keywords[:10]
                
                if brand_keywords:
                    # 브랜드별 키워드를 탭으로 표시
                    keyword_tabs = st.tabs(list(brand_keywords.keys()))
                    
                    for i, (brand, keywords) in enumerate(brand_keywords.items()):
                        with keyword_tabs[i]:
                            keywords_df = pd.DataFrame(keywords, columns=['키워드', '빈도'])
                            
                            fig = px.bar(keywords_df, x='빈도', y='키워드',
                                       orientation='h', title=f"{brand} 주요 키워드")
                            fig.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)
            
            # 브랜드별 시간 트렌드
            st.markdown("### 브랜드별 시간 트렌드")
            
            if 'review_date' in brand_filtered_df.columns:
                time_df = brand_filtered_df.dropna(subset=['review_date']).copy()
                
                if not time_df.empty:
                    # 각 브랜드별로 월별 리뷰 수 계산
                    brand_trends = []
                    
                    for brand in highlight_brands:
                        brand_data = time_df[
                            time_df['product_name'].str.contains(brand, case=False, na=False)
                        ]
                        
                        if not brand_data.empty:
                            brand_data['month'] = brand_data['review_date'].dt.to_period('M')
                            monthly_counts = brand_data.groupby('month').size()
                            
                            for month, count in monthly_counts.items():
                                brand_trends.append({
                                    '월': str(month),
                                    '브랜드': brand,
                                    '리뷰수': count
                                })
                    
                    if brand_trends:
                        trend_df = pd.DataFrame(brand_trends)
                        
                        fig4 = px.line(trend_df, x='월', y='리뷰수', color='브랜드',
                                     title="브랜드별 월별 리뷰 수 트렌드", markers=True)
                        st.plotly_chart(fig4, use_container_width=True)
                    else:
                        st.warning("브랜드별 시간 트렌드 데이터가 없습니다.")
                else:
                    st.warning("시간 데이터가 없습니다.")

    # subtab7: 분석 보고서
    with tabs[6]:
        st.subheader("분석 보고서")
        
        if 'product_name' in filtered_df.columns:
            products = sorted(filtered_df['product_name'].unique())
            selected_product_report = st.selectbox(
                "보고서 생성할 제품을 선택하세요",
                products,
                key="product_report_select"
            )
            
            if selected_product_report:
                product_data = filtered_df[filtered_df['product_name'] == selected_product_report]
                basic_info = get_product_basic_info(product_data)
                
                if st.button("분석 보고서 생성", type="primary"):
                    
                    report_title = f"{basic_info['product_name']}_리뷰 분석 보고서"
                    st.markdown(f"# {report_title}")
                    st.markdown("---")
                    
                    # 1. 제품 개요
                    st.markdown("## 제품 개요")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("총 리뷰수", f"{basic_info['total_reviews']:,}개")
                    col2.metric("다이소 순위", f"{basic_info['rank']}위")
                    col3.metric("제품 가격", basic_info['price'])
                    col4.metric("카테고리", basic_info['category'])
                    
                    # 2. 고객 만족도 분석
                    st.markdown("## 고객 만족도 분석")
                    
                    if basic_info['rating_counts']:
                        total_reviews = sum(basic_info['rating_counts'].values())
                        rating_5 = basic_info['rating_counts'].get('5점', 0)
                        rating_4 = basic_info['rating_counts'].get('4점', 0)
                        rating_3 = basic_info['rating_counts'].get('3점', 0)
                        rating_2 = basic_info['rating_counts'].get('2점', 0)
                        rating_1 = basic_info['rating_counts'].get('1점', 0)
                        
                        positive_ratio = (rating_5 + rating_4) / total_reviews * 100
                        negative_ratio = (rating_1 + rating_2 + rating_3) / total_reviews * 100
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("긍정 리뷰 비율", f"{positive_ratio:.1f}%", f"{rating_5 + rating_4}개")
                        col2.metric("부정 리뷰 비율", f"{negative_ratio:.1f}%", f"{rating_1 + rating_2 + rating_3}개")
                        
                        total_rating = (rating_5*5 + rating_4*4 + rating_3*3 + rating_2*2 + rating_1*1)
                        avg_rating = total_rating / total_reviews if total_reviews > 0 else 0
                        col3.metric("평균 평점", f"{avg_rating:.2f}/5.0")
                        
                        # 평점 분포 차트
                        rating_df = pd.DataFrame(list(basic_info['rating_counts'].items()), 
                                               columns=['평점', '개수'])
                        fig_rating = px.bar(rating_df, x='평점', y='개수', 
                                          title="평점 분포", text='개수')
                        fig_rating.update_traces(textposition='outside')
                        fig_rating.update_layout(height=300)
                        st.plotly_chart(fig_rating, use_container_width=True)
                    
                    # 3. 키워드 분석 결과
                    st.markdown("## 주요 키워드 분석")
                    
                    positive_keywords, negative_keywords = analyze_sentiment_keywords(product_data)
                    
                    if positive_keywords and negative_keywords:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 긍정 키워드 TOP 5")
                            pos_top5 = positive_keywords[:5]
                            for i, (keyword, freq) in enumerate(pos_top5, 1):
                                st.write(f"{i}. **{keyword}** ({freq}회)")
                        
                        with col2:
                            st.markdown("### 부정 키워드 TOP 5")
                            neg_top5 = negative_keywords[:5]
                            for i, (keyword, freq) in enumerate(neg_top5, 1):
                                st.write(f"{i}. **{keyword}** ({freq}회)")
                    
                    # 4. 시간별 트렌드 요약
                    st.markdown("## 시간별 트렌드 요약")
                    
                    if 'review_date' in product_data.columns and not product_data['review_date'].isna().all():
                        trend_data = product_data.dropna(subset=['review_date']).copy()
                        trend_data['rating_numeric'] = trend_data['rating'].apply(extract_rating)
                        
                        if len(trend_data) > 1:
                            monthly_counts = trend_data.groupby(trend_data['review_date'].dt.to_period('M')).size()
                            
                            if len(monthly_counts) > 1:
                                peak_month = monthly_counts.idxmax()
                                peak_count = monthly_counts.max()
                                recent_month = monthly_counts.index[-1]
                                recent_count = monthly_counts.iloc[-1]
                                
                                col1, col2, col3 = st.columns(3)
                                col1.metric("최고 리뷰 달", str(peak_month), f"{peak_count}개")
                                col2.metric("최근 리뷰 달", str(recent_month), f"{recent_count}개")
                                
                                if len(monthly_counts) >= 2:
                                    trend = "증가" if monthly_counts.iloc[-1] > monthly_counts.iloc[-2] else "감소"
                                    col3.metric("최근 트렌드", trend)
                                
                                fig_trend = px.line(
                                    x=[str(m) for m in monthly_counts.index], 
                                    y=monthly_counts.values,
                                    title="월별 리뷰수 추이",
                                    labels={'x': '월', 'y': '리뷰 수'}
                                )
                                fig_trend.update_traces(mode='lines+markers')
                                fig_trend.update_layout(height=300)
                                st.plotly_chart(fig_trend, use_container_width=True)
                    
                    # 5. 핵심 인사이트
                    st.markdown("## 핵심 인사이트")
                    
                    insights = []
                    
                    if basic_info['rating_counts']:
                        if positive_ratio >= 80:
                            insights.append(f"높은 고객 만족도: 긍정 리뷰가 {positive_ratio:.1f}%로 매우 높은 만족도를 보임")
                        elif positive_ratio >= 60:
                            insights.append(f"보통 고객 만족도: 긍정 리뷰가 {positive_ratio:.1f}%로 개선 여지가 있음")
                        else:
                            insights.append(f"낮은 고객 만족도: 긍정 리뷰가 {positive_ratio:.1f}%로 품질 개선이 필요함")
                    
                    if basic_info['total_reviews'] >= 500:
                        insights.append(f"높은 관심도: 총 {basic_info['total_reviews']}개의 리뷰로 높은 구매율 및 관심도 확인")
                    elif basic_info['total_reviews'] >= 100:
                        insights.append(f"적당한 관심도: 총 {basic_info['total_reviews']}개의 리뷰로 꾸준한 관심 확인")
                    else:
                        insights.append(f"낮은 관심도: 총 {basic_info['total_reviews']}개의 리뷰로 마케팅 강화 필요")
                    
                    if positive_keywords:
                        top_pos_keyword = positive_keywords[0][0]
                        insights.append(f"핵심 강점: '{top_pos_keyword}' 키워드가 가장 많이 언급되어 주요 장점으로 인식")
                    
                    if negative_keywords:
                        top_neg_keyword = negative_keywords[0][0]
                        insights.append(f"개선 포인트: '{top_neg_keyword}' 키워드 개선을 통한 고객 만족도 향상 가능")
                    
                    if basic_info['rank'] <= 10:
                        insights.append(f"우수한 성과: 다이소 {basic_info['rank']}위로 카테고리 내 상위권 제품")
                    elif basic_info['rank'] <= 50:
                        insights.append(f"중위권 성과: 다이소 {basic_info['rank']}위로 안정적인 성과")
                    
                    for insight in insights:
                        st.markdown(f"- {insight}")
                    
                    # 6. 보고서 정보
                    st.markdown("---")
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.caption(f"보고서 생성일: {current_time}")
                    st.caption(f"분석 기간: {basic_info['date_range']}")
                    st.caption(f"데이터 출처: 다이소몰 리뷰 ({basic_info['sort_type']})")
                    
                    st.markdown("---")
                    st.info("보고서 다운로드: 현재 화면을 인쇄하거나 PDF로 저장하실 수 있습니다.")
        
        else:
            st.warning("제품명 데이터가 없습니다.")

def show_daiso_sidebar_info(daiso_df):
    """다이소 데이터 정보 표시"""
    if not daiso_df.empty:
        st.sidebar.markdown("### 다이소 데이터 현황")
        st.sidebar.write(f"총 리뷰: {len(daiso_df):,}개")
        
        if 'category' in daiso_df.columns:
            st.sidebar.write("**카테고리별:**")
            for cat, count in daiso_df['category'].value_counts().items():
                st.sidebar.write(f"- {cat}: {count:,}개")
        
        if 'sort_type' in daiso_df.columns:
            st.sidebar.write("**정렬방식별:**")
            for sort_type, count in daiso_df['sort_type'].value_counts().items():
                st.sidebar.write(f"- {sort_type}: {count:,}개")

if __name__ == "__main__":
    render_daiso_section()