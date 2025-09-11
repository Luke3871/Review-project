# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import glob
# import os
# import numpy as np
# from datetime import datetime, timedelta

# # 페이지 설정
# st.set_page_config(
#     page_title="다채널 리뷰 분석",
#     layout="wide"
# )

# st.title("다채널 리뷰 분석 대시보드")

# @st.cache_data
# def load_review_data():
#     """모든 채널의 리뷰 데이터 로딩"""
#     all_reviews = []
    
#     # 1. 다이소 데이터 로딩
#     daiso_dir = "../src/channels/daiso/data_daiso/reviews_daiso"
#     daiso_files = glob.glob(os.path.join(daiso_dir, "*_reviews.csv"))
    
#     for file in daiso_files:
#         try:
#             df = pd.read_csv(file, encoding='utf-8')
#             df['channel'] = 'daiso'
#             all_reviews.append(df)
#         except:
#             try:
#                 df = pd.read_csv(file, encoding='cp949')
#                 df['channel'] = 'daiso'
#                 all_reviews.append(df)
#             except:
#                 continue
    
#     # 2. 스킨케어 데이터 로딩 (skincare_LIKE_BEST로 시작하는 파일들)
#     skincare_dir = "../src/channels/daiso/data_daiso/reviews_daiso"  # 같은 폴더에 있다고 가정
#     skincare_files = glob.glob(os.path.join(skincare_dir, "skincare_*.csv"))
    
#     for file in skincare_files:
#         try:
#             df = pd.read_csv(file, encoding='utf-8')
#             df['channel'] = 'skincare'
#             all_reviews.append(df)
#         except:
#             try:
#                 df = pd.read_csv(file, encoding='cp949')
#                 df['channel'] = 'skincare'
#                 all_reviews.append(df)
#             except:
#                 continue
    
#     # 3. 쿠팡 데이터 로딩
#     coupang_dir = "../src/channels/coupang/data_coupang/reviews_coupang"
#     coupang_files = glob.glob(os.path.join(coupang_dir, "*.csv"))
    
#     for file in coupang_files:
#         try:
#             df = pd.read_csv(file, encoding='utf-8')
#             df['channel'] = 'coupang'
#             all_reviews.append(df)
#         except:
#             try:
#                 df = pd.read_csv(file, encoding='cp949')
#                 df['channel'] = 'coupang'
#                 all_reviews.append(df)
#             except:
#                 continue
    
#     if all_reviews:
#         df = pd.concat(all_reviews, ignore_index=True)
#         if 'review_date' in df.columns:
#             df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
#         return df
    
#     return pd.DataFrame()

# # 데이터 로딩
# review_df = load_review_data()

# if review_df.empty:
#     st.error("데이터를 로딩할 수 없습니다.")
#     st.stop()

# # 데이터 현황 표시
# st.info(f"총 {len(review_df):,}개의 리뷰 데이터를 로딩했습니다.")

# # 채널별 데이터 현황
# if 'channel' in review_df.columns:
#     channel_counts = review_df['channel'].value_counts()
#     st.write("**채널별 데이터 현황:**")
#     for channel, count in channel_counts.items():
#         st.write(f"- {channel}: {count:,}개")

# # 사이드바 필터
# st.sidebar.header("필터 설정")

# # 1. 채널 선택
# channels = ['전체']
# if 'channel' in review_df.columns:
#     channels.extend(list(review_df['channel'].unique()))
# selected_channel = st.sidebar.selectbox("채널 선택", channels)

# # 채널 필터링된 데이터
# if selected_channel == '전체':
#     channel_filtered = review_df.copy()
# else:
#     channel_filtered = review_df[review_df['channel'] == selected_channel].copy()

# # 2. 카테고리 선택
# categories = ['전체']
# if 'category' in channel_filtered.columns:
#     categories.extend(list(channel_filtered['category'].unique()))
# selected_category = st.sidebar.selectbox("카테고리 선택", categories)

