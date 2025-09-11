# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import numpy as np
# from datetime import datetime, timedelta
# import glob
# import os

# def load_oliveyoung_data():
#     """올리브영 데이터 로딩"""
#     oliveyoung_dir = "../src/channels/oliveyoung/data_oliveyoung/reviews_oliveyoung"
#     csv_files = glob.glob(os.path.join(oliveyoung_dir, "*.csv"))
    
#     all_reviews = []
#     for file in csv_files:
#         try:
#             df = pd.read_csv(file, encoding='utf-8')
            
#             # 파일명에서 카테고리 추출
#             filename = os.path.basename(file)
#             if 'makeup' in filename.lower():
#                 df['category'] = 'makeup'
#             elif 'skincare' in filename.lower():
#                 df['category'] = 'skincare'
#             else:
#                 df['category'] = 'unknown'
            
#             # 올리브영은 정렬방식이 없음 (TOP 100)
#             df['sort_type'] = 'TOP_100'
#             df['channel'] = 'oliveyoung'
#             all_reviews.append(df)
#         except:
#             try:
#                 df = pd.read_csv(file, encoding='cp949')
#                 filename = os.path.basename(file)
#                 if 'makeup' in filename.lower():
#                     df['category'] = 'makeup'
#                 elif 'skincare' in filename.lower():
#                     df['category'] = 'skincare'
#                 else:
#                     df['category'] = 'unknown'
                
#                 df['sort_type'] = 'TOP_100'
#                 df['channel'] = 'oliveyoung'
#                 all_reviews.append(df)
#             except:
#                 continue
    
#     if all_reviews:
#         df = pd.concat(all_reviews, ignore_index=True)
#         if 'review_date' in df.columns:
#             df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
#         return df
#     return pd.DataFrame()

# def render_oliveyoung_section():
#     """올리브영 분석 섹션 렌더링"""
#     st.header("올리브영 랭킹 분석")
    
#     # 데이터 로딩
#     oliveyoung_df = load_oliveyoung_data()
    
#     if oliveyoung_df.empty:
#         st.warning("올리브영 데이터를 로딩할 수 없습니다.")
#         return
    
#     # 데이터 현황
#     total_products = len(oliveyoung_df)
#     makeup_count = len(oliveyoung_df[oliveyoung_df['category'] == 'makeup'])
#     skincare_count = len(oliveyoung_df[oliveyoung_df['category'] == 'skincare'])
    
#     col1, col2, col3 = st.columns(3)
#     col1.metric("총 제품 수", f"{total_products:,}")
#     col2.metric("메이크업", f"{makeup_count:,}")
#     col3.metric("스킨케어", f"{skincare_count:,}")
    
#     # 필터링 옵션
#     st.subheader("필터 설정")
    
#     categories = ['전체'] + list(oliveyoung_df['category'].unique())
#     selected_category = st.selectbox("카테고리", categories, key="oliveyoung_category")
    
#     # 데이터 필터링
#     if selected_category == '전체':
#         filtered_df = oliveyoung_df.copy()
#     else:
#         filtered_df = oliveyoung_df[oliveyoung_df['category'] == selected_category].copy()
    
#     st.markdown("---")
    
#     # 분석 서브탭
#     subtab1, subtab2, subtab3, subtab4 = st.tabs(["전체 트렌드", "제품별 분석", "랭킹 분석", "성과 분석"])
    
#     with subtab1:
#         st.subheader("전체 리뷰 트렌드")
        
#         if 'review_date' in filtered_df.columns:
#             time_df = filtered_df.dropna(subset=['review_date'])
            
#             if not time_df.empty:
#                 time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="oliveyoung_time_unit")
                
#                 if time_unit == "일별":
#                     daily_counts = time_df.groupby(time_df['review_date'].dt.date).size()
#                     fig = px.line(x=daily_counts.index, y=daily_counts.values,
#                                 title="일별 리뷰 수 변화", labels={'x': '날짜', 'y': '리뷰 수'})
#                     fig.update_traces(mode='lines+markers')
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                 elif time_unit == "주별":
#                     time_df['week'] = time_df['review_date'].dt.to_period('W')
#                     weekly_counts = time_df.groupby('week').size()
#                     fig = px.bar(x=[str(w) for w in weekly_counts.index], y=weekly_counts.values,
#                                title="주별 리뷰 수 변화", labels={'x': '주', 'y': '리뷰 수'})
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                 else:  # 월별
#                     time_df['month'] = time_df['review_date'].dt.to_period('M')
#                     monthly_counts = time_df.groupby('month').size()
#                     fig = px.bar(x=[str(m) for m in monthly_counts.index], y=monthly_counts.values,
#                                title="월별 리뷰 수 변화", labels={'x': '월', 'y': '리뷰 수'})
#                     st.plotly_chart(fig, use_container_width=True)
#             else:
#                 st.warning("시간 데이터가 없습니다.")
#         else:
#             st.warning("review_date 컬럼이 없습니다.")
    
