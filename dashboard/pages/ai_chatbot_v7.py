#//==============================================================================//#
"""
ai_chatbot_v7.py
V7 LangGraph ReAct Agent 챗봇 페이지

LLM이 Tool을 동적으로 선택하는 ReAct 패턴

last_updated: 2025.11.02
"""
#//==============================================================================//#

import streamlit as st
import sys
import os
from pathlib import Path

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(dashboard_dir)

# ai_engines 경로 추가
ai_engines_dir = os.path.join(dashboard_dir, 'ai_engines')
v7_dir = os.path.join(ai_engines_dir, 'v7_langgraph_agent')

if ai_engines_dir not in sys.path:
    sys.path.insert(0, ai_engines_dir)
if v7_dir not in sys.path:
    sys.path.insert(0, v7_dir)

# V7 모듈 임포트
from graph import run_agent
from config import AGENT_CONFIG

#//==============================================================================//#
# 메인
#//==============================================================================//#

def main():
    st.header("🤖 AI Chatbot V7")
    st.caption("ReAct Agent - LLM이 도구를 동적으로 선택하는 지능형 Agent")

    # 세션 상태 초기화
    if 'v7_messages' not in st.session_state:
        st.session_state.v7_messages = []
    if 'v7_api_key' not in st.session_state:
        st.session_state.v7_api_key = ""

    # 사이드바
    show_sidebar()

    # API 키 입력
    if not st.session_state.v7_api_key:
        st.info("👋 시작하려면 먼저 OpenAI API 키를 입력해주세요")

        col1, col2 = st.columns([3, 1])
        with col1:
            api_key_input = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="GPT-4o를 사용하여 Agent를 실행합니다",
                key="api_key_input"
            )
        with col2:
            st.write("")  # 간격
            st.write("")  # 간격
            if st.button("✅ 설정", use_container_width=True, key="set_api_key"):
                if api_key_input and len(api_key_input) > 20:
                    st.session_state.v7_api_key = api_key_input
                    st.success("API 키가 설정되었습니다!")
                    st.rerun()
                else:
                    st.error("올바른 API 키를 입력하세요")

        return  # API 키 없으면 여기서 멈춤

    # 채팅 히스토리 표시
    for idx, msg in enumerate(st.session_state.v7_messages):
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

            # 생성된 이미지 표시
            if msg['role'] == 'assistant' and msg.get('images'):
                show_images(msg['images'])

            # Thought 표시 (선택적)
            if msg['role'] == 'assistant' and msg.get('thoughts'):
                show_thoughts(msg['thoughts'])

    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요 (예: 빌리프 보습력 어때?)"):

        # 사용자 메시지 추가
        st.session_state.v7_messages.append({
            'role': 'user',
            'content': prompt
        })

        with st.chat_message('user'):
            st.markdown(prompt)

        # AI 응답
        with st.chat_message('assistant'):
            with st.spinner('분석 중...'):

                # Thought 표시를 위한 placeholder
                thought_placeholder = st.empty()
                thoughts = []

                # V7 실행
                response = execute_v7_agent(
                    prompt,
                    st.session_state.v7_api_key,
                    thought_placeholder,
                    thoughts
                )

                # Thought 지우기 (최종 응답만 남김)
                thought_placeholder.empty()

                # 응답 표시
                st.markdown(response['text'])

                # 생성된 이미지
                if response.get('images'):
                    show_images(response['images'])

        # 응답 저장
        st.session_state.v7_messages.append({
            'role': 'assistant',
            'content': response['text'],
            'images': response.get('images'),
            'thoughts': thoughts if AGENT_CONFIG["show_thoughts"] else None
        })

        st.rerun()


def show_sidebar():
    """사이드바 UI"""

    with st.sidebar:
        st.markdown("### ⚙️ 설정")

        # API 키 상태 표시
        if st.session_state.v7_api_key:
            st.success("✅ API 키 설정됨")
            if st.button("🔄 API 키 변경", use_container_width=True):
                st.session_state.v7_api_key = ""
                st.rerun()
        else:
            st.info("메인 화면에서 API 키를 입력하세요")

        st.markdown("---")

        # 대화 초기화 버튼
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.v7_messages = []
            st.rerun()

        st.markdown("---")

        # 사용 통계
        st.markdown("### 📊 사용 통계")
        total_messages = len([m for m in st.session_state.v7_messages if m['role'] == 'user'])
        st.metric("총 질문", f"{total_messages}개")

        st.markdown("---")

        # 예시 질문
        st.markdown("### 💡 예시 질문")

        example_queries = [
            "빌리프 보습력 어때?",
            "VT랑 토리든 비교해줘",
            "최근 3개월 평점 추이 그래프로 보여줘",
            "복합성 피부 추천 제품"
        ]

        for query in example_queries:
            if st.button(f"💬 {query}", key=f"example_{query}", use_container_width=True):
                st.session_state.example_query = query
                st.rerun()

        st.markdown("---")

        # V7 특징 안내
        st.markdown("### 🆕 V7 특징")
        st.markdown("""
        - **ReAct Pattern**: LLM이 Tool 동적 선택
        - **State 기반**: Tool 간 데이터 자동 전달
        - **Adaptive Output**: 질문 의도에 맞는 답변
        - **Visualization**: 사용자 요청 시 차트 생성
        """)


def execute_v7_agent(user_query: str, api_key: str, thought_placeholder, thoughts: list) -> dict:
    """V7 Agent 실행"""

    try:
        # 환경변수에 API 키 설정
        os.environ["OPENAI_API_KEY"] = api_key

        # UI callback (Thought 표시)
        def ui_callback(data):
            if data.get("type") == "thought":
                thought_text = data.get("content", "")
                thoughts.append(thought_text)

                # 실시간 표시
                if AGENT_CONFIG.get("thought_display", {}).get("mode") == "hybrid":
                    with thought_placeholder.container():
                        with st.expander("💭 Agent의 생각 과정", expanded=False):
                            for thought in thoughts:
                                st.caption(thought)

        # V7 실행
        final_state = run_agent(user_query, ui_callback=ui_callback)

        # 최종 응답 추출
        final_response = final_state.get("final_response", "응답을 생성할 수 없습니다.")

        # 생성된 이미지 경로
        images = final_state.get("generated_images", [])

        return {
            "text": final_response,
            "images": images
        }

    except Exception as e:
        error_response = {
            "text": f"❌ 오류 발생: {str(e)}",
            "images": []
        }
        return error_response


def show_images(image_paths: list):
    """생성된 이미지 표시"""

    if not image_paths:
        return

    st.markdown("---")
    st.markdown("#### 📊 생성된 차트")

    for idx, img_path in enumerate(image_paths):
        if os.path.exists(img_path):
            st.image(img_path, caption=f"Chart #{idx+1}", use_container_width=True)
        else:
            st.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")


def show_thoughts(thoughts: list):
    """Agent의 생각 과정 표시"""

    if not thoughts:
        return

    with st.expander("💭 Agent의 생각 과정"):
        for thought in thoughts:
            st.caption(thought)


if __name__ == "__main__":
    main()