# # 카테고리 필터링된 데이터
# if selected_category == '전체':
#     category_filtered = channel_filtered.copy()
# else:
#     category_filtered = channel_filtered[channel_filtered['category'] == selected_category].copy()

# # 3. 정렬방식 선택
# sort_types = ['전체']
# if 'sort_type' in category_filtered.columns:
#     sort_types.extend(list(category_filtered['sort_type'].unique()))
# selected_sort = st.sidebar.selectbox("정렬방식 선택", sort_types)

# # 정렬방식 필터링된 데이터
# if selected_sort == '전체':
#     sort_filtered = category_filtered.copy()
# else:
#     sort_filtered = category_filtered[category_filtered['sort_type'] == selected_sort].copy()

# # 4. 제품 선택
# products = ['전체']
# if 'product_name' in sort_filtered.columns:
#     unique_products = sort_filtered['product_name'].unique()
#     products.extend(sorted(unique_products))
# selected_product = st.sidebar.selectbox("제품 선택", products)

# # 최종 필터링된 데이터
# if selected_product == '전체':
#     filtered_df = sort_filtered.copy()
# else:
#     filtered_df = sort_filtered[sort_filtered['product_name'] == selected_product].copy()

# # 선택 정보 표시
# st.markdown("---")
# col1, col2, col3, col4, col5 = st.columns(5)

# with col1:
#     st.metric("채널", selected_channel)
# with col2:
#     st.metric("카테고리", selected_category)
# with col3:
#     st.metric("정렬방식", selected_sort)
# with col4:
#     display_product = selected_product
#     if len(selected_product) > 15:
#         display_product = selected_product[:15] + "..."
#     st.metric("제품", display_product)
# with col5:
#     st.metric("리뷰 수", f"{len(filtered_df):,}")

# st.markdown("---")

# # 메인 분석 탭
# tab1, tab2, tab3, tab4 = st.tabs(["기초 통계", "증가율 분석", "감성 분석", "채널 비교"])

# with tab1:
#     # 기초 통계 탭
#     st.header("기초 통계")
    
#     # 1. 제품별 리뷰 수
#     st.subheader("제품별 리뷰 수")
    
#     if not filtered_df.empty and 'product_name' in filtered_df.columns:
#         product_counts = filtered_df['product_name'].value_counts().head(20)
        
#         fig = px.bar(
#             x=product_counts.values,
#             y=product_counts.index,
#             orientation='h',
#             title="제품별 리뷰 수 (TOP 20)",
#             labels={'x': '리뷰 수', 'y': '제품명'},
#             text=product_counts.values
#         )
#         fig.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
#         fig.update_traces(textposition='outside')
#         st.plotly_chart(fig, use_container_width=True)
        
#         # 상세 테이블
#         st.subheader("제품별 리뷰 수 상세")
#         product_table = pd.DataFrame({
#             '제품명': product_counts.index,
#             '리뷰수': product_counts.values
#         }).reset_index(drop=True)
#         st.dataframe(product_table, use_container_width=True)
    
#     # 2. 시간별 리뷰 변화
#     st.subheader("시간별 리뷰 변화")
    
#     if not filtered_df.empty and 'review_date' in filtered_df.columns:
#         time_df = filtered_df.dropna(subset=['review_date']).copy()
        
#         if not time_df.empty:
#             time_tab1, time_tab2, time_tab3 = st.tabs(["일별", "주별", "월별"])
            
#             with time_tab1:
#                 daily_counts = time_df.groupby(time_df['review_date'].dt.date).size()
                
#                 total_reviews = daily_counts.sum()
#                 total_days = len(daily_counts)
#                 avg_daily = total_reviews / total_days if total_days > 0 else 0
                
#                 col1, col2, col3 = st.columns(3)
#                 col1.metric("총 리뷰 수", f"{total_reviews:,}")
#                 col2.metric("총 일수", f"{total_days}")
#                 col3.metric("일평균 리뷰", f"{avg_daily:.1f}")
                
