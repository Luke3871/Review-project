# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import r2_score
# from sklearn.preprocessing import StandardScaler
# from scipy import stats
# import glob
# import os
# import re
# from datetime import datetime, timedelta

# # SHAP import with error handling
# try:
#     import shap
#     SHAP_AVAILABLE = True
# except ImportError:
#     SHAP_AVAILABLE = False

# def load_daiso_data():
#     """다이소 데이터 로딩 - 스킨케어, 메이크업 카테고리의 SALES 정렬 + 최근 6개월만"""
#     daiso_dir = "../data/data_daiso/raw_data/reviews_daiso"
#     csv_files = glob.glob(os.path.join(daiso_dir, "*_reviews.csv"))
    
#     all_reviews = []
#     for file in csv_files:
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
    
#     if all_reviews:
#         df = pd.concat(all_reviews, ignore_index=True)
#         if 'review_date' in df.columns:
#             df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')
        
#         # 필터링: 스킨케어, 메이크업 카테고리 + SALES 정렬
#         filtered_df = df[
#             (df['category'].isin(['skincare', 'makeup'])) & 
#             (df['sort_type'] == 'SALES')
#         ]
        
#         # 최근 6개월 필터링
#         if 'review_date' in filtered_df.columns:
#             six_months_ago = datetime.now() - timedelta(days=180)
#             recent_df = filtered_df[filtered_df['review_date'] >= six_months_ago]
#             return recent_df
        
#         return filtered_df
#     return pd.DataFrame()

# def extract_rating_numeric(rating_str):
#     """평점을 숫자로 변환"""
#     if pd.isna(rating_str):
#         return np.nan
    
#     rating_str = str(rating_str)
    
#     if '점' in rating_str:
#         try:
#             return float(rating_str.replace('점', ''))
#         except:
#             return np.nan
#     elif '★' in rating_str:
#         return float(rating_str.count('★'))
    
#     try:
#         return float(rating_str)
#     except:
#         return np.nan

# def calculate_sentiment_score(rating):
#     """평점 기반 감정 점수 계산 (1-5 -> 0-1)"""
#     if pd.isna(rating):
#         return np.nan
#     return (rating - 1) / 4

# def extract_basic_features(df):
#     """기본 피쳐 추출 (제품별)"""
#     if df.empty:
#         return pd.DataFrame()
    
#     # 평점 숫자 변환
#     df['rating_numeric'] = df['rating'].apply(extract_rating_numeric)
#     df['sentiment_score'] = df['rating_numeric'].apply(calculate_sentiment_score)
    
#     basic_features = []
    
#     for product in df['product_name'].unique():
#         product_data = df[df['product_name'] == product].copy()
        
#         # 제품 기본 정보
#         first_row = product_data.iloc[0]
#         rank = first_row.get('rank', np.nan)
        
#         # rank를 숫자로 변환
#         if pd.notna(rank):
#             try:
#                 rank_num = float(str(rank).replace('위', ''))
#                 log_inverse_rank = -np.log(rank_num) if rank_num > 0 else np.nan
#             except:
#                 rank_num = np.nan
#                 log_inverse_rank = np.nan
#         else:
#             rank_num = np.nan
#             log_inverse_rank = np.nan
        
#         # 리뷰 텍스트 길이 계산
#         product_data['review_length'] = product_data['review_text'].fillna('').str.len()
        
#         # 기본 통계
#         valid_ratings = product_data.dropna(subset=['rating_numeric'])
        
#         # 데이터 기간 계산
#         if 'review_date' in product_data.columns and not product_data['review_date'].isna().all():
#             first_date = product_data['review_date'].min()
#             last_date = product_data['review_date'].max()
#             data_period_days = (last_date - first_date).days
#         else:
#             data_period_days = np.nan
        
#         feature_row = {
#             '제품명': product,
#             '카테고리': first_row.get('category', 'unknown'),
#             '가격': first_row.get('product_price', 'unknown'),
#             '순위': rank_num,
#             '순위_로그역수': log_inverse_rank,
            
#             # 리뷰 수 관련
#             '총_리뷰수': len(product_data),
#             '평점있는_리뷰수': len(valid_ratings),
#             '텍스트있는_리뷰수': len(product_data[product_data['review_text'].fillna('').str.len() > 0]),
            
#             # 평점 관련
#             '평균_평점': valid_ratings['rating_numeric'].mean() if len(valid_ratings) > 0 else np.nan,
#             '평점_표준편차': valid_ratings['rating_numeric'].std() if len(valid_ratings) > 0 else np.nan,
            
#             # 감정 점수 관련
#             '평균_감정점수': product_data['sentiment_score'].mean(),
#             '감정점수_표준편차': product_data['sentiment_score'].std(),
            
#             # 평점 분포
#             '5점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 5]),
#             '4점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 4]),
#             '3점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 3]),
#             '2점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 2]),
#             '1점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 1]),
            
#             # 리뷰 텍스트 관련
#             '평균_리뷰길이': product_data['review_length'].mean(),
#             '긴_리뷰수': len(product_data[product_data['review_length'] > 100]),
            
#             # 시간 관련
#             '데이터_기간일수': data_period_days,
#             '일평균_리뷰수': len(product_data) / max(data_period_days, 1) if pd.notna(data_period_days) else np.nan,
#         }
        
#         # 비율 계산
#         if feature_row['총_리뷰수'] > 0:
#             feature_row['긍정_비율'] = (feature_row['5점_개수'] + feature_row['4점_개수']) / feature_row['총_리뷰수']
#             feature_row['부정_비율'] = (feature_row['1점_개수'] + feature_row['2점_개수']) / feature_row['총_리뷰수']
#             feature_row['중립_비율'] = feature_row['3점_개수'] / feature_row['총_리뷰수']
#             feature_row['긴리뷰_비율'] = feature_row['긴_리뷰수'] / feature_row['총_리뷰수']
#         else:
#             feature_row['긍정_비율'] = 0
#             feature_row['부정_비율'] = 0
#             feature_row['중립_비율'] = 0
#             feature_row['긴리뷰_비율'] = 0
        
