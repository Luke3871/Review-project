#//==============================================================================//#
"""
ai_chat.py
AI 분석 챗봇 페이지

last_updated : 2025.10.02
"""
#//==============================================================================//#

import streamlit as st
import sys
import os

# 경로 설정 수정
current_dir = os.path.dirname(os.path.abspath(__file__))  # pages 폴더
dashboard_dir = os.path.dirname(current_dir)  # dashboard 폴더
project_root = os.path.dirname(dashboard_dir)  # ReviewFW_LG_hnh 폴더

# analytics는 project_root 아래에 있음
analytics_dir = os.path.join(project_root, 'analytics')
if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

print(f"DEBUG - analytics_dir: {analytics_dir}")  # 디버깅용
print(f"DEBUG - sys.path: {sys.path[:3]}")  # 확인용

from agents.orchestrator import Orchestrator

#//==============================================================================//#
# 설정
#//==============================================================================//#

DB_CONFIG = {
    "dbname": "ragdb",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432
}

#//==============================================================================//#
# 메인
#//==============================================================================//#

def main():
    st.header("AI 분석 챗봇")
    st.caption("자연어로 질문하면 AI가 데이터를 분석하여 답변합니다")
    
    # API 키 입력
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    
    with st.sidebar:
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="챗봇 사용을 위해 API 키가 필요합니다"
        )
        
        if api_key:
            st.session_state.api_key = api_key
            st.success("API 키 설정 완료")
        else:
            st.warning("API 키를 입력하세요")
    
    # 채팅 히스토리 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # 이전 메시지 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    
    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요 (예: 토리든 보습 어때?)"):
        
        if not st.session_state.api_key:
            st.error("먼저 API 키를 입력하세요")
            return
        
        # 사용자 메시지 추가
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        
        with st.chat_message('user'):
            st.markdown(prompt)
        
        # AI 응답
        with st.chat_message('assistant'):
            with st.spinner('분석 중...'):
                response = execute_agent(prompt, st.session_state.api_key)
                st.markdown(response)
        
        # 응답 저장
        st.session_state.messages.append({'role': 'assistant', 'content': response})


def execute_agent(user_query: str, api_key: str) -> str:
    """
    Agent 실행
    """
    
    try:
        # Orchestrator 초기화
        orchestrator = Orchestrator(api_key, DB_CONFIG)
        
        # 쿼리 처리
        result = orchestrator.process_query(user_query)
        
        return result['answer']
        
    except Exception as e:
        return f"오류 발생: {e}"


if __name__ == "__main__":
    main()