#                 fig = px.line(
#                     x=daily_counts.index,
#                     y=daily_counts.values,
#                     title="일별 리뷰 수 변화",
#                     labels={'x': '날짜', 'y': '리뷰 수'}
#                 )
#                 fig.update_traces(mode='lines+markers')
#                 st.plotly_chart(fig, use_container_width=True)
            
#             with time_tab2:
#                 time_df['week'] = time_df['review_date'].dt.to_period('W')
#                 weekly_counts = time_df.groupby('week').size()
                
#                 total_reviews = weekly_counts.sum()
#                 total_weeks = len(weekly_counts)
#                 avg_weekly = total_reviews / total_weeks if total_weeks > 0 else 0
                
#                 col1, col2, col3 = st.columns(3)
#                 col1.metric("총 리뷰 수", f"{total_reviews:,}")
#                 col2.metric("총 주수", f"{total_weeks}")
#                 col3.metric("주평균 리뷰", f"{avg_weekly:.1f}")
                
#                 fig = px.bar(
#                     x=[str(w) for w in weekly_counts.index],
#                     y=weekly_counts.values,
#                     title="주별 리뷰 수 변화",
#                     labels={'x': '주', 'y': '리뷰 수'},
#                     text=weekly_counts.values
#                 )
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
            
#             with time_tab3:
#                 time_df['month'] = time_df['review_date'].dt.to_period('M')
#                 monthly_counts = time_df.groupby('month').size()
                
#                 total_reviews = monthly_counts.sum()
#                 total_months = len(monthly_counts)
#                 avg_monthly = total_reviews / total_months if total_months > 0 else 0
                
#                 col1, col2, col3 = st.columns(3)
#                 col1.metric("총 리뷰 수", f"{total_reviews:,}")
#                 col2.metric("총 월수", f"{total_months}")
#                 col3.metric("월평균 리뷰", f"{avg_monthly:.1f}")
                
#                 fig = px.bar(
#                     x=[str(m) for m in monthly_counts.index],
#                     y=monthly_counts.values,
#                     title="월별 리뷰 수 변화",
#                     labels={'x': '월', 'y': '리뷰 수'},
#                     text=monthly_counts.values
#                 )
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("유효한 날짜 데이터가 없습니다.")
#     else:
#         st.warning("시간 분석을 위한 날짜 데이터가 없습니다.")

# with tab2:
#     # 증가율 분석 탭 (실제 데이터 사용)
#     st.header("증가율 분석")
    
#     if not filtered_df.empty and 'review_date' in filtered_df.columns:
#         time_df = filtered_df.dropna(subset=['review_date']).copy()
        
#         if len(time_df) > 7:  # 최소 7일 이상 데이터가 있어야 증가율 계산 가능
#             # 현재 날짜 기준으로 기간 설정
#             today = datetime.now().date()
#             week_ago = today - timedelta(days=7)
#             two_weeks_ago = today - timedelta(days=14)
#             month_ago = today - timedelta(days=30)
#             two_months_ago = today - timedelta(days=60)
            
#             growth_tab1, growth_tab2, growth_tab3 = st.tabs(["7일 증가율", "30일 증가율", "제품별 성장 트렌드"])
            
#             with growth_tab1:
#                 st.subheader("최근 7일 vs 이전 7일 증가율")
                
#                 # 최근 7일 리뷰
#                 recent_week = time_df[time_df['review_date'].dt.date >= week_ago]
#                 previous_week = time_df[
#                     (time_df['review_date'].dt.date >= two_weeks_ago) & 
#                     (time_df['review_date'].dt.date < week_ago)
#                 ]
                
#                 if 'product_name' in time_df.columns:
#                     # 제품별 증가율 계산
#                     recent_counts = recent_week['product_name'].value_counts()
#                     previous_counts = previous_week['product_name'].value_counts()
                    
#                     growth_data = []
#                     for product in recent_counts.index:
#                         recent_count = recent_counts[product]
#                         previous_count = previous_counts.get(product, 0)
                        
#                         if previous_count > 0:
#                             growth_rate = ((recent_count - previous_count) / previous_count) * 100
#                         else:
#                             growth_rate = float('inf') if recent_count > 0 else 0
                        