#         basic_features.append(feature_row)
    
#     return pd.DataFrame(basic_features)

# def extract_weekly_features(df):
#     """주별 피쳐 추출"""
#     if df.empty or 'review_date' not in df.columns:
#         return pd.DataFrame()
    
#     # 평점 숫자 변환
#     df['rating_numeric'] = df['rating'].apply(extract_rating_numeric)
#     df['sentiment_score'] = df['rating_numeric'].apply(calculate_sentiment_score)
    
#     # 주별 그룹화 (ISO 주 기준)
#     df['year_week'] = df['review_date'].dt.to_period('W')
    
#     weekly_features = []
    
#     for product in df['product_name'].unique():
#         product_data = df[df['product_name'] == product].copy()
        
#         # 제품 기본 정보
#         first_row = product_data.iloc[0]
#         rank = first_row.get('rank', np.nan)
        
#         # rank를 숫자로 변환
#         if pd.notna(rank):
#             try:
#                 rank_num = float(str(rank).replace('위', ''))
#                 log_inverse_rank = -np.log(rank_num) if rank_num > 0 else np.nan
#             except:
#                 log_inverse_rank = np.nan
#         else:
#             log_inverse_rank = np.nan
        
#         # 주별 집계
#         weekly_group = product_data.groupby('year_week').agg({
#             'rating_numeric': ['count', 'mean', 'std'],
#             'sentiment_score': ['mean', 'std'],
#             'review_text': lambda x: x.str.len().mean()
#         }).round(4)
        
#         weekly_group.columns = ['리뷰수', '평균_평점', '평점_표준편차', 
#                                '평균_감정점수', '감정점수_표준편차', '평균_리뷰길이']
        
#         for period, row in weekly_group.iterrows():
#             feature_row = {
#                 '제품명': product,
#                 '연도_주차': str(period),
#                 '주_시작일': period.start_time,
#                 '리뷰수': row['리뷰수'],
#                 '평균_평점': row['평균_평점'],
#                 '평점_표준편차': row['평점_표준편차'] if pd.notna(row['평점_표준편차']) else 0,
#                 '평균_감정점수': row['평균_감정점수'],
#                 '감정점수_표준편차': row['감정점수_표준편차'] if pd.notna(row['감정점수_표준편차']) else 0,
#                 '평균_리뷰길이': row['평균_리뷰길이'],
#                 '순위': rank_num if 'rank_num' in locals() else np.nan,
#                 '순위_로그역수': log_inverse_rank,
#                 '카테고리': first_row.get('category', 'unknown')
#             }
#             weekly_features.append(feature_row)
    
#     return pd.DataFrame(weekly_features)

# def calculate_weekly_derived_features(weekly_df):
#     """주별 파생변수 계산"""
#     if weekly_df.empty:
#         return weekly_df
    
#     # 날짜 정렬
#     weekly_df = weekly_df.sort_values(['제품명', '주_시작일']).reset_index(drop=True)
    
#     derived_features = []
    
#     for product in weekly_df['제품명'].unique():
#         product_data = weekly_df[weekly_df['제품명'] == product].copy()
        
#         if len(product_data) < 2:
#             continue
            
#         # 변화율 계산
#         product_data['리뷰수_변화율'] = product_data['리뷰수'].pct_change()
#         product_data['감정점수_변화'] = product_data['평균_감정점수'].diff()
#         product_data['평점_변화'] = product_data['평균_평점'].diff()
        
#         # momentum 계산 (리뷰 수 가속도)
#         product_data['리뷰수_모멘텀'] = product_data['리뷰수_변화율'].diff()
        
#         # 4주 이동평균
#         product_data['리뷰수_4주평균'] = product_data['리뷰수'].rolling(window=4, min_periods=1).mean()
#         product_data['감정점수_4주평균'] = product_data['평균_감정점수'].rolling(window=4, min_periods=1).mean()
        
#         # 트렌드 지표 (최근 4주 vs 이전 4주)
#         if len(product_data) >= 8:
#             recent_4weeks = product_data.tail(4)['리뷰수'].mean()
#             previous_4weeks = product_data.iloc[-8:-4]['리뷰수'].mean()
#             trend_ratio = recent_4weeks / previous_4weeks if previous_4weeks > 0 else np.nan
#             product_data['트렌드_비율'] = trend_ratio
#         else:
#             product_data['트렌드_비율'] = np.nan
        
#         derived_features.append(product_data)
    
#     if derived_features:
#         return pd.concat(derived_features, ignore_index=True)
#     return weekly_df

# def perform_statistical_regression(feature_df):
#     """통계적 유의성을 포함한 회귀분석"""
#     if feature_df.empty:
#         return None, None, None
    
#     # target과 features 준비 (영어 컬럼명으로 매핑)
#     feature_mapping = {
#         '리뷰수': 'review_count',
#         '평균_평점': 'avg_rating', 
#         '평균_감정점수': 'sentiment_mean',
#         '평균_리뷰길이': 'avg_review_length',
#         '평점_표준편차': 'rating_std',
#         '감정점수_표준편차': 'sentiment_std',
#         '리뷰수_변화율': 'review_count_change',
#         '감정점수_변화': 'sentiment_change',
#         '리뷰수_모멘텀': 'review_momentum',
#         '리뷰수_4주평균': 'review_count_ma4',
#         '감정점수_4주평균': 'sentiment_ma4'
#     }
    
#     # 한글 컬럼을 영어로 변환
#     regression_data = feature_df.copy()
#     for korean, english in feature_mapping.items():
#         if korean in regression_data.columns:
#             regression_data[english] = regression_data[korean]
    
