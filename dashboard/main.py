"""
로그인 전용 화면
- 로그인 기능만 담당
- 로그인 성공시 분석 메인으로 이동
"""

import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="리뷰 데이터 분석 Framework - 로그인",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 페이지 네비게이션 숨기기
st.markdown("""
<style>
    .stSidebar > div:first-child {
        padding-top: 0rem;
    }
    [data-testid="stSidebarNav"] {
        display: none;
    }
    [data-testid="stSidebarNav"] > ul {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# 로그인 사용자 정보
USERS = {
    "admin": "123",
    "임현석": "1234",
    "박지연": "1234"
}

def main():
    """메인 함수 - 로그인 처리만"""
    
    # 세션 상태 초기화
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    
    # 로그인 상태에 따른 처리
    if st.session_state.logged_in:
        # 로그인 완료시 분석 메인으로 이동
        redirect_to_analysis()
    else:
        # 로그인 화면 표시
        show_login_page()

def show_login_page():
    """로그인 페이지"""
    
    # 메인 화면 컨텐츠
    st.markdown("""
    <div style="text-align: center; margin-top: 6rem;">
        <h1 style="font-size: 2.5rem; font-weight: bold; color: #333; margin-bottom: 1.5rem;">
            리뷰 데이터 분석 Framework
        </h1>
        <div style="font-size: 1rem; color: #666; margin-bottom: 2rem;">
            <p style="margin: 0.3rem;">고려대학교 MSBA 캡스톤 프로젝트</p>
            <p style="margin: 0.3rem;">LG 생활건강 뷰티 제품 리뷰 분석</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 - 로그인만
    with st.sidebar:
        show_login_sidebar()

def show_login_sidebar():
    """로그인 전용 사이드바"""
    
    # 로고 (중앙 정렬)
    st.markdown('<div style="text-align: center; margin-bottom: 1rem;">', unsafe_allow_html=True)
    try:
        st.image(r"C:\ReviewFW_LG_hnh\dashboard\assets\KOREA UNIV LOGO.png", width=200)
    except:
        st.markdown("### 고려대학교")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 프로젝트 정보
    st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem; padding: 0.5rem;">
        <div style="font-size: 0.85rem; font-weight: bold; margin-bottom: 0.3rem;">MSBA Capstone Project</div>
        <div style="color: #e74c3c; font-size: 0.9rem; font-weight: bold; margin-bottom: 0.3rem;">LG 생활건강</div>
        <div style="font-size: 0.7rem; color: #999;">Team 7 | 박지연 · 임현석</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 로그인 폼
    st.markdown("#### 로그인")
    
    with st.form("login_form"):
        username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        submitted = st.form_submit_button("로그인", use_container_width=True)
        
        if submitted:
            if username in USERS and USERS[username] == password:
                # 로그인 성공
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("로그인 성공! 분석 화면으로 이동합니다...")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
    
    # 테스트 계정 정보
    with st.expander("테스트 계정"):
        st.write("• admin / 123")
        st.write("• 임현석 / 1234") 
        st.write("• 박지연 / 1234")

def redirect_to_analysis():
    """분석 메인으로 리다이렉트"""
    
    try:
        # 분석 메인 모듈 import 및 실행
        import pages.main_tab as analysis_main
        analysis_main.main()
    except ImportError:
        # 백업 화면
        st.title("분석 화면")
        st.success(f"환영합니다, {st.session_state.username}님!")
        
        st.error("pages/analysis_main.py 모듈을 찾을 수 없습니다.")
        st.info("분석 메인 화면을 생성해주세요.")
        
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

if __name__ == "__main__":
    main()