#                         growth_data.append({
#                             '제품명': product,
#                             '최근_7일': recent_count,
#                             '이전_7일': previous_count,
#                             '증가율': growth_rate
#                         })
                    
#                     if growth_data:
#                         growth_df = pd.DataFrame(growth_data)
#                         growth_df = growth_df[growth_df['증가율'] != float('inf')].sort_values('증가율', ascending=False)
                        
#                         # 상위 10개 제품 증가율 차트
#                         top_growth = growth_df.head(10)
                        
#                         fig = px.bar(
#                             top_growth,
#                             x='증가율',
#                             y='제품명',
#                             orientation='h',
#                             title="제품별 7일 증가율 TOP 10",
#                             labels={'증가율': '증가율 (%)', '제품명': '제품명'},
#                             text='증가율'
#                         )
#                         fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
#                         fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
#                         st.plotly_chart(fig, use_container_width=True)
                        
#                         # 상세 테이블
#                         st.dataframe(growth_df.head(20), use_container_width=True)
#                 else:
#                     st.warning("제품 정보가 없습니다.")
            
#             with growth_tab2:
#                 st.subheader("최근 30일 vs 이전 30일 증가율")
                
#                 # 최근 30일 리뷰
#                 recent_month = time_df[time_df['review_date'].dt.date >= month_ago]
#                 previous_month = time_df[
#                     (time_df['review_date'].dt.date >= two_months_ago) & 
#                     (time_df['review_date'].dt.date < month_ago)
#                 ]
                
#                 col1, col2, col3 = st.columns(3)
#                 col1.metric("최근 30일 리뷰", f"{len(recent_month):,}")
#                 col2.metric("이전 30일 리뷰", f"{len(previous_month):,}")
                
#                 if len(previous_month) > 0:
#                     overall_growth = ((len(recent_month) - len(previous_month)) / len(previous_month)) * 100
#                     col3.metric("전체 증가율", f"{overall_growth:.1f}%")
#                 else:
#                     col3.metric("전체 증가율", "신규")
                
#                 # 월별 증가율 계산 (제품별)
#                 if 'product_name' in time_df.columns and len(recent_month) > 0 and len(previous_month) > 0:
#                     recent_counts = recent_month['product_name'].value_counts()
#                     previous_counts = previous_month['product_name'].value_counts()
                    
#                     monthly_growth_data = []
#                     for product in recent_counts.index:
#                         recent_count = recent_counts[product]
#                         previous_count = previous_counts.get(product, 0)
                        
#                         if previous_count > 0:
#                             growth_rate = ((recent_count - previous_count) / previous_count) * 100
#                         else:
#                             growth_rate = float('inf') if recent_count > 0 else 0
                        
#                         monthly_growth_data.append({
#                             '제품명': product,
#                             '최근_30일': recent_count,
#                             '이전_30일': previous_count,
#                             '증가율': growth_rate
#                         })
                    
#                     if monthly_growth_data:
#                         monthly_df = pd.DataFrame(monthly_growth_data)
#                         monthly_df = monthly_df[monthly_df['증가율'] != float('inf')].sort_values('증가율', ascending=False)
                        
#                         st.dataframe(monthly_df.head(20), use_container_width=True)
            
#             with growth_tab3:
#                 st.subheader("제품별 성장 트렌드")
                
#                 # 일별 누적 리뷰 수 추이
#                 if 'product_name' in time_df.columns:
#                     # 상위 5개 제품 선택
#                     top_products = time_df['product_name'].value_counts().head(5).index
                    
#                     # 각 제품의 일별 누적 리뷰 수 계산
#                     trend_data = []
#                     for product in top_products:
#                         product_data = time_df[time_df['product_name'] == product].copy()
#                         daily_counts = product_data.groupby(product_data['review_date'].dt.date).size().cumsum()
                        
#                         for date, cumulative_count in daily_counts.items():
#                             trend_data.append({
#                                 '날짜': date,
#                                 '제품명': product,
#                                 '누적_리뷰수': cumulative_count
#                             })
                    