#     with subtab2:
#         st.subheader("제품별 분석")
        
#         if 'product_name' in filtered_df.columns:
#             # 제품 선택 (멀티셀렉트)
#             products = list(filtered_df['product_name'].unique())
#             selected_products = st.multiselect(
#                 "분석할 제품 선택 (최대 5개)", 
#                 products, 
#                 default=products[:3] if len(products) >= 3 else products,
#                 max_selections=5,
#                 key="oliveyoung_products"
#             )
            
#             if selected_products and 'review_date' in filtered_df.columns:
#                 time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="oliveyoung_product_time")
                
#                 # 선택된 제품들의 시간별 트렌드
#                 trend_data = []
#                 for product in selected_products:
#                     product_data = filtered_df[filtered_df['product_name'] == product].dropna(subset=['review_date'])
                    
#                     if not product_data.empty:
#                         if time_unit == "일별":
#                             counts = product_data.groupby(product_data['review_date'].dt.date).size()
#                         elif time_unit == "주별":
#                             product_data['week'] = product_data['review_date'].dt.to_period('W')
#                             counts = product_data.groupby('week').size()
#                         else:  # 월별
#                             product_data['month'] = product_data['review_date'].dt.to_period('M')
#                             counts = product_data.groupby('month').size()
                        
#                         for period, count in counts.items():
#                             trend_data.append({
#                                 '기간': str(period),
#                                 '제품명': product,
#                                 '리뷰수': count
#                             })
                
#                 if trend_data:
#                     trend_df = pd.DataFrame(trend_data)
#                     fig = px.line(trend_df, x='기간', y='리뷰수', color='제품명',
#                                 title=f"제품별 {time_unit} 리뷰 수 변화")
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     # 제품별 통계 테이블
#                     product_stats = []
#                     for product in selected_products:
#                         product_data = filtered_df[filtered_df['product_name'] == product]
#                         stats = {
#                             '제품명': product,
#                             '총리뷰수': len(product_data),
#                             '카테고리': product_data['category'].iloc[0] if len(product_data) > 0 else 'Unknown'
#                         }
                        
#                         if 'rating' in product_data.columns:
#                             # 올리브영 평점 처리
#                             def extract_rating(rating_str):
#                                 if pd.isna(rating_str):
#                                     return np.nan
#                                 try:
#                                     return float(rating_str)
#                                 except:
#                                     return str(rating_str).count('★')
                            
#                             product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
#                             valid_ratings = product_data.dropna(subset=['rating_numeric'])
#                             if not valid_ratings.empty:
#                                 stats['평균평점'] = f"{valid_ratings['rating_numeric'].mean():.2f}"
#                             else:
#                                 stats['평균평점'] = "N/A"
#                         else:
#                             stats['평균평점'] = "N/A"
                        
#                         product_stats.append(stats)
                    
#                     st.subheader("선택 제품 상세 통계")
#                     st.dataframe(pd.DataFrame(product_stats), use_container_width=True)
#                 else:
#                     st.warning("선택된 제품의 시간 데이터가 없습니다.")
#             else:
#                 st.warning("제품을 선택해주세요.")
#         else:
#             st.warning("제품명 데이터가 없습니다.")
    
#     with subtab3:
#         st.subheader("랭킹 분석")
        
#         # 올리브영 TOP 100 제품 분석
#         if 'product_name' in filtered_df.columns:
            
#             # 카테고리별 상위 제품
#             for category in filtered_df['category'].unique():
#                 cat_data = filtered_df[filtered_df['category'] == category]
                
#                 st.write(f"**{category.upper()} 카테고리 TOP 10**")
                
#                 top_products = cat_data['product_name'].value_counts().head(10)
                
#                 if not top_products.empty:
#                     fig = px.bar(
#                         x=top_products.values,
#                         y=top_products.index,
#                         orientation='h',
#                         title=f"올리브영 {category} 상위 제품",
#                         labels={'x': '리뷰 수', 'y': '제품명'},
#                         text=top_products.values
#                     )
#                     fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
#                     fig.update_traces(textposition='outside')
#                     st.plotly_chart(fig, use_container_width=True)
#                 else:
#                     st.write("데이터가 없습니다.")
                
