#//==============================================================================//#
"""
분석 북마크 관리 유틸리티

기능:
- 분석 결과 자동 저장 (최대 9개, FIFO)
- 중요한 분석 고정 (무제한)
- 북마크 불러오기

last_updated: 2025.10.25
"""
#//==============================================================================//#
import streamlit as st
from datetime import datetime
import uuid


def initialize_bookmarks():
    """북마크 세션 상태 초기화"""
    if 'analysis_bookmarks' not in st.session_state:
        st.session_state.analysis_bookmarks = {
            'pinned': [],    # 고정된 분석 (무제한)
            'recent': []     # 최근 분석 (최대 9개, FIFO)
        }


def save_analysis(page_type, title, filters, df):
    """분석 결과 자동 저장

    Args:
        page_type (str): 페이지 타입 ('channel', 'brand', 'product', 'lghnh')
        title (str): 분석 제목 (예: "올리브영 > 스킨케어")
        filters (dict): 필터 조건
        df (DataFrame): 분석 데이터
    """
    initialize_bookmarks()

    # 북마크 객체 생성
    bookmark = {
        'id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'page_type': page_type,
        'title': title,
        'filters': filters,
        'df': df,
        'pinned': False
    }

    # 최근 분석에 추가
    st.session_state.analysis_bookmarks['recent'].insert(0, bookmark)

    # FIFO: 9개 초과 시 가장 오래된 것 삭제
    if len(st.session_state.analysis_bookmarks['recent']) > 9:
        st.session_state.analysis_bookmarks['recent'].pop()


def pin_bookmark(bookmark_id):
    """북마크 고정

    Args:
        bookmark_id (str): 북마크 ID
    """
    initialize_bookmarks()

    # recent에서 찾아서 pinned로 이동
    for i, bookmark in enumerate(st.session_state.analysis_bookmarks['recent']):
        if bookmark['id'] == bookmark_id:
            bookmark['pinned'] = True
            st.session_state.analysis_bookmarks['pinned'].append(bookmark)
            st.session_state.analysis_bookmarks['recent'].pop(i)
            return True

    return False


def unpin_bookmark(bookmark_id):
    """북마크 고정 해제

    Args:
        bookmark_id (str): 북마크 ID
    """
    initialize_bookmarks()

    # pinned에서 찾아서 recent로 이동
    for i, bookmark in enumerate(st.session_state.analysis_bookmarks['pinned']):
        if bookmark['id'] == bookmark_id:
            bookmark['pinned'] = False
            st.session_state.analysis_bookmarks['recent'].insert(0, bookmark)
            st.session_state.analysis_bookmarks['pinned'].pop(i)

            # FIFO 적용
            if len(st.session_state.analysis_bookmarks['recent']) > 9:
                st.session_state.analysis_bookmarks['recent'].pop()

            return True

    return False


def delete_bookmark(bookmark_id):
    """북마크 삭제 (recent만)

    Args:
        bookmark_id (str): 북마크 ID
    """
    initialize_bookmarks()

    # recent에서만 삭제 가능
    for i, bookmark in enumerate(st.session_state.analysis_bookmarks['recent']):
        if bookmark['id'] == bookmark_id:
            st.session_state.analysis_bookmarks['recent'].pop(i)
            return True

    return False


def get_all_bookmarks():
    """모든 북마크 가져오기

    Returns:
        dict: {'pinned': [...], 'recent': [...]}
    """
    initialize_bookmarks()
    return st.session_state.analysis_bookmarks


def clear_recent_bookmarks():
    """최근 분석 전체 삭제 (고정된 것 제외)"""
    initialize_bookmarks()
    st.session_state.analysis_bookmarks['recent'] = []


def load_bookmark(bookmark_id):
    """북마크 불러오기

    Args:
        bookmark_id (str): 북마크 ID

    Returns:
        dict: 북마크 객체 또는 None
    """
    initialize_bookmarks()

    # pinned에서 찾기
    for bookmark in st.session_state.analysis_bookmarks['pinned']:
        if bookmark['id'] == bookmark_id:
            return bookmark

    # recent에서 찾기
    for bookmark in st.session_state.analysis_bookmarks['recent']:
        if bookmark['id'] == bookmark_id:
            return bookmark

    return None


def get_bookmark_count():
    """북마크 총 개수

    Returns:
        dict: {'pinned': int, 'recent': int, 'total': int}
    """
    initialize_bookmarks()

    pinned_count = len(st.session_state.analysis_bookmarks['pinned'])
    recent_count = len(st.session_state.analysis_bookmarks['recent'])

    return {
        'pinned': pinned_count,
        'recent': recent_count,
        'total': pinned_count + recent_count
    }


def show_bookmarks_sidebar():
    """사이드바에 북마크 UI 표시"""
    initialize_bookmarks()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📌 저장된 분석")

    counts = get_bookmark_count()
    st.sidebar.caption(f"고정 {counts['pinned']}개 | 최근 {counts['recent']}개")

    bookmarks = get_all_bookmarks()

    # 고정된 분석
    if bookmarks['pinned']:
        st.sidebar.markdown("#### 📍 고정된 분석")
        for bookmark in bookmarks['pinned']:
            with st.sidebar.expander(f"📌 {bookmark['title']}", expanded=False):
                st.caption(f"🕒 {bookmark['timestamp']}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("불러오기", key=f"load_pinned_{bookmark['id']}", use_container_width=True):
                        restore_analysis(bookmark)
                with col2:
                    if st.button("고정 해제", key=f"unpin_{bookmark['id']}", use_container_width=True):
                        unpin_bookmark(bookmark['id'])
                        st.rerun()

    # 최근 분석
    if bookmarks['recent']:
        st.sidebar.markdown("#### 🕒 최근 분석")
        for bookmark in bookmarks['recent']:
            with st.sidebar.expander(f"{bookmark['title']}", expanded=False):
                st.caption(f"🕒 {bookmark['timestamp']}")

                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("불러오기", key=f"load_recent_{bookmark['id']}", use_container_width=True):
                        restore_analysis(bookmark)
                with col2:
                    if st.button("📌 고정", key=f"pin_{bookmark['id']}", use_container_width=True):
                        pin_bookmark(bookmark['id'])
                        st.rerun()

    # 전체 삭제 버튼
    if counts['recent'] > 0:
        if st.sidebar.button("🗑️ 최근 분석 전체 삭제", use_container_width=True):
            clear_recent_bookmarks()
            st.rerun()

    if counts['total'] == 0:
        st.sidebar.info("저장된 분석이 없습니다.\n분석을 실행하면 자동으로 저장됩니다.")


def restore_analysis(bookmark):
    """북마크에서 분석 복원

    Args:
        bookmark (dict): 북마크 객체
    """
    # 필터 값 복원
    for key, value in bookmark['filters'].items():
        st.session_state[key] = value

    # 데이터프레임 복원
    page_type = bookmark['page_type']
    st.session_state[f'{page_type}_analysis_df'] = bookmark['df']
    st.session_state[f'{page_type}_analysis_done'] = True

    # 페이지 전환
    st.session_state.selected_analysis = {
        'channel': '채널',
        'brand': '브랜드',
        'product': '제품',
        'lghnh': 'LG생활건강'
    }.get(page_type, '채널')

    st.success(f"✅ '{bookmark['title']}' 분석을 불러왔습니다!")
    st.rerun()