#                     if trend_data:
#                         trend_df = pd.DataFrame(trend_data)
                        
#                         fig = px.line(
#                             trend_df,
#                             x='날짜',
#                             y='누적_리뷰수',
#                             color='제품명',
#                             title="상위 제품별 누적 리뷰 수 트렌드",
#                             labels={'누적_리뷰수': '누적 리뷰 수', '날짜': '날짜'}
#                         )
#                         st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.warning("증가율 분석을 위해서는 최소 7일 이상의 데이터가 필요합니다.")
#     else:
#         st.warning("증가율 분석을 위한 날짜 데이터가 없습니다.")

# with tab3:
#     # 감성 분석 탭
#     st.header("감성 분석")
    
#     if not filtered_df.empty:
#         # 실제 평점 데이터 처리 (★ -> 숫자)
#         rating_tab1, rating_tab2, rating_tab3 = st.tabs(["평점 분포", "키워드 분석", "감성 점수"])
        
#         with rating_tab1:
#             st.subheader("평점 분포")
            
#             # 실제 평점 데이터가 있다면 처리
#             if 'rating' in filtered_df.columns:
#                 # 별표 개수 세기
#                 def count_stars(rating_str):
#                     if pd.isna(rating_str):
#                         return np.nan
#                     return str(rating_str).count('★')
                
#                 filtered_df['rating_numeric'] = filtered_df['rating'].apply(count_stars)
#                 valid_ratings = filtered_df.dropna(subset=['rating_numeric'])
                
#                 if not valid_ratings.empty:
#                     rating_dist = valid_ratings['rating_numeric'].value_counts().sort_index()
                    
#                     fig = px.bar(
#                         x=rating_dist.index,
#                         y=rating_dist.values,
#                         title="평점 분포",
#                         labels={'x': '평점 (별 개수)', 'y': '리뷰 수'},
#                         text=rating_dist.values
#                     )
#                     fig.update_traces(textposition='outside')
#                     st.plotly_chart(fig, use_container_width=True)
                    
#                     # 평점 통계
#                     col1, col2, col3 = st.columns(3)
#                     col1.metric("평균 평점", f"{valid_ratings['rating_numeric'].mean():.2f}")
#                     col2.metric("최고 평점", f"{valid_ratings['rating_numeric'].max():.0f}")
#                     col3.metric("평점 표준편차", f"{valid_ratings['rating_numeric'].std():.2f}")
#                 else:
#                     st.warning("평점 데이터를 처리할 수 없습니다.")
#             else:
#                 st.info("평점 데이터가 없어 샘플 데이터를 표시합니다.")
#                 # 샘플 평점 분포
#                 sample_ratings = np.random.choice([1,2,3,4,5], size=1000, p=[0.05, 0.1, 0.15, 0.35, 0.35])
#                 rating_counts = pd.Series(sample_ratings).value_counts().sort_index()
                
#                 fig = px.bar(
#                     x=rating_counts.index,
#                     y=rating_counts.values,
#                     title="평점 분포 (샘플)",
#                     labels={'x': '평점', 'y': '리뷰 수'},
#                     text=rating_counts.values
#                 )
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
        
#         with rating_tab2:
#             st.subheader("키워드 분석")
#             st.info("키워드 분석은 향후 구현 예정입니다.")
            
#             # 샘플 키워드 데이터
#             sample_keywords = {
#                 '좋아요': 145, '만족': 132, '추천': 118, '예뻐요': 95, '발색': 87,
#                 '지속력': 76, '가격': 65, '품질': 54, '색상': 48, '텍스처': 42,
#                 '아쉬워요': 38, '부족': 25, '실망': 18, '별로': 12, '최악': 8
#             }
            