#                 st.markdown("---")
            
#             # 카테고리별 성과 비교
#             st.subheader("카테고리별 성과 비교")
            
#             category_comparison = []
#             for category in filtered_df['category'].unique():
#                 cat_data = filtered_df[filtered_df['category'] == category]
                
#                 total_products = len(cat_data['product_name'].unique())
#                 total_reviews = len(cat_data)
#                 avg_reviews_per_product = total_reviews / total_products if total_products > 0 else 0
                
#                 category_comparison.append({
#                     '카테고리': category,
#                     '제품수': total_products,
#                     '총리뷰수': total_reviews,
#                     '제품당평균리뷰': round(avg_reviews_per_product, 1)
#                 })
            
#             if category_comparison:
#                 cat_comp_df = pd.DataFrame(category_comparison)
                
#                 fig = px.bar(cat_comp_df, x='카테고리', y='총리뷰수',
#                            title="올리브영 카테고리별 리뷰 수", text='총리뷰수')
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
                
#                 st.dataframe(cat_comp_df, use_container_width=True)
    
#     with subtab4:
#         st.subheader("성과 분석")
        
#         # 평점 vs 리뷰수 산점도
#         if 'rating' in filtered_df.columns and 'product_name' in filtered_df.columns:
#             # 제품별 평점과 리뷰수 계산
#             product_performance = []
            
#             for product in filtered_df['product_name'].unique():
#                 product_data = filtered_df[filtered_df['product_name'] == product]
                
#                 # 올리브영 평점 처리
#                 def extract_rating(rating_str):
#                     if pd.isna(rating_str):
#                         return np.nan
#                     try:
#                         return float(rating_str)
#                     except:
#                         return str(rating_str).count('★')
                
#                 product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
#                 valid_ratings = product_data.dropna(subset=['rating_numeric'])
                
#                 if not valid_ratings.empty:
#                     avg_rating = valid_ratings['rating_numeric'].mean()
#                     review_count = len(product_data)
#                     category = product_data['category'].iloc[0] if len(product_data) > 0 else 'Unknown'
                    
#                     product_performance.append({
#                         '제품명': product,
#                         '평균평점': avg_rating,
#                         '리뷰수': review_count,
#                         '카테고리': category
#                     })
            
#             if product_performance:
#                 perf_df = pd.DataFrame(product_performance)
                
#                 # 산점도
#                 fig = px.scatter(perf_df, x='리뷰수', y='평균평점', 
#                                color='카테고리', size='리뷰수',
#                                hover_data=['제품명'],
#                                title="제품 성과 분석: 평점 vs 리뷰수")
#                 st.plotly_chart(fig, use_container_width=True)
                
#                 # 성과 순위
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.write("**평점 높은 제품 TOP 10**")
#                     top_rating = perf_df.nlargest(10, '평균평점')[['제품명', '평균평점', '리뷰수', '카테고리']]
#                     st.dataframe(top_rating, use_container_width=True)
                
#                 with col2:
#                     st.write("**리뷰 많은 제품 TOP 10**")
#                     top_reviews = perf_df.nlargest(10, '리뷰수')[['제품명', '리뷰수', '평균평점', '카테고리']]
#                     st.dataframe(top_reviews, use_container_width=True)
        
#         # 카테고리별 성과 분석
#         st.subheader("카테고리별 성과 분석")
        
#         if 'category' in filtered_df.columns:
#             beauty_performance = []
            
#             for category in filtered_df['category'].unique():
#                 cat_data = filtered_df[filtered_df['category'] == category]
                
#                 total_products = len(cat_data['product_name'].unique())
#                 total_reviews = len(cat_data)
#                 avg_reviews_per_product = total_reviews / total_products if total_products > 0 else 0
                
#                 # 평점 통계
#                 if 'rating' in cat_data.columns:
#                     def extract_rating(rating_str):
#                         if pd.isna(rating_str):
#                             return np.nan
#                         try:
#                             return float(rating_str)
#                         except:
#                             return str(rating_str).count('★')
                    
#                     cat_data['rating_numeric'] = cat_data['rating'].apply(extract_rating)
#                     valid_ratings = cat_data.dropna(subset=['rating_numeric'])
#                     avg_rating = valid_ratings['rating_numeric'].mean() if not valid_ratings.empty else 0
#                 else:
#                     avg_rating = 0
                
