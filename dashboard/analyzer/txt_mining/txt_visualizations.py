#//==============================================================================//#
"""
텍스트 마이닝 시각화 모듈

last_updated : 2025.10.25
"""
#//==============================================================================//#
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


#//==============================================================================//#
# 키워드 워드클라우드
#//==============================================================================//#
def create_keyword_wordcloud(keyword_df, title="키워드 워드클라우드"):
    """키워드 워드클라우드 생성

    Args:
        keyword_df (DataFrame): [키워드, TF-IDF점수, 문서빈도]
        title (str): 차트 제목

    Returns:
        matplotlib.figure.Figure
    """
    if keyword_df.empty:
        return None

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import numpy as np

        # TF-IDF 점수를 딕셔너리로 변환
        word_freq = dict(zip(keyword_df['키워드'], keyword_df['TF-IDF점수']))

        # 한글 폰트 경로 찾기
        font_path = None
        font_candidates = [
            'C:/Windows/Fonts/malgun.ttf',
            'C:/Windows/Fonts/malgunbd.ttf',
            'C:/Windows/Fonts/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        ]

        for font in font_candidates:
            import os
            if os.path.exists(font):
                font_path = font
                break

        if not font_path:
            # 시스템 폰트에서 한글 폰트 찾기
            font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
            for font in font_list:
                if 'malgun' in font.lower() or 'nanum' in font.lower():
                    font_path = font
                    break

        # 원형 마스크 생성 (동그랗게) - 고해상도
        x, y = np.ogrid[:800, :800]
        mask = (x - 400) ** 2 + (y - 400) ** 2 > 380 ** 2
        mask = 255 * mask.astype(int)

        # 워드클라우드 생성 - 더욱 조밀하고 크기 차이 명확하게
        wordcloud = WordCloud(
            font_path=font_path,  # 한글 폰트
            width=800,
            height=800,
            background_color='white',
            colormap='Set2',
            relative_scaling=0.7,  # 크기 차이 확대
            min_font_size=12,      # 최소 크기
            max_font_size=100,     # 최대 크기
            prefer_horizontal=1.0,
            collocations=False,
            mask=mask,
            max_words=30,          # 단어 수 제한
            mode='RGBA',
            scale=3,               # 2 → 3: 더욱 조밀하게 배치
            repeat=False,          # 중복 방지
            contour_width=0,       # 윤곽선 제거
            contour_color='white',
            margin=1,              # 2 → 1: 단어 간 여백 최소화
            random_state=42        # 일관된 배치
        ).generate_from_frequencies(word_freq)

        # Figure 생성 - 고해상도 유지
        fig, ax = plt.subplots(figsize=(8, 8), dpi=100)
        fig.patch.set_facecolor('#f8f9fa')
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')

        # 한글 폰트로 제목 설정
        if font_path:
            font_prop = fm.FontProperties(fname=font_path, size=14, weight='bold')
            ax.set_title(title, fontproperties=font_prop, pad=20)
        else:
            ax.set_title(title, fontsize=14, pad=20, weight='bold')

        plt.tight_layout()
        return fig

    except ImportError:
        import streamlit as st
        st.warning("워드클라우드 생성을 위해 wordcloud 라이브러리가 필요합니다: pip install wordcloud")
        return None
    except Exception as e:
        import streamlit as st
        st.error(f"워드클라우드 생성 중 오류: {str(e)}")
        return None


#//==============================================================================//#
# 키워드 테이블
#//==============================================================================//#
def create_keyword_table(keyword_df):
    """키워드 테이블 (정렬 가능, 클릭 가능)
    
    Args:
        keyword_df (DataFrame): [키워드, TF-IDF점수, 문서빈도]
    
    Returns:
        DataFrame: 표시용 데이터프레임
    """
    if keyword_df.empty:
        return pd.DataFrame()
    
    display_df = keyword_df.copy()
    display_df['TF-IDF점수'] = display_df['TF-IDF점수'].round(4)
    display_df.insert(0, '순위', range(1, len(display_df) + 1))
    
    return display_df


#//==============================================================================//#
# 키워드 막대 그래프
#//==============================================================================//#
def create_keyword_bar_chart(keyword_df, title="TOP 30 키워드"):
    """키워드 막대 그래프 (가로형)
    
    Args:
        keyword_df (DataFrame): [키워드, TF-IDF점수, 문서빈도]
        title (str): 차트 제목
    
    Returns:
        plotly.graph_objects.Figure
    """
    if keyword_df.empty:
        return None
    
    fig = px.bar(
        keyword_df,
        x='TF-IDF점수',
        y='키워드',
        orientation='h',
        labels={'TF-IDF점수': 'TF-IDF 점수', '키워드': '키워드'},
        hover_data=['문서빈도']
    )
    
    fig.update_layout(
        title=title,
        height=max(500, len(keyword_df) * 25),
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        hovermode='closest'
    )
    
    return fig


#//==============================================================================//#
# 채널별 키워드 비교
#//==============================================================================//#
def create_channel_keyword_comparison(channel_keyword_dict, keyword):
    """채널별 키워드 비교 막대 그래프
    
    Args:
        channel_keyword_dict (dict): {채널명: 언급수}
        keyword (str): 키워드명
    
    Returns:
        plotly.graph_objects.Figure
    """
    if not channel_keyword_dict:
        return None
    
    df = pd.DataFrame(list(channel_keyword_dict.items()), columns=['채널', '언급수'])
    
    fig = px.bar(
        df,
        x='채널',
        y='언급수',
        title=f"채널별 '{keyword}' 언급 비교",
        labels={'언급수': '언급 횟수', '채널': '채널'}
    )
    
    fig.update_layout(
        height=400,
        showlegend=False
    )
    
    return fig


#//==============================================================================//#
# 키워드 시계열 트렌드
#//==============================================================================//#
def create_keyword_trend_line_chart(trend_df, keyword):
    """키워드 시계열 트렌드 라인 차트
    
    Args:
        trend_df (DataFrame): [날짜, 언급수]
        keyword (str): 키워드명
    
    Returns:
        plotly.graph_objects.Figure
    """
    if trend_df.empty:
        return None
    
    fig = px.line(
        trend_df,
        x='날짜',
        y='언급수',
        title=f"'{keyword}' 키워드 시계열 트렌드",
        labels={'날짜': '날짜', '언급수': '언급 횟수'}
    )
    
    fig.update_traces(mode='lines+markers')
    fig.update_layout(
        height=400,
        showlegend=False,
        hovermode='x unified'
    )
    
    return fig


#//==============================================================================//#
# 공출현 키워드
#//==============================================================================//#
def create_cooccurrence_bar_chart(cooccur_df, target_keyword):
    """공출현 키워드 막대 그래프
    
    Args:
        cooccur_df (DataFrame): [키워드, 공출현횟수, 비율(%)]
        target_keyword (str): 대상 키워드
    
    Returns:
        plotly.graph_objects.Figure
    """
    if cooccur_df.empty:
        return None
    
    fig = px.bar(
        cooccur_df,
        x='공출현횟수',
        y='키워드',
        orientation='h',
        title=f"'{target_keyword}'와 함께 언급되는 키워드 TOP 10",
        labels={'공출현횟수': '공출현 횟수', '키워드': '키워드'},
        hover_data=['비율(%)']
    )
    
    fig.update_layout(
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    return fig


#//==============================================================================//#
# 키워드별 제품 테이블
#//==============================================================================//#
def create_product_keyword_table(product_df):
    """키워드별 제품 TOP 10 테이블 (클릭 가능)
    
    Args:
        product_df (DataFrame): [순위, 제품명, 브랜드, TF-IDF점수, 리뷰수, 평균평점, 워닝]
    
    Returns:
        DataFrame: 표시용 데이터프레임
    """
    if product_df.empty:
        return pd.DataFrame()
    
    display_df = product_df.copy()
    
    # TF-IDF 점수 포맷팅
    display_df['TF-IDF점수'] = display_df['TF-IDF점수'].round(4)
    
    # 제품명 축약 (60자)
    display_df['제품명_표시'] = display_df['제품명'].str[:60] + '...'
    
    # 워닝 컬럼 제거 (표시용)
    result_df = display_df[['순위', '제품명_표시', '브랜드', 'TF-IDF점수', '리뷰수', '평균평점']].copy()
    result_df.columns = ['순위', '제품명', '브랜드', 'TF-IDF점수', '리뷰수', '평균평점']

    return result_df


#//==============================================================================//#
# 키워드 시간대별 트렌드 (다중 키워드 비교)
#//==============================================================================//#
def create_keyword_trend_chart(df, selected_keywords, time_unit, channel_name, keyword_to_indices):
    """키워드 시간대별 트렌드 차트 (여러 키워드 동시 비교)

    Args:
        df (DataFrame): 리뷰 데이터 (review_date 컬럼 필요)
        selected_keywords (list): 선택된 키워드 리스트
        time_unit (str): "월별" 또는 "주별"
        channel_name (str): 채널명
        keyword_to_indices (dict): {키워드: [리뷰 인덱스 리스트]} 매핑

    Returns:
        plotly.graph_objects.Figure
    """
    if df.empty or not selected_keywords or not keyword_to_indices:
        return None

    try:
        # 날짜 컬럼 확인 및 변환
        if 'review_date' not in df.columns:
            return None

        df_copy = df.copy()
        df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
        df_copy = df_copy.dropna(subset=['review_date'])

        if df_copy.empty:
            return None

        # 시간 단위에 따라 그룹화
        if time_unit == "월별":
            df_copy['period'] = df_copy['review_date'].dt.to_period('M')
            time_format = '%Y-%m'
        else:  # 주별
            df_copy['period'] = df_copy['review_date'].dt.to_period('W')
            time_format = '%Y-W%U'

        # 각 키워드별로 시간대별 언급 횟수 계산
        trend_data = []

        for keyword in selected_keywords:
            # 저장된 인덱스로 키워드 리뷰 필터링 (텍스트 검색 없이)
            review_indices = keyword_to_indices.get(keyword, [])

            if not review_indices:
                continue

            # 인덱스가 df_copy에 존재하는 것만 필터링
            valid_indices = [idx for idx in review_indices if idx in df_copy.index]

            if not valid_indices:
                continue

            keyword_df = df_copy.loc[valid_indices].copy()

            # 시간대별 언급 횟수
            period_counts = keyword_df.groupby('period').size().reset_index(name='count')
            period_counts['keyword'] = keyword
            period_counts['period_str'] = period_counts['period'].astype(str)

            trend_data.append(period_counts)

        if not trend_data:
            return None

        # 모든 키워드 데이터 합치기
        combined_df = pd.concat(trend_data, ignore_index=True)

        # Plotly 라인 차트 생성
        fig = go.Figure()

        for keyword in selected_keywords:
            keyword_data = combined_df[combined_df['keyword'] == keyword]

            if not keyword_data.empty:
                fig.add_trace(go.Scatter(
                    x=keyword_data['period_str'],
                    y=keyword_data['count'],
                    mode='lines+markers',
                    name=keyword,
                    line=dict(width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                  '기간: %{x}<br>' +
                                  '언급 횟수: %{y}<br>' +
                                  '<extra></extra>'
                ))

        # 레이아웃 설정
        title_text = f"{channel_name} - 키워드 트렌드 ({time_unit})"

        fig.update_layout(
            title=title_text,
            xaxis_title="기간",
            yaxis_title="언급 횟수",
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            plot_bgcolor='white',
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                showline=True,
                linewidth=1,
                linecolor='black'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                showline=True,
                linewidth=1,
                linecolor='black'
            )
        )

        return fig

    except Exception as e:
        import streamlit as st
        st.error(f"키워드 트렌드 차트 생성 중 오류: {str(e)}")
        return None