#             # 긍정/부정 키워드 분리
#             positive_words = {'좋아요': 145, '만족': 132, '추천': 118, '예뻐요': 95, '발색': 87, '지속력': 76}
#             negative_words = {'아쉬워요': 38, '부족': 25, '실망': 18, '별로': 12, '최악': 8}
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 st.write("**긍정 키워드 TOP 6**")
#                 pos_df = pd.DataFrame(list(positive_words.items()), columns=['키워드', '빈도'])
#                 fig = px.bar(pos_df, x='빈도', y='키워드', orientation='h', 
#                            title="긍정 키워드", color='빈도', color_continuous_scale='Greens')
#                 fig.update_layout(height=300, yaxis={'categoryorder':'total ascending'})
#                 st.plotly_chart(fig, use_container_width=True)
            
#             with col2:
#                 st.write("**부정 키워드 TOP 5**")
#                 neg_df = pd.DataFrame(list(negative_words.items()), columns=['키워드', '빈도'])
#                 fig = px.bar(neg_df, x='빈도', y='키워드', orientation='h',
#                            title="부정 키워드", color='빈도', color_continuous_scale='Reds')
#                 fig.update_layout(height=300, yaxis={'categoryorder':'total ascending'})
#                 st.plotly_chart(fig, use_container_width=True)
        
#         with rating_tab3:
#             st.subheader("감성 점수")
#             st.info("감성 점수 분석은 향후 구현 예정입니다.")
            
#             # 샘플 감성 점수 데이터
#             dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
#             sentiment_scores = np.random.normal(0.7, 0.2, len(dates))  # 평균 0.7의 긍정적 점수
            
#             sentiment_df = pd.DataFrame({
#                 '날짜': dates,
#                 '감성점수': sentiment_scores
#             })
            
#             fig = px.line(sentiment_df, x='날짜', y='감성점수', 
#                          title="시간별 감성 점수 변화 (샘플)",
#                          labels={'감성점수': '감성 점수 (-1: 부정, +1: 긍정)'})
#             fig.add_hline(y=0, line_dash="dash", line_color="gray")
#             st.plotly_chart(fig, use_container_width=True)
            
#             # 감성 통계
#             col1, col2, col3 = st.columns(3)
#             col1.metric("평균 감성점수", f"{sentiment_scores.mean():.3f}")
#             col2.metric("긍정 비율", f"{(sentiment_scores > 0).sum() / len(sentiment_scores) * 100:.1f}%")
#             col3.metric("감성 변동성", f"{sentiment_scores.std():.3f}")
#     else:
#         st.warning("분석할 데이터가 없습니다.")

# with tab4:
#     # 채널 비교 분석 탭 (실제 데이터 사용)
#     st.header("채널 비교 분석")
    
#     if not review_df.empty and 'channel' in review_df.columns:
#         channel_tab1, channel_tab2 = st.tabs(["채널별 기본 통계", "채널별 제품 분석"])
        
#         with channel_tab1:
#             st.subheader("채널별 성과 비교")
            
#             # 채널별 기본 통계
#             channel_stats = review_df.groupby('channel').agg({
#                 'product_name': 'count'  # 리뷰 수
#             }).reset_index()
#             channel_stats.columns = ['채널', '총_리뷰수']
            
#             # 채널별 제품 수
#             product_counts_by_channel = review_df.groupby('channel')['product_name'].nunique().reset_index()
#             product_counts_by_channel.columns = ['채널', '제품수']
            