#     # target 설정
#     regression_data = regression_data.dropna(subset=['순위_로그역수']).copy()
    
#     if len(regression_data) < 10:
#         return None, None, "데이터가 부족합니다"
    
#     # feature 선택 (영어명 사용)
#     feature_columns = ['review_count', 'avg_rating', 'sentiment_mean', 'avg_review_length', 'rating_std', 'sentiment_std']
    
#     # 파생변수가 있으면 추가
#     if 'review_count_change' in regression_data.columns:
#         feature_columns.extend(['review_count_change', 'sentiment_change', 'review_momentum'])
    
#     if 'review_count_ma4' in regression_data.columns:
#         feature_columns.extend(['review_count_ma4', 'sentiment_ma4'])
    
#     # 결측치 제거
#     regression_data = regression_data.dropna(subset=feature_columns + ['순위_로그역수'])
    
#     if len(regression_data) < 5:
#         return None, None, "회귀분석 데이터 부족"
    
#     X = regression_data[feature_columns]
#     y = regression_data['순위_로그역수']
    
#     # 표준화
#     scaler = StandardScaler()
#     X_scaled = scaler.fit_transform(X)
    
#     # sklearn 회귀분석
#     model = LinearRegression()
#     model.fit(X_scaled, y)
    
#     # 예측 및 평가
#     y_pred = model.predict(X_scaled)
#     r2 = r2_score(y, y_pred)
    
#     # 통계적 유의성 계산
#     n = len(X_scaled)
#     p = len(feature_columns)
    
#     # 잔차 계산
#     residuals = y - y_pred
#     mse = np.mean(residuals ** 2)
    
#     # 표준오차 계산
#     X_with_const = np.column_stack([np.ones(n), X_scaled])
    
#     try:
#         # 공분산 행렬
#         cov_matrix = mse * np.linalg.inv(X_with_const.T @ X_with_const)
#         se_coef = np.sqrt(np.diag(cov_matrix)[1:])  # 절편 제외
        
#         # t-통계량과 p-value
#         t_stats = model.coef_ / se_coef
#         p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
        
#     except:
#         se_coef = np.full(len(feature_columns), np.nan)
#         t_stats = np.full(len(feature_columns), np.nan)
#         p_values = np.full(len(feature_columns), np.nan)
    
#     # 한글명으로 변환
#     korean_names = []
#     for eng_name in feature_columns:
#         korean_name = None
#         for kor, eng in feature_mapping.items():
#             if eng == eng_name:
#                 korean_name = kor
#                 break
#         korean_names.append(korean_name if korean_name else eng_name)
    
#     # 결과 정리
#     coefficients = pd.DataFrame({
#         '피쳐': korean_names,
#         '회귀계수': model.coef_,
#         '표준오차': se_coef,
#         't통계량': t_stats,
#         'p값': p_values,
#         '유의성': ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '' for p in p_values],
#         '절댓값': np.abs(model.coef_)
#     }).sort_values('절댓값', ascending=False)
    
#     regression_results = {
#         'model': model,
#         'scaler': scaler,
#         'r2_score': r2,
#         'coefficients': coefficients,
#         'n_samples': len(regression_data),
#         'intercept': model.intercept_
#     }
    
#     # SHAP 분석
#     if SHAP_AVAILABLE:
#         try:
#             explainer = shap.LinearExplainer(model, X_scaled)
#             shap_values = explainer.shap_values(X_scaled)
            
#             shap_results = {
#                 'explainer': explainer,
#                 'shap_values': shap_values,
#                 'feature_names': korean_names,
#                 'X_scaled': X_scaled
#             }
#         except Exception as e:
#             shap_results = None
#     else:
#         shap_results = None
    
#     return regression_results, shap_results, None

# def render_demand_forecast_features():
#     """수요예측 피쳐 추출 메인 함수"""
#     st.header("수요예측 피쳐 추출")
#     st.caption("스킨케어 • 메이크업 카테고리 • SALES 정렬 • 최근 6개월 데이터")
    
#     # 데이터 로딩
#     daiso_df = load_daiso_data()
    
#     if daiso_df.empty:
#         st.error("필터링된 다이소 데이터가 없습니다.")
#         return
    
#     # 필터링 결과 표시
#     skincare_count = len(daiso_df[daiso_df['category'] == 'skincare'])
#     makeup_count = len(daiso_df[daiso_df['category'] == 'makeup'])
    
#     # 데이터 기간 표시
#     if 'review_date' in daiso_df.columns and not daiso_df['review_date'].isna().all():
#         date_min = daiso_df['review_date'].min().strftime('%Y-%m-%d')
#         date_max = daiso_df['review_date'].max().strftime('%Y-%m-%d')
#         st.info(f"데이터 기간: {date_min} ~ {date_max} | 스킨케어 {skincare_count}개, 메이크업 {makeup_count}개 리뷰")
#     else:
#         st.info(f"스킨케어 {skincare_count}개, 메이크업 {makeup_count}개 리뷰")
    
#     # 기본 피쳐 추출
#     basic_features = extract_basic_features(daiso_df)
    
#     # 주별 피쳐 추출
#     weekly_features = extract_weekly_features(daiso_df)
#     if not weekly_features.empty:
#         derived_features = calculate_weekly_derived_features(weekly_features)
#     else:
#         derived_features = pd.DataFrame()
    
#     # 기본 메트릭
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("총 제품 수", len(basic_features))
#     with col2:
#         st.metric("총 리뷰 수", basic_features['총_리뷰수'].sum())
#     with col3:
#         st.metric("평균 평점", f"{basic_features['평균_평점'].mean():.2f}")
#     with col4:
#         if not weekly_features.empty:
#             st.metric("주별 관측치", len(weekly_features))
#         else:
#             st.metric("주별 관측치", "0")
    