#                 beauty_performance.append({
#                     '카테고리': category,
#                     '제품수': total_products,
#                     '총리뷰수': total_reviews,
#                     '제품당평균리뷰': round(avg_reviews_per_product, 1),
#                     '평균평점': round(avg_rating, 2)
#                 })
            
#             if beauty_performance:
#                 beauty_perf_df = pd.DataFrame(beauty_performance)
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     fig = px.bar(beauty_perf_df, x='카테고리', y='제품당평균리뷰',
#                                title="카테고리별 제품당 평균 리뷰", text='제품당평균리뷰')
#                     fig.update_traces(textposition='outside')
#                     st.plotly_chart(fig, use_container_width=True)
                
#                 with col2:
#                     fig = px.bar(beauty_perf_df, x='카테고리', y='평균평점',
#                                title="카테고리별 평균 평점", text='평균평점')
#                     fig.update_traces(textposition='outside')
#                     st.plotly_chart(fig, use_container_width=True)
                
#                 st.dataframe(beauty_perf_df, use_container_width=True)

# # 사이드바 정보
# def show_oliveyoung_sidebar_info(oliveyoung_df):
#     """올리브영 데이터 정보 표시"""
#     if not oliveyoung_df.empty:
#         st.sidebar.markdown("### 올리브영 데이터 현황")
#         st.sidebar.write(f"총 제품: {len(oliveyoung_df):,}개")
        
#         if 'category' in oliveyoung_df.columns:
#             st.sidebar.write("**카테고리별:**")
#             for cat, count in oliveyoung_df['category'].value_counts().items():
#                 st.sidebar.write(f"- {cat}: {count:,}개")

# if __name__ == "__main__":
#     render_oliveyoung_section()


#//==============================================================================//#
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import glob
import os

def load_oliveyoung_data():
    """올리브영 데이터 로딩"""
    oliveyoung_dir = "../src/channels/oliveyoung/data_oliveyoung/reviews_oliveyoung"
    csv_files = glob.glob(os.path.join(oliveyoung_dir, "*.csv"))
    
    all_reviews = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, encoding='utf-8')
            
            # 파일명에서 카테고리 추출
            filename = os.path.basename(file)
            if 'makeup' in filename.lower():
                df['category'] = 'makeup'
            elif 'skincare' in filename.lower():
                df['category'] = 'skincare'
            else:
                df['category'] = 'makeup'  # 기본값
            
            # 올리브영은 랭킹 정렬
            df['sort_type'] = 'RANKED'
            df['channel'] = 'oliveyoung'
            
            # 컬럼명 매핑 (기존 다이소 구조와 맞추기)
            if 'name' in df.columns:
                df['product_name'] = df['name']
            if 'review' in df.columns:
                df['review_text'] = df['review']
            
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
                    df['category'] = 'makeup'
                
                df['sort_type'] = 'RANKED'
                df['channel'] = 'oliveyoung'
                
                if 'name' in df.columns:
                    df['product_name'] = df['name']
                if 'review' in df.columns:
                    df['review_text'] = df['review']
                
                all_reviews.append(df)
            except:
                continue
    
    if all_reviews:
        df = pd.concat(all_reviews, ignore_index=True)
        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        return df
    return pd.DataFrame()

def extract_rating(rating_value):
    """올리브영 평점 처리 (이미 Float 타입)"""
    if pd.isna(rating_value):
        return np.nan
    
    # 이미 숫자인 경우
    if isinstance(rating_value, (int, float)):
        return float(rating_value)
    
    # 문자열인 경우 처리
    try:
        return float(rating_value)
    except:
        return np.nan

