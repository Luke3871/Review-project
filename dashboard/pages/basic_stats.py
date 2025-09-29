"""
기본 통계량 분석 페이지
채널별 탭으로 구분하여 기본 통계 정보 제공
"""

import streamlit as st

def main():
    """기본 통계량 메인 함수"""
    
    # 메인 컨텐츠 (사이드바는 analysis_main.py에서 관리)
    st.header("기본 통계량")
    st.caption("채널별 제품 리뷰 기본 현황을 확인할 수 있습니다")
    
    # 채널별 탭 생성
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "다이소", "올리브영", "무신사", "쿠팡", "화해", "글로우픽"
    ])
    
    with tab1:
        try:
            import pages.channels.daiso as daiso
            daiso.show_analysis()
        except ImportError:
            st.error("channels/daiso.py 모듈을 찾을 수 없습니다.")
    
    with tab2:
        st.info("올리브영 분석 기능은 준비 중입니다.")
    
    with tab3:
        st.info("무신사 분석 기능은 준비 중입니다.")
    
    with tab4:
        st.info("쿠팡 분석 기능은 준비 중입니다.")
    
    with tab5:
        st.info("화해 분석 기능은 준비 중입니다.")
    
    with tab6:
        st.info("글로우픽 분석 기능은 준비 중입니다.")

if __name__ == "__main__":
    main()