#     # 탭 구성
#     if SHAP_AVAILABLE:
#         tab1, tab2, tab3, tab4, tab5 = st.tabs(["제품별 기본 피쳐", "주별 피쳐", "주별 파생변수", "회귀분석", "SHAP 분석"])
#     else:
#         tab1, tab2, tab3, tab4 = st.tabs(["제품별 기본 피쳐", "주별 피쳐", "주별 파생변수", "회귀분석"])
    
#     with tab1:
#         if not basic_features.empty:
#             # 카테고리별 필터
#             category_filter = st.selectbox(
#                 "카테고리 필터",
#                 options=['전체', 'skincare', 'makeup']
#             )
            
#             display_df = basic_features.copy()
#             if category_filter != '전체':
#                 display_df = display_df[display_df['카테고리'] == category_filter]
            
#             # 표시할 컬럼 선택
#             display_columns = [
#                 '제품명', '카테고리', '순위', '총_리뷰수', '평균_평점', 
#                 '긍정_비율', '부정_비율', '평균_리뷰길이', 
#                 '일평균_리뷰수', '데이터_기간일수', '순위_로그역수'
#             ]
            
#             available_columns = [col for col in display_columns if col in display_df.columns]
            
#             st.dataframe(
#                 display_df[available_columns].round(4),
#                 use_container_width=True
#             )
            
#             # CSV 다운로드
#             csv_basic = basic_features.to_csv(index=False, encoding='utf-8-sig')
#             st.download_button(
#                 label="제품별 기본 피쳐 CSV 다운로드",
#                 data=csv_basic,
#                 file_name=f"daiso_beauty_basic_features_{datetime.now().strftime('%Y%m%d')}.csv",
#                 mime="text/csv"
#             )
#         else:
#             st.warning("기본 피쳐를 추출할 수 없습니다.")
    
#     with tab2:
#         if not weekly_features.empty:
#             # 제품 필터
#             selected_products_weekly = st.multiselect(
#                 "제품 선택 (주별)",
#                 options=sorted(weekly_features['제품명'].unique()),
#                 default=[],
#                 key="weekly_products"
#             )
            
#             display_df_weekly = weekly_features.copy()
#             if selected_products_weekly:
#                 display_df_weekly = display_df_weekly[display_df_weekly['제품명'].isin(selected_products_weekly)]
            
#             st.dataframe(
#                 display_df_weekly[['제품명', '카테고리', '연도_주차', '리뷰수', '평균_평점', 
#                                   '평균_감정점수', '평균_리뷰길이', '순위_로그역수']].round(4),
#                 use_container_width=True
#             )
            
#             # 주별 트렌드 차트
#             if selected_products_weekly:
#                 for product in selected_products_weekly[:3]:  # 최대 3개 제품만 표시
#                     product_data = display_df_weekly[display_df_weekly['제품명'] == product]
                    
#                     fig = px.line(
#                         product_data, 
#                         x='주_시작일', 
#                         y='리뷰수',
#                         title=f"{product} - 주별 리뷰 수 트렌드",
#                         markers=True
#                     )
#                     st.plotly_chart(fig, use_container_width=True)
            
#             # CSV 다운로드
#             csv_weekly = weekly_features.to_csv(index=False, encoding='utf-8-sig')
#             st.download_button(
#                 label="주별 피쳐 CSV 다운로드",
#                 data=csv_weekly,
#                 file_name=f"daiso_beauty_weekly_features_{datetime.now().strftime('%Y%m%d')}.csv",
#                 mime="text/csv"
#             )
#         else:
#             st.warning("주별 피쳐를 추출할 수 없습니다.")
    
#     with tab3:
#         if not derived_features.empty:
#             # 파생변수 테이블
#             derived_columns = ['제품명', '카테고리', '연도_주차', '리뷰수', 
#                              '리뷰수_변화율', '감정점수_변화', '리뷰수_모멘텀',
#                              '리뷰수_4주평균', '감정점수_4주평균', '트렌드_비율']
            
#             available_columns = [col for col in derived_columns if col in derived_features.columns]
            
#             if available_columns:
#                 st.dataframe(
#                     derived_features[available_columns].round(4),
#                     use_container_width=True
#                 )
            
#             # CSV 다운로드
#             csv_derived = derived_features.to_csv(index=False, encoding='utf-8-sig')
#             st.download_button(
#                 label="주별 파생변수 CSV 다운로드",
#                 data=csv_derived,
#                 file_name=f"daiso_beauty_weekly_derived_features_{datetime.now().strftime('%Y%m%d')}.csv",
#                 mime="text/csv"
#             )
#         else:
#             st.warning("주별 파생변수를 계산할 수 없습니다.")
    
#     with tab4:
#         if not derived_features.empty:
#             with st.spinner("통계적 회귀분석 수행 중..."):
#                 regression_results, shap_results, error_msg = perform_statistical_regression(derived_features)
            
#             if regression_results:
#                 col1, col2, col3 = st.columns(3)
                
#                 with col1:
#                     st.metric("R² Score", f"{regression_results['r2_score']:.4f}")
#                 with col2:
#                     st.metric("샘플 수", f"{regression_results['n_samples']:,}")
#                 with col3:
#                     st.metric("절편", f"{regression_results['intercept']:.4f}")
                
#                 st.markdown("### 통계적 유의성 검정 결과")
#                 st.caption("*** p<0.001, ** p<0.01, * p<0.05")
                
#                 # 회귀계수 테이블
#                 st.dataframe(
#                     regression_results['coefficients'][['피쳐', '회귀계수', '표준오차', 't통계량', 'p값', '유의성']].round(6),
#                     use_container_width=True
#                 )
                
#                 # 유의한 피쳐만 차트
#                 significant_features = regression_results['coefficients'][regression_results['coefficients']['p값'] < 0.05]
                