def render_oliveyoung_section():
    """올리브영 분석 섹션 렌더링"""
    st.header("올리브영 랭킹 분석")
    
    # 데이터 로딩
    oliveyoung_df = load_oliveyoung_data()
    
    if oliveyoung_df.empty:
        st.warning("올리브영 데이터를 로딩할 수 없습니다.")
        return
    
    # 데이터 현황
    total_reviews = len(oliveyoung_df)
    makeup_reviews = len(oliveyoung_df[oliveyoung_df['category'] == 'makeup']) if 'category' in oliveyoung_df.columns else 0
    skincare_reviews = len(oliveyoung_df[oliveyoung_df['category'] == 'skincare']) if 'category' in oliveyoung_df.columns else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("총 리뷰 수", f"{total_reviews:,}")
    col2.metric("메이크업", f"{makeup_reviews:,}")
    col3.metric("스킨케어", f"{skincare_reviews:,}")
    
    # 필터링 옵션
    st.subheader("필터 설정")
    
    if 'category' in oliveyoung_df.columns:
        categories = ['전체'] + list(oliveyoung_df['category'].unique())
        selected_category = st.selectbox("카테고리", categories, key="oliveyoung_category")
    else:
        selected_category = '전체'
    
    # 데이터 필터링
    if selected_category == '전체':
        filtered_df = oliveyoung_df.copy()
    else:
        filtered_df = oliveyoung_df[oliveyoung_df['category'] == selected_category].copy()
    
    st.markdown("---")
    
    # 분석 서브탭
    subtab1, subtab2, subtab3, subtab4 = st.tabs(["전체 트렌드", "제품별 분석", "랭킹 분석", "성과 분석"])
    
    with subtab1:
        st.subheader("전체 리뷰 트렌드")
        
        if 'review_date' in filtered_df.columns:
            time_df = filtered_df.dropna(subset=['review_date'])
            
            if not time_df.empty:
                time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="oliveyoung_time_unit")
                
                if time_unit == "일별":
                    daily_counts = time_df.groupby(time_df['review_date'].dt.date).size()
                    fig = px.bar(x=daily_counts.index, y=daily_counts.values,
                                title="일별 리뷰 수 변화", labels={'x': '날짜', 'y': '리뷰 수'})
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
            # 제품 선택 (멀티셀렉트)
            products = list(filtered_df['product_name'].unique())
            selected_products = st.multiselect(
                "분석할 제품 선택 (최대 5개)", 
                products, 
                default=products[:3] if len(products) >= 3 else products,
                max_selections=5,
                key="oliveyoung_products"
            )
            
            if selected_products and 'review_date' in filtered_df.columns:
                time_unit = st.radio("시간 단위", ["일별", "주별", "월별"], horizontal=True, key="oliveyoung_product_time")
                
                # 선택된 제품들의 시간별 트렌드
                trend_data = []
                for product in selected_products:
                    product_data = filtered_df[filtered_df['product_name'] == product].dropna(subset=['review_date'])
                    
                    if not product_data.empty:
                        if time_unit == "일별":
                            counts = product_data.groupby(product_data['review_date'].dt.date).size()
                        elif time_unit == "주별":
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
                    
                    # 제품별 통계 테이블
                    product_stats = []
                    for product in selected_products:
                        product_data = filtered_df[filtered_df['product_name'] == product]
                        stats = {
                            '제품명': product,
                            '총리뷰수': len(product_data),
                            '카테고리': product_data['category'].iloc[0] if len(product_data) > 0 and 'category' in product_data.columns else 'Unknown'
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
    
    with subtab3:
        st.subheader("랭킹 분석")
        
        # 올리브영 상위 제품 분석
        if 'product_name' in filtered_df.columns:
            
            # 카테고리별 상위 제품 (조건부 표시)
            if 'category' in filtered_df.columns:
                categories = filtered_df['category'].unique()
                
                if len(categories) >= 2:
                    # 카테고리가 여러 개일 때만 카테고리별 표시
                    for category in categories:
                        cat_data = filtered_df[filtered_df['category'] == category]
                        
                        st.write(f"**{category.upper()} 카테고리 TOP 10**")
                        
                        top_products = cat_data['product_name'].value_counts().head(10)
                        
                        if not top_products.empty:
                            fig = px.bar(
                                x=top_products.values,
                                y=top_products.index,
                                orientation='h',
                                title=f"올리브영 {category} 상위 제품",
                                labels={'x': '리뷰 수', 'y': '제품명'},
                                text=top_products.values
                            )
                            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                            fig.update_traces(textposition='outside')
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.write("데이터가 없습니다.")
                        
                        st.markdown("---")
                else:
                    # 단일 카테고리일 때는 전체 상위 제품 표시
                    st.write("**상위 제품 TOP 10**")
                    top_products = filtered_df['product_name'].value_counts().head(10)
                    
                    if not top_products.empty:
                        fig = px.bar(
                            x=top_products.values,
                            y=top_products.index,
                            orientation='h',
                            title="올리브영 상위 제품",
                            labels={'x': '리뷰 수', 'y': '제품명'},
                            text=top_products.values
                        )
                        fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
                        fig.update_traces(textposition='outside')
                        st.plotly_chart(fig, use_container_width=True)
            
            # 실제 순위 vs 리뷰수 분석 (rank 컬럼 활용)
            if 'rank' in filtered_df.columns:
                st.subheader("순위별 리뷰 수 분석")
                
                # 제품별 평균 순위와 리뷰 수
                rank_analysis = filtered_df.groupby('product_name').agg({
                    'rank': 'mean',
                    'product_name': 'count'
                }).rename(columns={'product_name': 'review_count'}).reset_index()
                
                # 상위 20개 제품만 표시
                rank_analysis = rank_analysis.nlargest(20, 'review_count')
                
                fig = px.scatter(rank_analysis, x='rank', y='review_count',
                               hover_data=['product_name'],
                               title="제품 순위 vs 리뷰 수",
                               labels={'rank': '평균 순위', 'review_count': '리뷰 수'})
                st.plotly_chart(fig, use_container_width=True)
    
    with subtab4:
        st.subheader("성과 분석")
        
        # 평점 vs 리뷰수 산점도
        if 'rating' in filtered_df.columns and 'product_name' in filtered_df.columns:
            # 제품별 평점과 리뷰수 계산
            product_performance = []
            
            for product in filtered_df['product_name'].unique():
                product_data = filtered_df[filtered_df['product_name'] == product]
                
                product_data['rating_numeric'] = product_data['rating'].apply(extract_rating)
                valid_ratings = product_data.dropna(subset=['rating_numeric'])
                
                if not valid_ratings.empty:
                    avg_rating = valid_ratings['rating_numeric'].mean()
                    review_count = len(product_data)
                    category = product_data['category'].iloc[0] if 'category' in product_data.columns else 'Unknown'
                    avg_rank = product_data['rank'].mean() if 'rank' in product_data.columns else None
                    
                    product_performance.append({
                        '제품명': product,
                        '평균평점': avg_rating,
                        '리뷰수': review_count,
                        '카테고리': category,
                        '평균순위': avg_rank
                    })
            
            if product_performance:
                perf_df = pd.DataFrame(product_performance)
                
                # 산점도
                fig = px.scatter(perf_df, x='리뷰수', y='평균평점', 
                               color='카테고리', size='리뷰수',
                               hover_data=['제품명', '평균순위'],
                               title="제품 성과 분석: 평점 vs 리뷰수")
                st.plotly_chart(fig, use_container_width=True)
                
                # 성과 순위
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**평점 높은 제품 TOP 10**")
                    top_rating = perf_df.nlargest(10, '평균평점')[['제품명', '평균평점', '리뷰수', '카테고리']]
                    st.dataframe(top_rating, use_container_width=True)
                
                with col2:
                    st.write("**리뷰 많은 제품 TOP 10**")
                    top_reviews = perf_df.nlargest(10, '리뷰수')[['제품명', '리뷰수', '평균평점', '카테고리']]
                    st.dataframe(top_reviews, use_container_width=True)
        
        # 평점 분포 분석
        if 'rating' in filtered_df.columns:
            st.subheader("평점 분포")
            
            filtered_df['rating_numeric'] = filtered_df['rating'].apply(extract_rating)
            valid_ratings = filtered_df.dropna(subset=['rating_numeric'])
            
            if not valid_ratings.empty:
                fig = px.histogram(valid_ratings, x='rating_numeric', 
                                 title="평점 분포", nbins=20,
                                 labels={'rating_numeric': '평점', 'count': '빈도'})
                st.plotly_chart(fig, use_container_width=True)
                
                # 평점 통계
                col1, col2, col3 = st.columns(3)
                col1.metric("평균 평점", f"{valid_ratings['rating_numeric'].mean():.2f}")
                col2.metric("최고 평점", f"{valid_ratings['rating_numeric'].max():.1f}")
                col3.metric("평점 표준편차", f"{valid_ratings['rating_numeric'].std():.2f}")

# 사이드바 정보
def show_oliveyoung_sidebar_info(oliveyoung_df):
    """올리브영 데이터 정보 표시"""
    if not oliveyoung_df.empty:
        st.sidebar.markdown("### 올리브영 데이터 현황")
        st.sidebar.write(f"총 리뷰: {len(oliveyoung_df):,}개")
        
        if 'category' in oliveyoung_df.columns:
            st.sidebar.write("**카테고리별:**")
            for cat, count in oliveyoung_df['category'].value_counts().items():
                st.sidebar.write(f"- {cat}: {count:,}개")

if __name__ == "__main__":
    render_oliveyoung_section()