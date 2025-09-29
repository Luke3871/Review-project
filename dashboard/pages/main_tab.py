"""
분석 메인 화면
- 사이드바에서 분석 메뉴 선택
- 각 분석 페이지로 라우팅
"""

import streamlit as st
import sys
import os

# 경로 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    """분석 메인 화면"""
    
    # 세션 상태 초기화 확인
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'selected_analysis' not in st.session_state:
        st.session_state.selected_analysis = "대시보드 홈"
    
    # 로그인 확인
    if not st.session_state.get('logged_in', False):
        st.error("로그인이 필요합니다.")
        st.info("main_section.py로 돌아가서 로그인해주세요.")
        st.stop()
    
    # 공통 사이드바 (사용자 정보, 히스토리 등)
    show_analysis_sidebar()
    
    # 선택된 분석에 따라 라우팅
    selected_analysis = st.session_state.get('selected_analysis', '대시보드 홈')
    
    if selected_analysis == "대시보드 홈":
        show_analysis_home()
    elif selected_analysis == "기본 통계량":
        try:
            import pages.basic_stats as basic_stats
            basic_stats.main()
        except ImportError:
            st.error("pages/basic_stats.py 모듈을 찾을 수 없습니다.")
    elif selected_analysis == "리뷰 분석":
        try:
            import pages.text_mining.review_analysis as review_analysis
            review_analysis.main()
        except ImportError:
            st.error("pages/review_analysis.py 모듈이 구현되지 않았습니다.")
            show_coming_soon("리뷰 분석")
    elif selected_analysis == "신조어 분석":
        try:
            import analyzer.newword_analysis as newword_analysis
            newword_analysis.main()
        except ImportError:
            st.error("pages/newword_analysis.py 모듈이 구현되지 않았습니다.")
            show_coming_soon("신조어 분석")