#                 if not significant_features.empty:
#                     fig = px.bar(
#                         significant_features,
#                         x='절댓값',
#                         y='피쳐',
#                         orientation='h',
#                         title="통계적으로 유의한 피쳐 (p < 0.05)",
#                         text='회귀계수',
#                         color='p값',
#                         color_continuous_scale='RdYlBu_r'
#                     )
#                     fig.update_traces(texttemplate='%{text:.4f}', textposition='outside')
#                     fig.update_layout(yaxis={'categoryorder':'total ascending'})
#                     st.plotly_chart(fig, use_container_width=True)
#                 else:
#                     st.warning("통계적으로 유의한 피쳐가 없습니다 (p < 0.05)")
                
#             else:
#                 st.error(f"회귀분석 실패: {error_msg}")
#         else:
#             st.warning("회귀분석 데이터가 없습니다.")
    
#     # SHAP 탭 (SHAP가 설치된 경우에만)
#     if SHAP_AVAILABLE:
#         with tab5:
#             if not derived_features.empty:
#                 with st.spinner("SHAP 분석 수행 중..."):
#                     regression_results, shap_results, error_msg = perform_statistical_regression(derived_features)
                
#                 if shap_results:
#                     st.markdown("### SHAP 피쳐 중요도")
#                     st.caption("각 피쳐가 예측에 미치는 실제 기여도")
                    
#                     try:
#                         # SHAP 요약 플롯
#                         fig_shap = go.Figure()
                        
#                         # SHAP 값의 평균 절댓값으로 피쳐 중요도 계산
#                         feature_importance = np.abs(shap_results['shap_values']).mean(axis=0)
                        
#                         # 중요도 순으로 정렬
#                         sorted_indices = np.argsort(feature_importance)[::-1]
#                         sorted_features = [shap_results['feature_names'][i] for i in sorted_indices]
#                         sorted_importance = feature_importance[sorted_indices]
                        
#                         fig_shap.add_trace(go.Bar(
#                             x=sorted_importance,
#                             y=sorted_features,
#                             orientation='h',
#                             text=[f'{val:.4f}' for val in sorted_importance],
#                             textposition='outside'
#                         ))
                        
#                         fig_shap.update_layout(
#                             title="SHAP 피쳐 중요도",
#                             xaxis_title="평균 SHAP 값 (절댓값)",
#                             yaxis_title="피쳐",
#                             yaxis={'categoryorder':'total ascending'}
#                         )
                        
#                         st.plotly_chart(fig_shap, use_container_width=True)
                        
#                         # SHAP 값 요약 테이블
#                         shap_summary = pd.DataFrame({
#                             '피쳐': sorted_features,
#                             'SHAP_중요도': sorted_importance,
#                             '순위': range(1, len(sorted_features) + 1)
#                         })
                        
#                         st.markdown("### SHAP 피쳐 중요도 순위")
#                         st.dataframe(shap_summary.round(6), use_container_width=True)
                        
#                         # 해석
#                         st.markdown("### SHAP 분석 해석")
#                         top_feature = sorted_features[0]
#                         st.markdown(f"""
#                         **SHAP 분석 결과:**
#                         - 가장 영향력 있는 피쳐: **{top_feature}**
#                         - SHAP 값이 클수록 해당 피쳐가 예측에 더 큰 영향을 미침
#                         - 회귀계수와 다르게 실제 기여도를 측정 (상호작용 효과 포함)
#                         """)
                        
#                     except Exception as e:
#                         st.error(f"SHAP 시각화 오류: {e}")
                        
#                 elif regression_results:
#                     st.warning("SHAP 분석을 수행할 수 없습니다.")
#                 else:
#                     st.warning("회귀분석이 선행되어야 SHAP 분석이 가능합니다.")
#             else:
#                 st.warning("SHAP 분석을 위한 데이터가 없습니다.")
#     elif not SHAP_AVAILABLE:
#         st.info("SHAP 라이브러리가 설치되지 않아 SHAP 분석을 사용할 수 없습니다. `pip install shap`로 설치하세요.")

# if __name__ == "__main__":
#     render_demand_forecast_features()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from scipy import stats
import glob
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# SHAP import with error handling
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

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
        
        # 필터링: 스킨케어, 메이크업 카테고리 + SALES 정렬
        filtered_df = df[
            (df['category'].isin(['skincare', 'makeup'])) & 
            (df['sort_type'] == 'SALES')
        ]
        
        # 최근 6개월 필터링
        if 'review_date' in filtered_df.columns:
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_df = filtered_df[filtered_df['review_date'] >= six_months_ago]
            return recent_df
        
        return filtered_df
    return pd.DataFrame()

def extract_rating_numeric(rating_str):
    """평점을 숫자로 변환"""
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

def calculate_sentiment_score(rating):
    """평점 기반 감정 점수 계산 (1-5 -> 0-1)"""
    if pd.isna(rating):
        return np.nan
    return (rating - 1) / 4

