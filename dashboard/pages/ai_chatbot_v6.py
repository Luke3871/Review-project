#//==============================================================================//#
"""
ai_chatbot_v6.py
V6 LangGraph Text-to-SQL 챗봇 페이지

last_updated : 2025.10.29
"""
#//==============================================================================//#

import streamlit as st
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(dashboard_dir)

# ai_engines 경로 추가
ai_engines_dir = os.path.join(dashboard_dir, 'ai_engines')
if ai_engines_dir not in sys.path:
    sys.path.insert(0, ai_engines_dir)

# V6 모듈 임포트
from v6_langgraph_agent.graph import create_graph
from v6_langgraph_agent.query_logger import QueryLogger
from v6_langgraph_agent.config import FEEDBACK_REASONS

#//==============================================================================//#
# 메인
#//==============================================================================//#

def main():
    st.header("🤖 AI Chatbot V6")
    st.caption("Text-to-SQL & AI Visual Agent (LangGraph)")

    # 세션 상태 초기화
    if 'v6_messages' not in st.session_state:
        st.session_state.v6_messages = []
    if 'v6_api_key' not in st.session_state:
        st.session_state.v6_api_key = ""
    if 'v6_logger' not in st.session_state:
        username = st.session_state.get('username', 'anonymous')
        st.session_state.v6_logger = QueryLogger(username=username)

    # 사이드바
    show_sidebar()

    # API 키 입력 (메인 화면 상단)
    if not st.session_state.v6_api_key:
        st.info("👋 시작하려면 먼저 OpenAI API 키를 입력해주세요")

        col1, col2 = st.columns([3, 1])
        with col1:
            api_key_input = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-...",
                help="GPT-4o-mini를 사용하여 SQL을 생성합니다",
                key="api_key_input"
            )
        with col2:
            st.write("")  # 간격
            st.write("")  # 간격
            if st.button("✅ 설정", use_container_width=True, key="set_api_key"):
                if api_key_input and len(api_key_input) > 20:
                    st.session_state.v6_api_key = api_key_input
                    st.success("API 키가 설정되었습니다!")
                    st.rerun()
                else:
                    st.error("올바른 API 키를 입력하세요")

        return  # API 키 없으면 여기서 멈춤

    # 채팅 히스토리 표시
    for idx, msg in enumerate(st.session_state.v6_messages):
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

            # 시각화가 있으면 표시
            if msg['role'] == 'assistant' and msg.get('visualizations'):
                show_visualizations(msg['visualizations'])

            # 테이블이 있으면 표시
            if msg['role'] == 'assistant' and msg.get('tables'):
                show_tables(msg['tables'])

            # 생성된 이미지 표시
            if msg['role'] == 'assistant' and msg.get('generated_images'):
                show_generated_images(msg['generated_images'])

            # 메타데이터 표시
            if msg['role'] == 'assistant' and msg.get('metadata'):
                show_metadata(msg['metadata'])

            # Debug 추적 정보 (Debug 모드일 때만, 히스토리)
            if msg['role'] == 'assistant' and st.session_state.get('v6_debug_mode', False) and msg.get('debug_traces'):
                show_debug_traces(msg['debug_traces'])

            # 피드백 버튼 (assistant 메시지에만)
            if msg['role'] == 'assistant' and msg.get('log_id'):
                show_feedback_buttons(msg['log_id'], idx)

    # 사용자 입력
    if prompt := st.chat_input("질문을 입력하세요 (예: 빌리프 보습력 어때?)"):

        # 사용자 메시지 추가
        st.session_state.v6_messages.append({
            'role': 'user',
            'content': prompt
        })

        with st.chat_message('user'):
            st.markdown(prompt)

        # AI 응답
        with st.chat_message('assistant'):
            with st.spinner('분석 중...'):

                # 진행상황 표시를 위한 placeholder
                progress_placeholder = st.empty()

                # V6 실행
                response = execute_v6_agent(
                    prompt,
                    st.session_state.v6_api_key,
                    progress_placeholder
                )

                # 진행상황 지우기
                progress_placeholder.empty()

                # 응답 표시
                response_text = response.get('text', '응답을 생성하지 못했습니다.')
                st.markdown(response_text)

                # 시각화
                if response.get('visualizations'):
                    show_visualizations(response['visualizations'])

                # 시각화 제안 (suggest 전략)
                if response.get('visualization_suggestions'):
                    show_visualization_suggestions(response['visualization_suggestions'])

                # 테이블
                if response.get('tables'):
                    show_tables(response['tables'])

                # 생성된 이미지
                if response.get('generated_images'):
                    show_generated_images(response['generated_images'])

                # 메타데이터
                if response.get('metadata'):
                    show_metadata(response['metadata'])

                # Debug 추적 정보 (Debug 모드일 때만)
                if st.session_state.get('v6_debug_mode', False) and response.get('debug_traces'):
                    show_debug_traces(response['debug_traces'])

        # 응답 저장
        st.session_state.v6_messages.append({
            'role': 'assistant',
            'content': response.get('text', '응답을 생성하지 못했습니다.'),
            'visualizations': response.get('visualizations'),
            'tables': response.get('tables'),
            'generated_images': response.get('generated_images'),
            'metadata': response.get('metadata'),
            'debug_traces': response.get('debug_traces'),  # Debug 추적 정보
            'log_id': response.get('log_id')
        })

        st.rerun()