def show_analysis_sidebar():
    """분석용 사이드바"""
    
    with st.sidebar:
        # 사용자 정보 (깔끔한 디자인)
        username = st.session_state.get('username', '사용자')
        if username:
            # 사용자명과 로그아웃 버튼을 같은 행에
            col1, col2 = st.columns([2.5, 1.5])
            
            with col1:
                st.markdown(f"""
                <div style="color: white; font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; margin-top: 0.2rem;">
                    {username}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("logout", key="logout_btn", help="로그아웃"):
                    # 모든 세션 상태 초기화
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            
            # 로그인 날짜
            import datetime
            login_date = datetime.datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
            st.markdown(f"""
            <div style="color: #888; font-size: 0.8rem; margin-bottom: 1rem;">
                로그인: {login_date}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("사용자 정보가 없습니다.")
        
        # 분석 히스토리 (상단 이동)
        st.markdown("**분석 히스토리**")
        if 'analysis_history' not in st.session_state:
            st.session_state.analysis_history = []
        
        if st.session_state.analysis_history:
            for i, history in enumerate(st.session_state.analysis_history[-5:]):  # 최근 5개만
                st.markdown(f"<div style='font-size: 0.8rem; color: #ccc; margin-bottom: 0.2rem;'>• {history}</div>", unsafe_allow_html=True)
            
            if st.button("히스토리 삭제", use_container_width=True, key="clear_history"):
                st.session_state.analysis_history = []
                st.rerun()
        else:
            st.markdown("<div style='font-size: 0.8rem; color: #888;'>분석 히스토리가 없습니다.</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 분석 메뉴
        st.markdown("### 분석 메뉴")
        
        analysis_options = [
            "대시보드 홈",
            "기본 통계량",
            "채널별 비교 분석",
            "리뷰 분석", 
            "신조어 분석"
        ]
        
        if 'selected_analysis' not in st.session_state:
            st.session_state.selected_analysis = "대시보드 홈"
        
        selected_analysis = st.selectbox(
            "분석 유형을 선택하세요:",
            analysis_options,
            index=analysis_options.index(st.session_state.selected_analysis),
            key="analysis_menu"
        )
        
        if selected_analysis != st.session_state.selected_analysis:
            st.session_state.selected_analysis = selected_analysis
            st.rerun()
        
        # 메뉴별 설명
        if selected_analysis == "기본 통계량":
            st.info("채널별 기본 통계량 및 현황을 확인합니다")
        elif selected_analysis == "리뷰 분석":
            st.info("텍스트 분석 및 벡터라이저를 활용한 리뷰 분석")
        elif selected_analysis == "신조어 분석":
            st.info("리뷰에서 신조어 사용 현황을 분석하고 관리합니다")

def show_analysis_home():
    """분석 대시보드 홈"""
    
    st.title("리뷰 데이터 분석 Framework")
    st.markdown("**LG 생활건강 뷰티 제품 리뷰 분석**")
    
    # 전체 현황
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("전체 채널", "3개", help="다이소, 올리브영, 쿠팡")
    with col2:
        st.metric("분석 가능 데이터", "1개", help="기본 통계량 분석")
    
    st.markdown("---")
    
    # 빠른 시작 섹션
    st.subheader("빠른 시작")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📊 기본 통계량
        - 채널별 리뷰 현황 확인
        - 제품별 분석 및 평점 분포
        - 시간대별 리뷰 트렌드
        """)
        if st.button("기본 통계량 시작", use_container_width=True):
            st.session_state.selected_analysis = "기본 통계량"
            st.rerun()
    
    with col2:
        st.markdown("""
        #### 🔍 리뷰 분석 
        - 텍스트 감정 분석
        - 키워드 추출 및 분석
        - 벡터라이저 기반 분석
        """)
        if st.button("리뷰 분석", use_container_width=True):
            st.session_state.selected_analysis = "리뷰 분석"
            st.rerun()
    
    st.markdown("---")
    
    # 최근 활동
    st.subheader("최근 활동")
    
    if st.session_state.get('analysis_history'):
        recent_activities = st.session_state.analysis_history[-3:]  # 최근 3개
        for i, activity in enumerate(reversed(recent_activities), 1):
            st.write(f"{i}. {activity}")
    else:
        st.info("아직 분석 활동이 없습니다. 위의 '빠른 시작'에서 분석을 시작해보세요!")
    
    # 사용 가이드
    with st.expander("📖 사용 가이드"):
        st.markdown("""
        ### 시작하기
        1. **사이드바에서 분석 메뉴 선택**: 원하는 분석 유형을 선택하세요
        2. **채널과 카테고리 선택**: 분석할 데이터 범위를 설정하세요
        3. **분석 실행**: '분석 실행' 버튼을 클릭하여 결과를 확인하세요
        
        ### 주요 기능
        - **기본 통계량**: 리뷰 수, 평점, 트렌드 등 기본 현황
        - **리뷰 분석**: 감정 분석, 키워드 추출 (개발 예정)
        - **신조어 분석**: 신조어 탐지 및 관리 (개발 예정)
        
        ### 데이터 현황
        - **다이소**: 제품 리뷰 데이터
        - **올리브영**: 제품 리뷰 데이터  
        - **쿠팡**: 제품 리뷰 데이터
        """)

def show_coming_soon(feature_name):
    """개발 예정 기능 안내"""
    
    st.title(f"{feature_name} (개발 예정)")
    
    st.info(f"{feature_name} 기능은 현재 개발 중입니다.")
    
    st.markdown(f"""
    ### {feature_name} 예정 기능
    """)
    
    if feature_name == "리뷰 분석":
        st.markdown("""
        - **감정 분석**: 긍정/부정 리뷰 분류
        - **키워드 추출**: 주요 키워드 및 토픽 분석
        - **텍스트 클러스터링**: 유사한 리뷰 그룹화
        - **벡터라이저 활용**: TF-IDF, Word2Vec 등
        """)
    elif feature_name == "신조어 분석":
        st.markdown("""
        - **신조어 탐지**: 새로운 단어/표현 발견
        - **트렌드 분석**: 신조어 사용 빈도 변화
        - **사용자 정의 사전**: 신조어 사전 관리
        - **의미 분석**: 신조어의 감정/의도 분석
        """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("기본 통계량으로 이동", use_container_width=True):
            st.session_state.selected_analysis = "기본 통계량"
            st.rerun()
    
    with col2:
        if st.button("홈으로 돌아가기", use_container_width=True):
            st.session_state.selected_analysis = "대시보드 홈"
            st.rerun()

if __name__ == "__main__":
    main()