def extract_product_features(df):
    """제품별 피쳐 추출"""
    if df.empty:
        return pd.DataFrame()
    
    # 평점 숫자 변환
    df['rating_numeric'] = df['rating'].apply(extract_rating_numeric)
    df['sentiment_score'] = df['rating_numeric'].apply(calculate_sentiment_score)
    
    product_features = []
    
    for product in df['product_name'].unique():
        product_data = df[df['product_name'] == product].copy()
        
        # 제품 기본 정보
        first_row = product_data.iloc[0]
        rank = first_row.get('rank', np.nan)
        
        # rank를 숫자로 변환
        if pd.notna(rank):
            try:
                rank_num = float(str(rank).replace('위', ''))
            except:
                rank_num = np.nan
        else:
            rank_num = np.nan
        
        # 리뷰 텍스트 길이 계산
        product_data['review_length'] = product_data['review_text'].fillna('').str.len()
        
        # 기본 통계
        valid_ratings = product_data.dropna(subset=['rating_numeric'])
        
        feature_row = {
            '제품명': product,
            '카테고리': first_row.get('category', 'unknown'),
            '순위': rank_num,
            
            # 기본 지표
            '총_리뷰수': len(product_data),
            '평균_평점': valid_ratings['rating_numeric'].mean() if len(valid_ratings) > 0 else np.nan,
            '평균_감정점수': product_data['sentiment_score'].mean(),
            '평균_리뷰길이': product_data['review_length'].mean(),
            
            # 평점 분포
            '5점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 5]),
            '4점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 4]),
            '3점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 3]),
            '2점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 2]),
            '1점_개수': len(valid_ratings[valid_ratings['rating_numeric'] == 1]),
            
            # 텍스트 분석
            '긴_리뷰수': len(product_data[product_data['review_length'] > 100]),
        }
        
        # 비율 계산
        if feature_row['총_리뷰수'] > 0:
            feature_row['긍정_비율'] = (feature_row['5점_개수'] + feature_row['4점_개수']) / feature_row['총_리뷰수']
            feature_row['부정_비율'] = (feature_row['1점_개수'] + feature_row['2점_개수']) / feature_row['총_리뷰수']
            feature_row['긴리뷰_비율'] = feature_row['긴_리뷰수'] / feature_row['총_리뷰수']
        else:
            feature_row['긍정_비율'] = 0
            feature_row['부정_비율'] = 0
            feature_row['긴리뷰_비율'] = 0
        
        product_features.append(feature_row)
    
    return pd.DataFrame(product_features)

def generate_sample_weekly_sales_data(product_features):
    """샘플 주별 판매량 데이터 생성"""
    if product_features.empty:
        return pd.DataFrame()
    
    # 주별 데이터 생성 (최근 12주)
    weeks = pd.date_range(start='2024-10-01', periods=12, freq='W')
    sample_data = []
    
    for product in product_features['제품명'].unique()[:15]:  # 상위 15개 제품만
        product_info = product_features[product_features['제품명'] == product].iloc[0]
        
        # 제품 특성에 따른 기본 판매량 설정
        base_sales = max(10, int(product_info['총_리뷰수'] * 0.3))
        rating_factor = product_info['평균_평점'] / 5.0 if pd.notna(product_info['평균_평점']) else 0.7
        
        for week in weeks:
            # 실제 리뷰 특성이 판매량에 영향을 미치도록 설정
            sales_base = base_sales * rating_factor
            
            # 노이즈 추가
            noise = np.random.normal(0, sales_base * 0.3)
            weekly_sales = max(1, int(sales_base + noise))
            
            # 주별 리뷰 특성 (약간의 변동 추가)
            weekly_reviews = max(1, int(product_info['총_리뷰수'] / 12 + np.random.normal(0, 2)))
            weekly_rating = min(5, max(1, product_info['평균_평점'] + np.random.normal(0, 0.3)))
            weekly_sentiment = min(1, max(0, product_info['평균_감정점수'] + np.random.normal(0, 0.1)))
            weekly_positive_ratio = min(1, max(0, product_info['긍정_비율'] + np.random.normal(0, 0.1)))
            weekly_review_length = max(10, product_info['평균_리뷰길이'] + np.random.normal(0, 20))
            
            sample_data.append({
                '제품명': product,
                '카테고리': product_info['카테고리'],
                '주차': week,
                '판매량': weekly_sales,
                '리뷰수': weekly_reviews,
                '평균평점': weekly_rating,
                '감정점수': weekly_sentiment,
                '긍정비율': weekly_positive_ratio,
                '리뷰길이': weekly_review_length,
                '긴리뷰비율': min(1, max(0, product_info['긴리뷰_비율'] + np.random.normal(0, 0.1)))
            })
    
    return pd.DataFrame(sample_data)

def perform_sales_prediction_analysis(sales_data, category_filter):
    """판매량 예측 분석 (SHAP 포함)"""
    if sales_data.empty:
        return None, None, "데이터가 없습니다"
    
    # 카테고리 필터링
    if category_filter != '전체':
        analysis_data = sales_data[sales_data['카테고리'] == category_filter].copy()
    else:
        analysis_data = sales_data.copy()
    
    if len(analysis_data) < 10:
        return None, None, "분석을 위한 데이터가 부족합니다"
    
    # 피쳐 선택
    feature_columns = ['리뷰수', '평균평점', '감정점수', '긍정비율', '리뷰길이', '긴리뷰비율']
    
    # 로그 변환
    analysis_data['로그_리뷰수'] = np.log1p(analysis_data['리뷰수'])
    analysis_data['로그_리뷰길이'] = np.log1p(analysis_data['리뷰길이'])
    
    # 변환된 피쳐 사용
    transformed_features = ['로그_리뷰수', '평균평점', '감정점수', '긍정비율', '로그_리뷰길이', '긴리뷰비율']
    
    # 결측치 제거
    clean_data = analysis_data.dropna(subset=transformed_features + ['판매량'])
    
    if len(clean_data) < 5:
        return None, None, "결측치 제거 후 데이터가 부족합니다"
    
    X = clean_data[transformed_features]
    y = clean_data['판매량']
    
    # 표준화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 회귀분석
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    y_pred = model.predict(X_scaled)
    r2 = r2_score(y, y_pred)
    
    # 통계적 유의성 계산
    n = len(X_scaled)
    p = len(transformed_features)
    
    residuals = y - y_pred
    mse = np.mean(residuals ** 2)
    
    X_with_const = np.column_stack([np.ones(n), X_scaled])
    
    try:
        cov_matrix = mse * np.linalg.inv(X_with_const.T @ X_with_const)
        se_coef = np.sqrt(np.diag(cov_matrix)[1:])
        
        t_stats = model.coef_ / se_coef
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
        
    except:
        se_coef = np.full(len(transformed_features), np.nan)
        t_stats = np.full(len(transformed_features), np.nan)
        p_values = np.full(len(transformed_features), np.nan)
    
    # 결과 정리
    regression_results = {
        'model': model,
        'scaler': scaler,
        'r2_score': r2,
        'n_samples': len(clean_data),
        'feature_names': transformed_features,
        'coefficients': model.coef_,
        'p_values': p_values,
        'clean_data': clean_data
    }
    
    # SHAP 분석
    shap_results = None
    if SHAP_AVAILABLE:
        try:
            explainer = shap.LinearExplainer(model, X_scaled)
            shap_values = explainer.shap_values(X_scaled)
            
            shap_results = {
                'explainer': explainer,
                'shap_values': shap_values,
                'feature_names': transformed_features,
                'X_scaled': X_scaled,
                'expected_value': explainer.expected_value
            }
        except Exception as e:
            pass
    
    return regression_results, shap_results, None