def show_sidebar():
    """사이드바 UI"""

    with st.sidebar:
        st.markdown("### ⚙️ 설정")

        # API 키 상태 표시
        if st.session_state.v6_api_key:
            st.success("✅ API 키 설정됨")
            if st.button("🔄 API 키 변경", use_container_width=True):
                st.session_state.v6_api_key = ""
                st.rerun()
        else:
            st.info("메인 화면에서 API 키를 입력하세요")

        st.markdown("---")

        # Debug 모드 토글 (Phase 2: UI 피드백 개선)
        debug_mode = st.checkbox(
            "🔧 Debug 모드 (개발자용)",
            value=st.session_state.get('v6_debug_mode', False),
            help="LLM 프롬프트와 응답을 추적합니다"
        )
        st.session_state.v6_debug_mode = debug_mode

        if debug_mode:
            st.info("💡 Debug 모드 활성화: 답변 하단에 LLM 추적 정보가 표시됩니다")

        st.markdown("---")

        # 대화 초기화 버튼
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.v6_messages = []
            st.rerun()

        st.markdown("---")

        # 사용 통계
        st.markdown("### 📊 사용 통계")

        logger = st.session_state.v6_logger
        stats = logger.get_statistics()

        if stats.get('total_queries', 0) > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 질문", f"{stats['total_queries']}개")
            with col2:
                st.metric("평균 시간", f"{stats['avg_duration']}초")

            # 피드백 통계
            feedback_stats = logger.get_feedback_statistics()
            if feedback_stats.get('satisfaction_rate', 0) > 0:
                st.metric(
                    "만족도",
                    f"{feedback_stats['satisfaction_rate']}%",
                    delta=f"{feedback_stats['positive_count']}👍 {feedback_stats['negative_count']}👎"
                )
        else:
            st.info("아직 질문 기록이 없습니다")

        st.markdown("---")

        # 예시 질문
        st.markdown("### 💡 예시 질문")

        example_queries = [
            "빌리프 보습력 어때?",
            "VT랑 토리든 비교해줘",
            "올리브영 평점 높은 제품은?",
            "최근 3개월 인기 제품 보여줘",
            "복합성 피부 추천 제품"
        ]

        for query in example_queries:
            if st.button(f"💬 {query}", key=f"example_{query}", use_container_width=True):
                # 직접 입력창에 넣기
                st.session_state.example_query = query
                st.rerun()


def execute_v6_agent(user_query: str, api_key: str, progress_placeholder) -> dict:
    """V6 Agent 실행"""

    try:
        # 환경변수에 API 키 설정 (OpenAI 클라이언트가 자동으로 읽음)
        import os
        os.environ["OPENAI_API_KEY"] = api_key

        # LangGraph 생성
        graph = create_graph()

        # 진행상황 콜백
        def update_progress(progress_text):
            progress_placeholder.markdown(progress_text)

        # 대화 히스토리 구성 (최근 10개 메시지 = 5턴)
        conversation_history = []
        if 'v6_messages' in st.session_state:
            # 마지막 10개 메시지만 사용 (user + assistant 쌍 5개)
            recent_messages = st.session_state.v6_messages[-10:]
            for msg in recent_messages:
                conversation_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # 초기 상태
        initial_state = {
            "user_query": user_query,
            "ui_callback": update_progress,
            "debug_mode": st.session_state.get('v6_debug_mode', False),  # Debug 모드 전달
            "conversation_history": conversation_history,  # 대화 히스토리 전달
            "messages": [],
            "error": None
        }

        # 디버깅: Graph 실행 시작
        print(f"\n[DEBUG] ===== Graph 실행 시작 =====")
        print(f"[DEBUG] Graph - user_query: {user_query}")
        print(f"[DEBUG] Graph - conversation_history: {len(conversation_history)}개 메시지")

        # 실행
        final_state = graph.invoke(initial_state)

        # 디버깅: Graph 실행 완료
        print(f"[DEBUG] ===== Graph 실행 완료 =====")
        print(f"[DEBUG] Graph - final_state keys: {list(final_state.keys())}")
        print(f"[DEBUG] Graph - error: {final_state.get('error')}")
        print(f"[DEBUG] Graph - final_response 존재: {'final_response' in final_state}")
        if 'final_response' in final_state:
            fr = final_state['final_response']
            print(f"[DEBUG] Graph - final_response type: {type(fr)}")
            if isinstance(fr, dict):
                print(f"[DEBUG] Graph - final_response keys: {list(fr.keys())}")

        # 최종 응답
        final_response = final_state.get("final_response", {})

        # 로그 저장
        logger = st.session_state.v6_logger
        logger.log_query(
            user_query=user_query,
            state=final_state,
            final_response=final_response,
            error=final_state.get("error")
        )

        # 최근 로그 ID 가져오기 (피드백용)
        history = logger.get_user_history(limit=1)
        log_id = history[0]['log_id'] if history else None

        # 응답에 log_id 추가
        final_response['log_id'] = log_id

        # Debug 모드 추적 정보 추가
        if st.session_state.get('v6_debug_mode', False):
            final_response['debug_traces'] = final_state.get('debug_traces', [])

        return final_response

    except Exception as e:
        # 예외 발생 시에도 로그 저장
        logger = st.session_state.v6_logger
        error_info = {"exception": str(e), "type": type(e).__name__}

        logger.log_query(
            user_query=user_query,
            state={"error": error_info, "messages": []},
            final_response={"text": f"오류 발생: {str(e)}"},
            error=error_info
        )

        error_response = {
            "text": f"❌ 오류 발생: {str(e)}",
            "visualizations": None,
            "tables": None,
            "metadata": {"error": str(e)},
            "log_id": None
        }
        return error_response


