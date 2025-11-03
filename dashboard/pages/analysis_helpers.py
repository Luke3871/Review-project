"""
분석 페이지 공통 헬퍼 함수
"""
import streamlit as st


def switch_to_page(page_name, **kwargs):
    """페이지 전환
    
    Args:
        page_name: 'channel', 'brand', 'product', 'lghh'
        **kwargs: session state에 저장할 값들
    
    Example:
        switch_to_page('brand', selected_channel='Coupang', selected_brand='VT')
    """
    # 페이지명 매핑
    page_map = {
        'channel': '채널',
        'brand': '브랜드',
        'product': '제품',
        'lghh': 'LG생활건강'
    }
    
    st.session_state.selected_analysis = page_map.get(page_name, page_name)
    
    # 필터 값 저장
    for key, value in kwargs.items():
        st.session_state[key] = value
    
    st.rerun()


def show_clickable_chart(fig, key, on_click):
    """클릭 가능한 차트 표시 및 이벤트 처리
    
    Args:
        fig: Plotly figure 객체
        key: 차트 고유 키
        on_click: 클릭시 실행할 콜백 함수 (clicked_value를 인자로 받음)
    
    Example:
        show_clickable_chart(
            fig,
            "channel_brand_chart",
            lambda brand: switch_to_page('brand', selected_brand=brand)
        )
    """
    
    # 클릭 처리 플래그
    flag_key = f"{key}_click_processed"
    
    if flag_key not in st.session_state:
        st.session_state[flag_key] = False
    
    # 차트 표시
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key=key
    )
    
    # 클릭 이벤트 처리 (한 번만)
    if event and hasattr(event, 'selection') and event.selection:
        if hasattr(event.selection, 'points') and event.selection.points:
            if not st.session_state[flag_key]:
                # 클릭된 값 추출
                clicked_value = event.selection.points[0]['y']
                
                # 플래그 설정
                st.session_state[flag_key] = True
                
                # 콜백 실행
                on_click(clicked_value)
        else:
            # 선택 해제되면 플래그 리셋
            st.session_state[flag_key] = False
    else:
        # 이벤트 없으면 플래그 리셋
        st.session_state[flag_key] = False


def show_breadcrumb(items):
    """경로 표시 (Breadcrumb)
    
    Args:
        items: 경로 리스트 ['Coupang', 'VT', '시카크림']
    """
    breadcrumb = " > ".join(items)
    st.caption(f"📍 {breadcrumb}")


def initialize_filter_states():
    """필터 관련 session state 초기화"""
    defaults = {
        'selected_channel': None,
        'selected_brand': None,
        'selected_category': '전체',
        'selected_product': None,
        'selected_option': '전체',
        'selected_period': '전체'
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_analysis_cache(page_name):
    """특정 페이지의 분석 캐시 초기화
    
    Args:
        page_name: 'channel', 'brand', 'product', 'lghh'
    """
    cache_keys = [
        f'{page_name}_analysis_df',
        f'{page_name}_analysis_done'
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]