def perform_rank_correlation_analysis(features_df):
    """순위 상관관계 분석"""
    if features_df.empty:
        return None, "데이터가 없습니다"
    
    # 순위가 있는 데이터만 사용
    analysis_data = features_df.dropna(subset=['순위']).copy()
    
    if len(analysis_data) < 10:
        return None, "분석을 위한 데이터가 부족합니다"
    
    # 분석할 피쳐 선택
    feature_columns = ['총_리뷰수', '평균_평점', '평균_감정점수', '긍정_비율', 
                      '부정_비율', '평균_리뷰길이', '긴리뷰_비율']
    
    # 사용 가능한 피쳐만 선택
    available_features = [col for col in feature_columns if col in analysis_data.columns]
    
    # 결측치 제거
    clean_data = analysis_data.dropna(subset=available_features + ['순위']).copy()
    
    if len(clean_data) < 5:
        return None, "결측치 제거 후 데이터가 부족합니다"
    
    # 로그 변환 (큰 값들)
    clean_data['로그_총리뷰수'] = np.log1p(clean_data['총_리뷰수'])
    clean_data['로그_평균리뷰길이'] = np.log1p(clean_data['평균_리뷰길이'])
    
    # 순위를 역순으로 (1위가 가장 좋은 것)
    clean_data['순위_역순'] = clean_data['순위'].max() - clean_data['순위'] + 1
    
    # 상관관계 계산
    correlation_features = ['로그_총리뷰수', '평균_평점', '평균_감정점수', '긍정_비율', 
                           '부정_비율', '로그_평균리뷰길이', '긴리뷰_비율']
    
    correlations = []
    
    for feature in correlation_features:
        if feature in clean_data.columns:
            # 피어슨 상관관계
            corr_coef, p_value = stats.pearsonr(clean_data[feature], clean_data['순위_역순'])
            
            correlations.append({
                '피쳐': feature,
                '상관계수': corr_coef,
                'p값': p_value,
                '유의성': '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else '',
                '절댓값': abs(corr_coef)
            })
    
    correlation_df = pd.DataFrame(correlations).sort_values('절댓값', ascending=False)
    
    results = {
        'correlation_df': correlation_df,
        'n_samples': len(clean_data),
        'clean_data': clean_data
    }
    
    return results, None