def show_visualizations(visualizations: list):
    """시각화 표시"""

    if not visualizations:
        return

    st.markdown("---")
    st.markdown("#### 📈 시각화")

    for viz in visualizations:
        viz_type = viz.get('type')
        figure = viz.get('figure')

        if figure:
            if viz_type == 'wordcloud':
                # Matplotlib figure
                st.pyplot(figure, use_container_width=False)
            else:
                # Plotly figure
                st.plotly_chart(figure, use_container_width=False)


def show_tables(tables: dict):
    """테이블 표시"""

    if not tables:
        return

    st.markdown("---")
    st.markdown("#### 📋 데이터")

    for table_name, table_data in tables.items():
        if table_data:
            st.markdown(f"**{table_name}**")

            import pandas as pd
            df = pd.DataFrame(table_data['data'], columns=table_data['columns'])
            st.dataframe(df, use_container_width=True, hide_index=True)


def show_visualization_suggestions(suggestions: list):
    """시각화 제안 표시"""

    if not suggestions:
        return

    st.markdown("---")
    st.markdown("#### 💡 시각화 제안")
    st.info("다음 시각화 옵션을 사용할 수 있습니다:")

    # 제안 타입별 안내 메시지
    viz_labels = {
        "line_chart": "📈 라인 차트 (시계열 트렌드)",
        "bar_chart": "📊 막대 차트 (비교 분석)",
        "wordcloud": "☁️ 워드클라우드 (키워드 분석)"
    }

    cols = st.columns(len(suggestions))
    for i, viz_type in enumerate(suggestions):
        with cols[i]:
            label = viz_labels.get(viz_type, viz_type)
            st.button(
                label,
                key=f"viz_suggest_{viz_type}",
                use_container_width=True,
                disabled=True  # 일단 비활성화 (나중에 클릭 시 시각화 생성 기능 추가)
            )

    st.caption("💬 시각화가 필요하시면 '워드클라우드 보여줘' 같이 명시적으로 요청해주세요!")


