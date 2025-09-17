import streamlit as st
import hashlib

# 간단한 사용자 정보 (실제 운영시에는 데이터베이스나 별도 파일로 관리)
USERS = {
    "admin": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",  # "admin123" 해시
    "user1": "04f8996da763b7a969b1028ee3007569eaf3a635486ddab211d512c85b9df8fb",  # "user123" 해시
    "demo": "2a97516c354b68848cdbd8f54a226a0a55b21ed138e207ad6c5cbb9c00aa5aea"   # "demo123" 해시
}

def hash_password(password):
    """비밀번호를 SHA-256으로 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password):
    """사용자명과 비밀번호 검증"""
    if username in USERS:
        return USERS[username] == hash_password(password)
    return False

def show_sidebar_login():
    """사이드바에서 로그인 폼 표시"""
    with st.sidebar:
        st.markdown("# 리뷰 데이터 분석")
        st.markdown("LG 생활건강")
        st.markdown("---")
        
        st.markdown("### 로그인")
        
        # 로그인 폼
        with st.form("sidebar_login_form"):
            username = st.text_input("사용자명", placeholder="사용자명")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호")
            submit_button = st.form_submit_button("로그인", type="primary", use_container_width=True)
            
            if submit_button:
                if username and password:
                    if verify_password(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.error("로그인 실패")
                else:
                    st.warning("모든 필드를 입력하세요")
        
        # 테스트 계정 정보 (개발용)
        with st.expander("테스트 계정"):
            st.markdown("""
            **계정 정보:**
            - admin / admin123
            - user1 / user123  
            - demo / demo123
            """)

def show_sidebar_navigation():
    """사이드바에서 네비게이션 및 사용자 정보 표시"""
    with st.sidebar:
        st.markdown("# 리뷰 데이터 분석")
        st.markdown("LG 생활건강")
        st.markdown("---")
        
        # 사용자 정보
        st.markdown("### 사용자 정보")
        username = st.session_state.get('username', 'Unknown')
        st.markdown(f"**접속자:** {username}")
        
        # 접속 시간 표시
        import datetime
        if 'login_time' not in st.session_state:
            st.session_state.login_time = datetime.datetime.now()
        
        login_time = st.session_state.login_time.strftime("%Y-%m-%d %H:%M")
        st.markdown(f"**접속 시간:** {login_time}")
        
        st.markdown("---")
        
        # 분석 메뉴 선택
        st.markdown("### 분석 메뉴")
        
        analysis_options = [
            "대시보드 홈",
            "다이소 분석", 
            "수요예측 피쳐 추출",
            "쿠팡 분석", 
            "올리브영 분석", 
            "통합 분석",
            "신조어 분석"
        ]
        
        # 세션에 현재 선택된 메뉴가 없으면 기본값 설정
        if 'selected_analysis' not in st.session_state:
            st.session_state.selected_analysis = "대시보드 홈"
        
        selected_analysis = st.selectbox(
            "분석 유형을 선택하세요:",
            analysis_options,
            index=analysis_options.index(st.session_state.selected_analysis),
            key="analysis_menu"
        )
        
        # 선택이 변경되면 세션에 저장
        if selected_analysis != st.session_state.selected_analysis:
            st.session_state.selected_analysis = selected_analysis
            st.rerun()
        
        # 메뉴별 설명
        if selected_analysis == "수요예측 피쳐 추출":
            st.info("리뷰 기반 수요예측 변수를 생성하고 분석합니다")
        elif selected_analysis == "다이소 분석":
            st.info("다이소 제품의 상세 리뷰 분석을 제공합니다")
        elif selected_analysis in ["쿠팡 분석", "올리브영 분석"]:
            st.warning("개발 중인 기능입니다")
        elif selected_analysis == "신조어 분석":
            st.info("리뷰에서 신조어 사용 현황을 분석하고 관리합니다")

        st.markdown("---")
        
        # 로그아웃 버튼
        if st.button("로그아웃", type="secondary", use_container_width=True):
            # 세션 상태 초기화
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def check_login():
    """로그인 상태 확인"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    return st.session_state.logged_in

def require_login(func):
    """로그인 데코레이터 (함수용)"""
    def wrapper(*args, **kwargs):
        if check_login():
            return func(*args, **kwargs)
        else:
            show_sidebar_login()
            return None
    return wrapper