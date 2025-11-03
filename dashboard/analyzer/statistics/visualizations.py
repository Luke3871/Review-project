#//==============================================================================//#
"""
visualization.py

 - 시각화 툴


last_updated : 2025.10.16
"""
#//==============================================================================//#
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_product_chart(product_counts, title="제품별 리뷰 수 TOP 15"):
    """제품별 리뷰 수 막대 그래프"""
    
    fig = px.bar(
        x=product_counts.values,
        y=product_counts.index,
        orientation='h',
        labels={'x': '리뷰 수', 'y': '제품명'}
    )
    fig.update_layout(
        title=title,
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    return fig


def create_brand_chart(brand_counts, title="브랜드별 리뷰 수 TOP 15"):
    """브랜드별 리뷰 수 막대 그래프"""
    
    fig = px.bar(
        x=brand_counts.values,
        y=brand_counts.index,
        orientation='h',
        labels={'x': '리뷰 수', 'y': '브랜드'}
    )
    fig.update_layout(
        title=title,
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    return fig


def create_rating_chart(avg_ratings_df, title="평점 높은 제품 TOP 10"):
    """평균 평점 막대 그래프"""
    
    fig = px.bar(
        x=avg_ratings_df['mean'],
        y=avg_ratings_df.index,
        orientation='h',
        labels={'x': '평균 평점', 'y': '제품명'}
    )
    fig.update_layout(
        title=title,
        height=400,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    return fig


def create_rating_histogram(ratings_series, title="평점 분포"):
    """평점 히스토그램"""

    # 평점은 1~5의 정수값이므로 5개 bin으로 고정
    fig = px.histogram(
        x=ratings_series,
        nbins=5,
        labels={'x': '평점', 'y': '빈도'}
    )
    fig.update_layout(
        title=title,
        showlegend=False,
        xaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,
            range=[0.5, 5.5]
        )
    )
    return fig


def create_rating_bar_chart(rating_counts, title="평점별 리뷰 수"):
    """평점별 막대 그래프"""

    fig = px.bar(
        x=rating_counts.index,
        y=rating_counts.values,
        labels={'x': '평점', 'y': '리뷰 수'}
    )
    fig.update_layout(
        title=title,
        showlegend=False,
        xaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,
            range=[0.5, 5.5]
        )
    )
    return fig


def create_trend_chart(time_series, title="시간별 리뷰 트렌드", x_label="기간"):
    """시계열 라인 차트"""
    
    fig = px.line(
        x=[str(p) for p in time_series.index],
        y=time_series.values,
        labels={'x': x_label, 'y': '리뷰 수'}
    )
    fig.update_traces(mode='lines+markers')
    fig.update_layout(
        title=title,
        showlegend=False
    )
    return fig