def show_metadata(metadata: dict):
    """메타데이터 표시"""

    if not metadata:
        return

    with st.expander("ℹ️ 실행 정보"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("처리 시간", f"{metadata.get('total_duration', 0):.2f}초")
        with col2:
            st.metric("복잡도", metadata.get('complexity', 'unknown'))
        with col3:
            st.metric("SQL 쿼리", f"{metadata.get('total_queries', 0)}개")

        # 추가 정보
        if metadata.get('total_data_rows'):
            st.write(f"📊 분석 데이터: {metadata['total_data_rows']:,}개 리뷰")

        if metadata.get('visualization_confidence'):
            st.write(f"🎨 시각화 신뢰도: {metadata['visualization_confidence']:.0%}")

        # SQL 쿼리 표시 (새로 추가)
        sql_queries = metadata.get('sql_queries', [])
        if sql_queries:
            st.markdown("---")
            st.markdown("### 📋 생성된 SQL 쿼리")

            for i, sql_meta in enumerate(sql_queries, 1):
                purpose = sql_meta.get('purpose', f'Query {i}')
                with st.expander(f"Q{i}: {purpose}", expanded=False):
                    st.code(sql_meta.get('sql', ''), language='sql')

                    # 부가 정보
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.caption(f"💡 {sql_meta.get('explanation', '')}")
                    with col_b:
                        st.caption(f"📊 예상 결과: {sql_meta.get('estimated_rows', 0)}건")


def show_feedback_buttons(log_id: int, message_idx: int):
    """피드백 버튼"""

    # 이미 피드백을 남긴 경우 체크
    feedback_key = f"feedback_{log_id}"
    if feedback_key in st.session_state:
        st.success(f"✅ 피드백 완료: {st.session_state[feedback_key]}")
        return

    st.markdown("---")
    st.markdown("**이 답변이 도움이 되었나요?**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍 좋아요", key=f"pos_{log_id}_{message_idx}", use_container_width=True):
            show_feedback_dialog(log_id, "positive")

    with col2:
        if st.button("👎 별로예요", key=f"neg_{log_id}_{message_idx}", use_container_width=True):
            show_feedback_dialog(log_id, "negative")


def show_feedback_dialog(log_id: int, feedback_type: str):
    """피드백 상세 입력"""

    # 모달 대신 expander 사용
    with st.expander("📝 피드백 작성", expanded=True):

        # 이유 선택
        reasons = FEEDBACK_REASONS[feedback_type]
        selected_reason = st.selectbox(
            "이유를 선택해주세요",
            reasons,
            key=f"reason_{log_id}"
        )

        # 추가 코멘트
        comment = st.text_area(
            "추가 의견 (선택)",
            placeholder="개선이 필요한 부분이나 좋았던 점을 알려주세요",
            key=f"comment_{log_id}"
        )

        # 제출 버튼
        if st.button("제출", key=f"submit_{log_id}"):
            logger = st.session_state.v6_logger
            success = logger.save_feedback(
                log_id=log_id,
                feedback=feedback_type,
                reason=selected_reason,
                comment=comment if comment else None
            )

            if success:
                st.session_state[f"feedback_{log_id}"] = "👍 좋아요" if feedback_type == "positive" else "👎 별로예요"
                st.success("피드백이 저장되었습니다. 감사합니다!")
                st.rerun()
            else:
                st.error("피드백 저장에 실패했습니다.")


def show_generated_images(generated_images: list):
    """생성된 이미지 표시 (AI Visual Agent)"""

    if not generated_images:
        return

    st.markdown("---")
    st.markdown("#### 🎨 생성된 디자인 시안")

    for idx, img_data in enumerate(generated_images):
        local_path = img_data.get('local_path')
        revised_prompt = img_data.get('revised_prompt')
        timestamp = img_data.get('timestamp', '')

        # 이미지 표시
        if local_path and os.path.exists(local_path):
            st.image(local_path, caption=f"Daiso 채널 최적화 디자인 #{idx+1}", width=700)

            # 상세 정보 (expander)
            with st.expander(f"📝 디자인 #{idx+1} 상세 정보"):
                st.markdown(f"**생성 시간:** {timestamp}")
                st.markdown(f"**파일 경로:** `{local_path}`")

                if revised_prompt:
                    st.markdown("**Gemini Prompt:**")
                    st.code(revised_prompt, language="text")
        else:
            st.warning(f"이미지 파일을 찾을 수 없습니다: {local_path}")


def show_debug_traces(debug_traces: list):
    """Debug 추적 정보 표시 (개발자용)"""

    if not debug_traces:
        return

    with st.expander("🔧 Debug 추적 정보 (개발자용)", expanded=False):
        st.caption("LLM 프롬프트와 응답을 추적합니다")

        for i, trace in enumerate(debug_traces, 1):
            node = trace.get('node', 'Unknown')
            step = trace.get('step', 'Unknown')

            st.markdown(f"### Trace {i}: {node} - {step}")

            # 프롬프트 표시
            if trace.get('prompt'):
                with st.expander("📝 LLM 프롬프트", expanded=False):
                    prompt_text = trace['prompt']
                    # 너무 길면 잘라내기
                    if len(prompt_text) > 2000:
                        st.text(prompt_text[:2000] + "\n\n... (truncated)")
                    else:
                        st.text(prompt_text)

            # LLM 응답 표시
            if trace.get('llm_response'):
                with st.expander("💬 LLM 원본 응답", expanded=False):
                    response_text = trace['llm_response']
                    # 너무 길면 잘라내기
                    if len(response_text) > 2000:
                        st.text(response_text[:2000] + "\n\n... (truncated)")
                    else:
                        st.text(response_text)

            # 파싱된 결과 (있으면)
            if trace.get('parsed_result'):
                with st.expander("✅ 파싱된 결과", expanded=False):
                    st.json(trace['parsed_result'])

            st.markdown("---")


if __name__ == "__main__":
    main()
