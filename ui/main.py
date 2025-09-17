import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from login_section import show_sidebar_login, show_sidebar_navigation, check_login
from tab1_daiso_section import render_daiso_section
from demand_forecast_features import render_demand_forecast_features
from newwords_analysis_tab import render_newword_analysis_tab  # 신조어 분석 탭 import

# 다른 탭들 처리
def render_coupang_section():
    st.header("쿠팡 분석")
    st.info("구현 예정")

def render_oliveyoung_section():
    st.header("올리브영 분석")
    st.info("구현 예정")

# 페이지 설정
st.set_page_config(
    page_title="리뷰 데이터 분석 Framework",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_dashboard_home():
    """대시보드 홈 렌더링"""
    st.title("리뷰 데이터 분석 Framework")
    st.markdown("LG 생활건강")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("전체 채널", "3개")
    with col2:
        st.metric("분석 가능 데이터", "1개")
    with col3:
        st.metric("구현 진행률", "50%")

def render_integrated_analysis():
    """통합 분석"""
    st.header("통합 분석")
    st.info("다이소 데이터 기반 프로토타입")

def show_login_required_message():
    """로그인이 필요하다는 메시지 표시"""
    st.title("리뷰 데이터 분석 Framework")
    st.markdown("LG 생활건강")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("로그인이 필요합니다. 좌측 사이드바에서 로그인해주세요.")

def main():
    """메인 함수"""
    # 로그인 상태 확인
    if not check_login():
        show_sidebar_login()
        show_login_required_message()
    else:
        show_sidebar_navigation()
        
        # 선택된 분석에 따라 화면 렌더링
        selected_analysis = st.session_state.get('selected_analysis', '대시보드 홈')
        
        if selected_analysis == "대시보드 홈":
            render_dashboard_home()
        elif selected_analysis == "다이소 분석":
            render_daiso_section()
        elif selected_analysis == "수요예측 피쳐 추출":
            render_demand_forecast_features()
        elif selected_analysis == "신조어 분석":  # 신조어 분석 탭 추가
            render_newword_analysis_tab()
        elif selected_analysis == "쿠팡 분석":
            render_coupang_section()
        elif selected_analysis == "올리브영 분석":
            render_oliveyoung_section()
        elif selected_analysis == "통합 분석":
            render_integrated_analysis()

if __name__ == "__main__":
    main()


# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# import streamlit as st
# from tab1_daiso_section import render_daiso_section
# from tab2_coupang_section import render_coupang_section
# from tab3_oliveyoung_section import render_oliveyoung_section

# # 페이지 설정
# st.set_page_config(
#     page_title="뷰티 3채널 리뷰 분석",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# st.title("뷰티 3채널 리뷰 분석 대시보드")
# st.markdown("다이소 • 올리브영 • 쿠팡 리뷰 데이터 종합 분석")

# # 메인 채널별 분석 탭
# tab1, tab2, tab3, tab4 = st.tabs(["다이소 분석", "쿠팡 분석", "올리브영 분석", "통합 분석"])

# with tab1:
#     render_daiso_section()

# with tab2:
#     render_coupang_section()

# with tab3:
#     render_oliveyoung_section()

# with tab4:
#     st.header("통합 분석")
#     st.info("모든 채널 데이터 수집 완료 후 구현 예정")
    
#     # 구현 예정 기능들
#     st.subheader("구현 예정 기능")
    
#     feature_col1, feature_col2 = st.columns(2)
    
#     with feature_col1:
#         st.markdown("""
#         **채널별 시장 분석**
#         - 메이크업/스킨케어 시장 점유율
#         - 채널별 가격 포지셔닝
#         - 브랜드별 성과 비교
        
#         **트렌드 분석**
#         - 3채널 공통 인기 제품
#         - 계절별 트렌드 변화
#         - 신제품 vs 기존제품 성과
#         """)
    
#     with feature_col2:
#         st.markdown("""
#         **경쟁력 분석**
#         - 채널별 강점/약점 분석
#         - 고객 만족도 비교
#         - 리뷰 패턴 차이
        
#         **예측 모델**
#         - 제품 성공 예측
#         - 트렌드 예측
#         - 채널별 최적 전략
#         """)

# # 사이드바
# with st.sidebar:
#     st.markdown("# 뷰티 3채널 분석")
#     st.markdown("다이소 • 올리브영 • 쿠팡")

# if __name__ == "__main__":
#     pass