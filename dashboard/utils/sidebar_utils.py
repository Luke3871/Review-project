import streamlit as st

def show_common_sidebar():
    """모든 페이지에서 공통으로 사용할 사이드바"""
    with st.sidebar:
        # 사용자 정보
        if st.session_state.get('logged_in', False):
            st.success(f"환영합니다, {st.session_state.username}님!")
            
            if st.button("로그아웃", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()

            st.markdown("---")

            # 메인 메뉴로 돌아가기 버튼
            if st.button("메인 메뉴", use_container_width=True):
                st.session_state.selected_analysis = "대시보드 홈"
                st.rerun()