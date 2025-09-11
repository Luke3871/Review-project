import sys, os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
from tab1_daiso_section import render_daiso_section
from tab2_coupang_section import render_coupang_section
from tab3_oliveyoung_section import render_oliveyoung_section

# 페이지 설정
st.set_page_config(
    page_title="뷰티 3채널 리뷰 분석",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("뷰티 3채널 리뷰 분석 대시보드")
st.markdown("다이소 • 올리브영 • 쿠팡 리뷰 데이터 종합 분석")

# 메인 채널별 분석 탭
tab1, tab2, tab3, tab4 = st.tabs(["다이소 분석", "쿠팡 분석", "올리브영 분석", "통합 분석"])

with tab1:
    render_daiso_section()

with tab2:
    render_coupang_section()

with tab3:
    render_oliveyoung_section()

with tab4:
    st.header("통합 분석")
    st.info("모든 채널 데이터 수집 완료 후 구현 예정")
    
    # 구현 예정 기능들
    st.subheader("구현 예정 기능")
    
    feature_col1, feature_col2 = st.columns(2)
    
    with feature_col1:
        st.markdown("""
        **채널별 시장 분석**
        - 메이크업/스킨케어 시장 점유율
        - 채널별 가격 포지셔닝
        - 브랜드별 성과 비교
        
        **트렌드 분석**
        - 3채널 공통 인기 제품
        - 계절별 트렌드 변화
        - 신제품 vs 기존제품 성과
        """)
    
    with feature_col2:
        st.markdown("""
        **경쟁력 분석**
        - 채널별 강점/약점 분석
        - 고객 만족도 비교
        - 리뷰 패턴 차이
        
        **예측 모델**
        - 제품 성공 예측
        - 트렌드 예측
        - 채널별 최적 전략
        """)

# 사이드바
with st.sidebar:
    st.markdown("# 뷰티 3채널 분석")
    st.markdown("다이소 • 올리브영 • 쿠팡")

if __name__ == "__main__":
    # 스트림릿 실행: streamlit run main.py
    pass