def render_demand_forecast_features():
    """수요예측 피쳐 추출 메인 함수"""
    st.header("수요예측 피쳐 추출")
    st.caption("스킨케어 • 메이크업 카테고리 • SALES 정렬 • 최근 6개월 데이터")
    
    # 데이터 로딩
    daiso_df = load_daiso_data()
    
    if daiso_df.empty:
        st.error("필터링된 다이소 데이터가 없습니다.")
        return
    
    # 필터링 결과 표시
    skincare_count = len(daiso_df[daiso_df['category'] == 'skincare'])
    makeup_count = len(daiso_df[daiso_df['category'] == 'makeup'])
    
    # 데이터 기간 표시
    if 'review_date' in daiso_df.columns and not daiso_df['review_date'].isna().all():
        date_min = daiso_df['review_date'].min().strftime('%Y-%m-%d')
        date_max = daiso_df['review_date'].max().strftime('%Y-%m-%d')
        st.info(f"데이터 기간: {date_min} ~ {date_max} | 스킨케어 {skincare_count}개, 메이크업 {makeup_count}개 리뷰")
    else:
        st.info(f"스킨케어 {skincare_count}개, 메이크업 {makeup_count}개 리뷰")
    
    # 제품별 피쳐 추출
    product_features = extract_product_features(daiso_df)
    
    # 샘플 주별 판매량 데이터 생성
    sample_sales_data = generate_sample_weekly_sales_data(product_features)
    
    # 기본 메트릭
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 제품 수", len(product_features))
    with col2:
        st.metric("총 리뷰 수", product_features['총_리뷰수'].sum())
    with col3:
        st.metric("평균 평점", f"{product_features['평균_평점'].mean():.2f}")
    with col4:
        st.metric("샘플 데이터", f"{len(sample_sales_data)}주차")
    
    # 탭 구성
    if SHAP_AVAILABLE:
        tab1, tab2, tab3 = st.tabs(["제품별 피쳐", "순위 상관관계", "SHAP 분석"])
    else:
        tab1, tab2 = st.tabs(["제품별 피쳐", "순위 상관관계"])
    
    with tab1:
        st.subheader("제품별 기본 피쳐")
        
        if not product_features.empty:
            # 카테고리별 필터
            category_filter = st.selectbox(
                "카테고리 필터",
                options=['전체', 'skincare', 'makeup']
            )
            
            display_df = product_features.copy()
            if category_filter != '전체':
                display_df = display_df[display_df['카테고리'] == category_filter]
            
            # 표시할 컬럼 선택
            display_columns = [
                '제품명', '카테고리', '순위', '총_리뷰수', '평균_평점', 
                '긍정_비율', '부정_비율', '평균_리뷰길이', '긴리뷰_비율'
            ]
            
            available_columns = [col for col in display_columns if col in display_df.columns]
            
            st.dataframe(
                display_df[available_columns].round(4),
                use_container_width=True
            )
            
            # CSV 다운로드
            csv_data = product_features.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV 다운로드",
                data=csv_data,
                file_name=f"product_features_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("제품별 피쳐를 추출할 수 없습니다.")
    
    with tab2:
        st.subheader("순위 상관관계 분석")
        
        if not product_features.empty:
            # 카테고리 선택
            analysis_category = st.selectbox(
                "분석할 카테고리 선택",
                options=['skincare', 'makeup'],
                key="analysis_category"
            )
            
            # 선택된 카테고리만 필터링
            category_data = product_features[product_features['카테고리'] == analysis_category].copy()
            
            if len(category_data) < 5:
                st.warning(f"{analysis_category} 카테고리에 분석할 데이터가 부족합니다")
                return
            
            st.info(f"{analysis_category} 카테고리 {len(category_data)}개 제품 분석")
            
            with st.spinner("상관관계 분석 수행 중..."):
                analysis_results, error_msg = perform_rank_correlation_analysis(category_data)
            
            if analysis_results:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("분석 제품 수", f"{analysis_results['n_samples']}개")
                with col2:
                    significant_count = len(analysis_results['correlation_df'][analysis_results['correlation_df']['p값'] < 0.05])
                    st.metric("유의한 피쳐", f"{significant_count}개")
                
                # 상관관계 테이블
                st.dataframe(
                    analysis_results['correlation_df'][['피쳐', '상관계수', 'p값', '유의성']].round(6),
                    use_container_width=True
                )
                
                # 유의한 상관관계만 시각화
                significant_corr = analysis_results['correlation_df'][analysis_results['correlation_df']['p값'] < 0.05]
                
                if not significant_corr.empty:
                    fig = px.bar(
                        significant_corr,
                        x='상관계수',
                        y='피쳐',
                        orientation='h',
                        title="순위와 유의한 상관관계",
                        text='상관계수',
                        color='상관계수',
                        color_continuous_scale='RdBu_r'
                    )
                    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    fig.add_vline(x=0, line_dash="dash", line_color="gray")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("통계적으로 유의한 상관관계가 없습니다.")
                
            else:
                st.error(f"상관관계 분석 실패: {error_msg}")
        else:
            st.warning("상관관계 분석을 위한 데이터가 없습니다.")
    
    # SHAP 분석 탭
    if SHAP_AVAILABLE:
        with tab3:
            st.subheader("SHAP 분석")
            
            if not sample_sales_data.empty:
                # 카테고리 선택
                sales_category = st.selectbox(
                    "SHAP 분석할 카테고리",
                    options=['전체', 'skincare', 'makeup'],
                    key="sales_category"
                )
                
                with st.spinner("SHAP 분석 수행 중..."):
                    regression_results, shap_results, error_msg = perform_sales_prediction_analysis(sample_sales_data, sales_category)
                
                if regression_results and shap_results:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("R² Score", f"{regression_results['r2_score']:.4f}")
                    with col2:
                        st.metric("샘플 수", f"{regression_results['n_samples']:,}")
                    with col3:
                        significant_features = len([p for p in regression_results['p_values'] if p < 0.05])
                        st.metric("유의한 피쳐", f"{significant_features}개")
                    
                    # SHAP 피쳐 중요도 계산
                    feature_importance = np.abs(shap_results['shap_values']).mean(axis=0)
                    
                    # 중요도 순으로 정렬
                    sorted_indices = np.argsort(feature_importance)[::-1]
                    sorted_features = [shap_results['feature_names'][i] for i in sorted_indices]
                    sorted_importance = feature_importance[sorted_indices]
                    
                    # SHAP 중요도 차트
                    fig_shap = go.Figure()
                    fig_shap.add_trace(go.Bar(
                        x=sorted_importance,
                        y=sorted_features,
                        orientation='h',
                        text=[f'{val:.4f}' for val in sorted_importance],
                        textposition='outside',
                        marker_color='lightblue'
                    ))
                    
                    fig_shap.update_layout(
                        title="SHAP 피쳐 중요도",
                        xaxis_title="평균 SHAP 기여도",
                        yaxis_title="피쳐",
                        yaxis={'categoryorder':'total ascending'},
                        height=400
                    )
                    
                    st.plotly_chart(fig_shap, use_container_width=True)
                    
                    # SHAP 값 요약 테이블
                    shap_summary = pd.DataFrame({
                        '피쳐': sorted_features,
                        'SHAP_중요도': sorted_importance,
                        '순위': range(1, len(sorted_features) + 1)
                    })
                    
                    st.dataframe(shap_summary.round(6), use_container_width=True)
                    
                    # 샘플 데이터 보기
                    with st.expander("샘플 데이터 보기"):
                        sample_display = sample_sales_data.head(20)
                        st.dataframe(sample_display.round(2), use_container_width=True)
                
                elif regression_results:
                    st.warning("SHAP 분석을 수행할 수 없습니다.")
                    
                    # 기본 회귀분석 결과
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("R² Score", f"{regression_results['r2_score']:.4f}")
                    with col2:
                        st.metric("샘플 수", f"{regression_results['n_samples']:,}")
                    
                    # 회귀계수 표시
                    coef_df = pd.DataFrame({
                        '피쳐': regression_results['feature_names'],
                        '회귀계수': regression_results['coefficients'],
                        'p값': regression_results['p_values'],
                        '유의성': ['***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '' for p in regression_results['p_values']]
                    })
                    
                    st.dataframe(coef_df.round(6), use_container_width=True)
                
                else:
                    st.error(f"분석 실패: {error_msg}")
            else:
                st.warning("샘플 데이터가 없습니다.")

if __name__ == "__main__":
    render_demand_forecast_features()