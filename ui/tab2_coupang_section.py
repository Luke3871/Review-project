import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import glob
import os

def load_coupang_data():
    """쿠팡 데이터 로딩"""
    coupang_dir = "../src/channels/coupang/data_coupang/reviews_coupang"
    csv_files = glob.glob(os.path.join(coupang_dir, "*.csv"))
    
    all_reviews = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            
            # 파일명에서 카테고리와 정렬방식 추출
            filename = os.path.basename(file)
            if 'makeup' in filename.lower():
                df['category'] = 'makeup'
            elif 'skincare' in filename.lower():
                df['category'] = 'skincare'
            else:
                df['category'] = 'unknown'
            
            # 정렬방식 추출
            if 'RANKED_COUPANG' in filename or '쿠팡랭킹순' in filename:
                df['sort_type'] = '쿠팡랭킹순'
            elif '판매량순' in filename:
                df['sort_type'] = '판매량순'
            else:
                df['sort_type'] = 'unknown'
            
            df['channel'] = 'coupang'
            all_reviews.append(df)
        except:
            try:
                df = pd.read_csv(file, encoding='cp949')
                filename = os.path.basename(file)
                if 'makeup' in filename.lower():
                    df['category'] = 'makeup'
                elif 'skincare' in filename.lower():
                    df['category'] = 'skincare'
                else:
                    df['category'] = 'unknown'
                
                if 'RANKED_COUPANG' in filename or '쿠팡랭킹순' in filename:
                    df['sort_type'] = '쿠팡랭킹순'
                elif '판매량순' in filename:
                    df['sort_type'] = '판매량순'
                else:
                    df['sort_type'] = 'unknown'
                
                df['channel'] = 'coupang'
                all_reviews.append(df)
            except:
                continue
    
    if all_reviews:
        df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        return df
    return pd.DataFrame()

