#//==============================================================================//#
"""
main_tab.py

분석 메인 화면
- 사이드바에서 분석 메뉴 선택
- 각 분석 페이지로 라우팅

last_updated : 2025.10.23
"""
#//==============================================================================//#
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
    
    elif selected_analysis == "채널":
        try:
            import pages.channel_analysis as channel_analysis
            channel_analysis.main()
        except ImportError as e:
            st.error(f"채널 분석 모듈 로드 실패: {e}")
    
    elif selected_analysis == "브랜드":
        try:
            import pages.brand_analysis as brand_analysis
            brand_analysis.main()
        except ImportError as e:
            st.error(f"브랜드 분석 모듈 로드 실패: {e}")
    
    elif selected_analysis == "제품":
        try:
            import pages.product_analysis as product_analysis
            product_analysis.main()
        except ImportError as e:
            st.error(f"제품 분석 모듈 로드 실패: {e}")
    
    elif selected_analysis == "LG생활건강":
        try:
            import pages.lghnh_analysis as lghh_analysis
            lghh_analysis.main()
        except ImportError as e:
            st.error(f"LG생활건강 분석 모듈 로드 실패: {e}")

    elif selected_analysis == "신조어 분석":
        try:
            import pages.newword_analysis as newword_analysis
            newword_analysis.main()
        except ImportError as e:
            st.error(f"신조어 분석 모듈 로드 실패: {e}")

    elif selected_analysis == "AI Chatbot (V6)":
        try:
            import pages.ai_chatbot_v6 as ai_chatbot_v6
            ai_chatbot_v6.main()
        except ImportError as e:
            st.error(f"AI Chatbot V6 모듈 로드 실패: {e}")

    elif selected_analysis == "이전 모델 (V1-V5)":
        try:
            import pages.ai_chat as ai_chat
            ai_chat.main()
        except ImportError as e:
            st.error(f"이전 모델 로드 실패: {e}")

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
                <div style="color: #262730; font-size: 1.1rem; font-weight: bold; margin-bottom: 0.5rem; margin-top: 0.2rem;">
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

        st.markdown("---")

        # 분석 메뉴
        st.markdown("### 분석 메뉴")

        analysis_options = [
            "대시보드 홈",
            "LG생활건강",
            "채널",
            "브랜드",
            "제품",
            "신조어 분석",
            "AI Chatbot (V6)",
            "이전 모델 (V1-V5)"
        ]
        
        if 'selected_analysis' not in st.session_state:
            st.session_state.selected_analysis = "대시보드 홈"
        
        selected_analysis = st.selectbox(
            "메뉴 선택:",
            analysis_options,
            index=analysis_options.index(st.session_state.selected_analysis),
            key="analysis_menu"
        )
        
        if selected_analysis != st.session_state.selected_analysis:
            st.session_state.selected_analysis = selected_analysis
            st.rerun()
        
        # 메뉴별 설명
        descriptions = {
            "대시보드 홈": "전체 데이터 현황",
            "LG생활건강": "LG생건 제품 집중 분석",
            "채널": "채널별 상세 분석",
            "브랜드": "브랜드별 상세 분석",
            "제품": "제품별 상세 분석",
            "신조어 분석": "신조어 검색 및 사전 관리",
            "AI Chatbot (V6)": "자연어 질의응답",
            "이전 모델 (V1-V5)": "이전 AI Chatbot 모델"
        }

        if selected_analysis in descriptions:
            st.caption(descriptions[selected_analysis])

        # 북마크 UI 추가
        from utils.analysis_bookmark import show_bookmarks_sidebar
        show_bookmarks_sidebar()

def show_analysis_home():
    """분석 대시보드 홈 - 전체 현황"""
    
    st.title("뷰티 리뷰 데이터 분석 프레임워크")
    st.markdown("**현황 대시보드**")
    
    st.markdown("---")
    
    # 전체 데이터 현황 표시
    with st.spinner("데이터 로딩 중..."):
        from dashboard_config import load_all_data
        import pandas as pd
        
        df = load_all_data()
        
        if df.empty:
            st.error("데이터를 불러올 수 없습니다.")
            return
        
        # 전체 요약
        st.subheader("📊 데이터 현황")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 리뷰", f"{len(df):,}개")
        with col2:
            channel_count = df['channel'].nunique() if 'channel' in df.columns else 0
            st.metric("채널 수", f"{channel_count}개")
        with col3:
            brand_count = df['brand'].nunique() if 'brand' in df.columns else 0
            st.metric("브랜드 수", f"{brand_count:,}개")
        with col4:
            product_count = df['product_name'].nunique() if 'product_name' in df.columns else 0
            st.metric("제품 수", f"{product_count:,}개")
        
        st.markdown("---")
        
        # 채널별 현황
        st.subheader("📍 채널별 현황")
        
        if 'channel' in df.columns:
            channel_stats = df.groupby('channel').agg({
                'review_id': 'count',
                'brand': 'nunique',
                'product_name': 'nunique'
            }).reset_index()
            
            channel_stats.columns = ['채널', '리뷰 수', '브랜드 수', '제품 수']
            channel_stats = channel_stats.sort_values('리뷰 수', ascending=False)
            
            st.dataframe(channel_stats, use_container_width=True, hide_index=True)
        
        st.markdown("---")

        # 데이터 수집 기간
        st.subheader("📅 데이터 수집 기간")

        if 'review_date' in df.columns:
            df_copy = df.copy()
            df_copy['review_date'] = pd.to_datetime(df_copy['review_date'], errors='coerce')
            valid_dates = df_copy['review_date'].dropna()

            if not valid_dates.empty:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                duration = (max_date - min_date).days

                # 한 줄로 표시
                st.markdown(
                    f"**최초:** {min_date.strftime('%Y-%m-%d')} | "
                    f"**최근:** {max_date.strftime('%Y-%m-%d')} | "
                    f"**기간:** {duration}일"
                )


if __name__ == "__main__":
    main()