#             # 합치기
#             channel_summary = pd.merge(channel_stats, product_counts_by_channel, on='채널')
#             channel_summary['제품당_평균리뷰'] = (channel_summary['총_리뷰수'] / channel_summary['제품수']).round(1)
            
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 fig = px.bar(channel_summary, x='채널', y='총_리뷰수', 
#                             title="채널별 총 리뷰 수", text='총_리뷰수',
#                             color='총_리뷰수', color_continuous_scale='viridis')
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
            
#             with col2:
#                 fig = px.bar(channel_summary, x='채널', y='제품수',
#                             title="채널별 제품 수", text='제품수',
#                             color='제품수', color_continuous_scale='plasma')
#                 fig.update_traces(textposition='outside')
#                 st.plotly_chart(fig, use_container_width=True)
            
#             # 제품당 평균 리뷰 수
#             st.subheader("제품당 평균 리뷰 수")
#             fig = px.bar(channel_summary, x='채널', y='제품당_평균리뷰',
#                         title="채널별 제품당 평균 리뷰 수", text='제품당_평균리뷰',
#                         color='제품당_평균리뷰', color_continuous_scale='blues')
#             fig.update_traces(textposition='outside')
#             st.plotly_chart(fig, use_container_width=True)
            
#             # 상세 통계 테이블
#             st.subheader("채널별 상세 통계")
#             st.dataframe(channel_summary, use_container_width=True)
        
#         with channel_tab2:
#             st.subheader("채널별 제품 분석")
            
#             # 각 채널의 상위 제품들
#             for channel in review_df['channel'].unique():
#                 st.write(f"**{channel.upper()} 채널 TOP 10 제품**")
#                 channel_data = review_df[review_df['channel'] == channel]
                
#                 if 'product_name' in channel_data.columns:
#                     top_products = channel_data['product_name'].value_counts().head(10)
                    
#                     if not top_products.empty:
#                         fig = px.bar(
#                             x=top_products.values,
#                             y=top_products.index,
#                             orientation='h',
#                             title=f"{channel} 채널 상위 제품",
#                             labels={'x': '리뷰 수', 'y': '제품명'},
#                             text=top_products.values
#                         )
#                         fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
#                         fig.update_traces(textposition='outside')
#                         st.plotly_chart(fig, use_container_width=True)
#                     else:
#                         st.write("제품 데이터가 없습니다.")
#                 else:
#                     st.write("제품명 데이터가 없습니다.")
                
#                 st.markdown("---")
            
#             # 채널 간 공통 제품 분석 (만약 있다면)
#             st.subheader("채널 간 제품 비교")
            
#             if 'product_name' in review_df.columns:
#                 # 각 채널의 제품 목록
#                 channel_products = {}
#                 for channel in review_df['channel'].unique():
#                     channel_data = review_df[review_df['channel'] == channel]
#                     channel_products[channel] = set(channel_data['product_name'].unique())
                
#                 # 공통 제품 찾기
#                 all_channels = list(channel_products.keys())
#                 if len(all_channels) >= 2:
#                     common_products = channel_products[all_channels[0]]
#                     for channel in all_channels[1:]:
#                         common_products = common_products.intersection(channel_products[channel])
                    
#                     if common_products:
#                         st.success(f"공통 제품 {len(common_products)}개 발견!")
#                         st.write("공통 제품:", list(common_products))
                        
#                         # 공통 제품의 채널별 리뷰 수 비교
#                         common_data = []
#                         for product in common_products:
#                             for channel in all_channels:
#                                 count = len(review_df[(review_df['channel'] == channel) & 
#                                                     (review_df['product_name'] == product)])
#                                 common_data.append({
#                                     '제품명': product,
#                                     '채널': channel,
#                                     '리뷰수': count
#                                 })
                        
#                         if common_data:
#                             common_df = pd.DataFrame(common_data)
#                             fig = px.bar(common_df, x='제품명', y='리뷰수', color='채널',
#                                         title="공통 제품의 채널별 리뷰 수 비교",
#                                         barmode='group')
#                             st.plotly_chart(fig, use_container_width=True)
#                     else:
#                         st.info("채널 간 공통 제품이 없습니다.")
#                 else:
#                     st.info("비교할 채널이 부족합니다.")
#     else:
#         st.warning("채널 정보가 없어 비교 분석을 할 수 없습니다.")

# # 디버그 정보
# with st.sidebar:
#     st.markdown("---")
#     st.subheader("데이터 정보")
#     st.write(f"전체 데이터: {len(review_df):,}개")
#     st.write(f"최종 필터링 후: {len(filtered_df):,}개")
    
#     if 'channel' in review_df.columns:
#         st.write("**채널별 분포:**")
#         for channel, count in review_df['channel'].value_counts().items():
#             st.write(f"- {channel}: {count:,}개")
    
#     # 컬럼 정보 표시
#     st.write("**데이터 컬럼:**")
#     for col in review_df.columns:
#         st.write(f"- {col}")