def render_coupang_section():
    """쿠팡 분석 섹션 렌더링"""
    st.header("쿠팡 랭킹 분석")
    
    # 데이터 로딩
    coupang_df = load_coupang_data()
    
    if coupang_df.empty:
        st.warning("쿠팡 데이터를 로딩할 수 없습니다. (크롤링 진행 중일 수 있습니다)")
        st.info("예상 데이터: 메이크업 200개 + 스킨케어 200개 = 총 400개 제품")
        return
    
    # 데이터 현황
    total_products = len(coupang_df)
    makeup_count = len(coupang_df[coupang_df['category'] == 'makeup'])
    skincare_count = len(coupang_df[coupang_df['category'] == 'skincare'])
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 제품 수", f"{total_products:,}")
    col2.metric("메이크업", f"{makeup_count:,}")
    col3.metric("스킨케어", f"{skincare_count:,}")
    
    # 필터링 옵션
    st.subheader("필터 설정")
    col1, col2 = st.columns(2)
    
    with col1:
        categories = ['전체'] + list(coupang_df['category'].unique())
        selected_category = st.selectbox("카테고리", categories, key="coupang_category")
    
    with col2:
        if selected_category == '전체':
            available_sorts = list(coupang_df['sort_type'].unique())
        else:
            available_sorts = list(coupang_df[coupang_df['category'] == selected_category]['sort_type'].unique())
        
        sort_options = ['전체'] + available_sorts
        selected_sort = st.selectbox("정렬방식", sort_options, key="coupang_sort")
    
    # 데이터 필터링
    filtered_df = coupang_df.copy()
    if selected_category != '전체':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_sort != '전체':
        filtered_df = filtered_df[filtered_df['sort_type'] == selected_sort]
    
    st.markdown("---")
    
    # 분석 서브탭
    subtab1, subtab2, subtab3, subtab4 = st.tabs(["전체 트렌드", "제품별 분석", "랭킹 분석", "성과 분석"])
    
    with subtab1:
        st.subheader("전체 리뷰 트렌드")
        
        if 'review_date' in filtered_df.columns:
            time_df = filtered_df.dropna(subset=['review_date'])
            
            if not time_df.empty:
                time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="coupang_time_unit")
                
                if time_unit == "일별":
                    daily_counts = time_df.groupby(time_df['review_date'].dt.date).size()
                    fig = px.line(x=daily_counts.index, y=daily_counts.values,
                                title="일별 리뷰 수 변화", labels={'x': '날짜', 'y': '리뷰 수'})
                    fig.update_traces(mode='lines+markers')
                    st.plotly_chart(fig, use_container_width=True)
                    
                elif time_unit == "주별":
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
    
    with subtab2:
        st.subheader("제품별 분석")
        
        if 'product_name' in filtered_df.columns:
            products = list(filtered_df['product_name'].unique())
            selected_products = st.multiselect(
                "분석할 제품 선택 (최대 5개)", 
                products, 
                default=products[:3] if len(products) >= 3 else products,
                max_selections=5,
                key="coupang_products"
            )
            
            if selected_products and 'review_date' in filtered_df.columns:
                time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="coupang_product_time")
                
                trend_data = []
                for product in selected_products:
                    product_data = filtered_df[filtered_df['product_name'] == product].dropna(subset=['review_date'])
                    
                    if not product_data.empty:
                        if time_unit == "일별":
                            counts = product_data.groupby(product_data['review_date'].dt.date).size()
                        elif time_unit == "주별":
                            product_data['week'] = product_data['review_date'].dt.to_period('W')
                            counts = product_data.groupby('week').size()
                        else:
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
                    fig = px.line(trend_df, x='기간', y='리뷰수', color='제품명',
                                title=f"제품별 {time_unit} 리뷰 수 변화")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 제품별 통계
                    product_stats = []
                    for product in selected_products:
                        product_data = filtered_df[filtered_df['product_name'] == product]
                        stats = {
                            '제품명': product,
                            '총리뷰수': len(product_data),
                            '카테고리': product_data['category'].iloc[0] if len(product_data) > 0 else 'Unknown',
                            '정렬방식': product_data['sort_type'].iloc[0] if len(product_data) > 0 else 'Unknown'
                        }
                        
                        if 'rating' in product_data.columns:
                            def extract_rating(rating_str):
                                if pd.isna(rating_str):
                                    return np.nan
                                try:
                                    return float(rating_str)
                                except:
                                    return str(rating_str).count('★')
                            
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
    
    with subtab3:
        st.subheader("랭킹 분석")
        
        if 'sort_type' in filtered_df.columns and 'product_name' in filtered_df.columns:
            # 정렬방식별 상위 제품
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
                
                st.markdown("---")
            
            # 쿠팡랭킹순 vs 판매량순 비교
            if len(filtered_df['sort_type'].unique()) >= 2:
                st.subheader("쿠팡랭킹순 vs 판매량순 비교")
                
                comparison_data = []
                for category in filtered_df['category'].unique():
                    cat_data = filtered_df[filtered_df['category'] == category]
                    
                    for sort_type in cat_data['sort_type'].unique():
                        sort_cat_data = cat_data[cat_data['sort_type'] == sort_type]
                        
                        total_products = len(sort_cat_data['product_name'].unique())
                        total_reviews = len(sort_cat_data)
                        avg_reviews = total_reviews / total_products if total_products > 0 else 0
                        
                        comparison_data.append({
                            '카테고리': category,
                            '정렬방식': sort_type,
                            '제품수': total_products,
                            '총리뷰수': total_reviews,
                            '제품당평균리뷰': round(avg_reviews, 1)
                        })
                
                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    
                    fig = px.bar(comp_df, x='정렬방식', y='총리뷰수', color='카테고리',
                               title="쿠팡 정렬방식별 리뷰 수 비교", barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.dataframe(comp_df, use_container_width=True)
    
    with subtab4:
        st.subheader("성과 분석")
        
        if 'rating' in filtered_df.columns and 'product_name' in filtered_df.columns:
            product_performance = []
            
            for product in filtered_df['product_name'].unique():
                product_data = filtered_df[filtered_df['product_name'] == product]
                
                def extract_rating(rating_str):
                    if pd.isna(rating_str):
                        return np.nan
                    try:
                        return float(rating_str)
                    except:
                        return str(rating_str).count('★')
                
                product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                valid_ratings = product_data.dropna(subset=['rating_numeric'])
                
                if not valid_ratings.empty:
                    avg_rating = valid_ratings['rating_numeric'].mean()
                    review_count = len(product_data)
                    category = product_data['category'].iloc[0] if len(product_data) > 0 else 'Unknown'
                    sort_type = product_data['sort_type'].iloc[0] if len(product_data) > 0 else 'Unknown'
                    
                    product_performance.append({
                        '제품명': product,
                        '평균평점': avg_rating,
                        '리뷰수': review_count,
                        '카테고리': category,
                        '정렬방식': sort_type
                    })
            
            if product_performance:
                perf_df = pd.DataFrame(product_performance)
                
                # 산점도
                fig = px.scatter(perf_df, x='리뷰수', y='평균평점', 
                               color='정렬방식', size='리뷰수',
                               hover_data=['제품명', '카테고리'],
                               title="제품 성과 분석: 평점 vs 리뷰수")
                st.plotly_chart(fig, use_container_width=True)
                
                # 성과 순위
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**평점 높은 제품 TOP 10**")
                    top_rating = perf_df.nlargest(10, '평균평점')[['제품명', '평균평점', '리뷰수', '정렬방식']]
                    st.dataframe(top_rating, use_container_width=True)
                
                with col2:
                    st.write("**리뷰 많은 제품 TOP 10**")
                    top_reviews = perf_df.nlargest(10, '리뷰수')[['제품명', '리뷰수', '평균평점', '정렬방식']]
                    st.dataframe(top_reviews, use_container_width=True)
        
        # 정렬방식별 성과 비교
        st.subheader("정렬방식별 성과 비교")
        
        if 'sort_type' in filtered_df.columns:
            sort_performance = []
            
            for sort_type in filtered_df['sort_type'].unique():
                sort_data = filtered_df[filtered_df['sort_type'] == sort_type]
                
                total_products = len(sort_data['product_name'].unique())
                total_reviews = len(sort_data)
                avg_reviews_per_product = total_reviews / total_products if total_products > 0 else 0
                
                # 평점 통계
                if 'rating' in sort_data.columns:
                    def extract_rating(rating_str):
                        if pd.isna(rating_str):
                            return np.nan
                        try:
                            return float(rating_str)
                        except:
                            return str(rating_str).count('★')
                    
                    sort_data['rating_numeric'] = sort_data['rating'].apply(extract_rating)
                    valid_ratings = sort_data.dropna(subset=['rating_numeric'])
                    avg_rating = valid_ratings['rating_numeric'].mean() if not valid_ratings.empty else 0
                else:
                    avg_rating = 0
                
                sort_performance.append({
                    '정렬방식': sort_type,
                    '제품수': total_products,
                    '총리뷰수': total_reviews,
                    '제품당평균리뷰': round(avg_reviews_per_product, 1),
                    '평균평점': round(avg_rating, 2)
                })
            
            if sort_performance:
                sort_perf_df = pd.DataFrame(sort_performance)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(sort_perf_df, x='정렬방식', y='총리뷰수',
                               title="정렬방식별 총 리뷰 수", text='총리뷰수')
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.bar(sort_perf_df, x='정렬방식', y='평균평점',
                               title="정렬방식별 평균 평점", text='평균평점')
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(sort_perf_df, use_container_width=True)

def show_coupang_sidebar_info(coupang_df):
    """쿠팡 데이터 정보 표시"""
    if not coupang_df.empty:
        st.sidebar.markdown("### 쿠팡 데이터 현황")
        st.sidebar.write(f"총 제품: {len(coupang_df):,}개")
        
        if 'category' in coupang_df.columns:
            st.sidebar.write("**카테고리별:**")
            for cat, count in coupang_df['category'].value_counts().items():
                st.sidebar.write(f"- {cat}: {count:,}개")
        
        if 'sort_type' in coupang_df.columns:
            st.sidebar.write("**정렬방식별:**")
            for sort_type, count in coupang_df['sort_type'].value_counts().items():
                st.sidebar.write(f"- {sort_type}: {count:,}개")

if __name__ == "__main__":
    render_coupang_section()