#//==============================================================================//#
"""
ai_chat.py
AI 분석 챗봇 페이지 - 3가지 버전 비교

- V1: Rule-based Report (통계 기반 규칙)
- V2: Multi-Agent System (Planning → Execution → Response)
- V3: Playbook-based Agent (재사용 패턴 + ReAct)

last_updated: 2025.10.26
"""
#//==============================================================================//#

import streamlit as st
import sys
import os

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))  # pages 폴더
dashboard_dir = os.path.dirname(current_dir)  # dashboard 폴더
project_root = os.path.dirname(dashboard_dir)  # ReviewFW_LG_hnh 폴더

# dashboard 경로 추가
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

# analytics 경로 추가
analytics_dir = os.path.join(project_root, 'analytics')
if analytics_dir not in sys.path:
    sys.path.insert(0, analytics_dir)

from dashboard_config import (
    load_filtered_data,
    get_available_channels,
    get_brand_list,
    get_product_list,
    PERIOD_OPTIONS
)

#//==============================================================================//#
# 설정
#//==============================================================================//#

DB_CONFIG = {
    "dbname": os.getenv('DB_NAME', 'cosmetic_reviews'),
    "user": os.getenv('DB_USER', 'postgres'),
    "password": os.getenv('DB_PASSWORD', 'postgres'),
    "host": os.getenv('DB_HOST', 'localhost'),
    "port": int(os.getenv('DB_PORT', 5432))
}

#//==============================================================================//#
# 메인
#//==============================================================================//#

def main():
    st.header("🤖 AI 분석 엔진 - 이전 모델")
    st.caption("V1 ~ V5 모델 히스토리")

    # 5개 탭
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "V1: 규칙 기반",
        "V2: LLM",
        "V3: Multi-Agent",
        "V4: ReAct",
        "V5: LangGraph"
    ])

    with tab1:
        render_v1_rulebased()

    with tab2:
        render_v2_llm_report()

    with tab3:
        render_v3_multiagent()

    with tab4:
        render_v4_playbook()

    with tab5:
        render_v5_langgraph()

#//==============================================================================//#
# V1: Rule-based Report
#//==============================================================================//#

def render_v1_rulebased():
    """V1: 규칙 기반 보고서"""

    st.subheader("V1: 규칙 기반 인사이트 생성")
    st.caption("통계 분석 + 조건문 규칙으로 인사이트 자동 생성")

    # 필터 초기화
    if 'v1_selected_channel' not in st.session_state:
        st.session_state.v1_selected_channel = None
    if 'v1_selected_brand' not in st.session_state:
        st.session_state.v1_selected_brand = None
    if 'v1_selected_product' not in st.session_state:
        st.session_state.v1_selected_product = None

    # 필터 UI
    st.markdown("#### 📍 제품 선택")

    col1, col2, col3 = st.columns(3)

    with col1:
        channels = get_available_channels()
        if channels:
            if st.session_state.v1_selected_channel not in channels:
                st.session_state.v1_selected_channel = channels[0]

            selected_channel = st.selectbox(
                "채널",
                channels,
                index=channels.index(st.session_state.v1_selected_channel),
                key="v1_channel"
            )
            st.session_state.v1_selected_channel = selected_channel

    with col2:
        brands = get_brand_list(st.session_state.v1_selected_channel)
        if brands:
            if st.session_state.v1_selected_brand not in brands:
                st.session_state.v1_selected_brand = brands[0]

            selected_brand = st.selectbox(
                "브랜드",
                brands,
                index=brands.index(st.session_state.v1_selected_brand),
                key="v1_brand"
            )
            st.session_state.v1_selected_brand = selected_brand

    with col3:
        products = get_product_list(
            st.session_state.v1_selected_channel,
            st.session_state.v1_selected_brand
        )
        if products:
            if st.session_state.v1_selected_product not in products:
                st.session_state.v1_selected_product = products[0]

            selected_product = st.selectbox(
                "제품",
                products,
                index=products.index(st.session_state.v1_selected_product),
                key="v1_product"
            )
            st.session_state.v1_selected_product = selected_product

    # 보고서 생성 버튼
    if st.button("📊 분석 보고서 생성", type="primary", use_container_width=True, key="v1_generate"):

        with st.spinner("보고서 생성 중..."):
            # 데이터 로드
            df = load_filtered_data(
                channel=st.session_state.v1_selected_channel,
                brand=st.session_state.v1_selected_brand,
                product=st.session_state.v1_selected_product
            )

            if df.empty:
                st.error("선택한 제품의 리뷰 데이터가 없습니다.")
                return

            # V1 보고서 생성
            try:
                from ai_engines.v1_rulebased import generate_product_report

                report = generate_product_report(
                    df,
                    st.session_state.v1_selected_channel
                )

                # 보고서 표시
                display_v1_report(report)

            except Exception as e:
                st.error(f"보고서 생성 중 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())

def display_v1_report(report):
    """V1 보고서 표시"""

    basic_info = report.get('basic_info', {})
    satisfaction = report.get('satisfaction', {})
    keywords = report.get('keywords', {})
    trend = report.get('trend', {})
    insights = report.get('insights', [])

    # 제목
    product_name = basic_info.get('product_name', 'N/A')
    st.markdown(f"# {product_name}")
    st.caption(f"분석 보고서 | {report.get('generated_at', '')}")

    st.markdown("---")

    # 1. 제품 개요
    st.markdown("## 📋 제품 개요")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 리뷰", f"{basic_info.get('total_reviews', 0):,}개")
    col2.metric("채널", basic_info.get('channel', 'N/A'))
    col3.metric("브랜드", basic_info.get('brand', 'N/A'))
    col4.metric("가격", basic_info.get('price', 'N/A'))

    # 추가 정보
    st.caption(f"📂 카테고리: {basic_info.get('category', 'N/A')}")
    st.caption(f"📅 리뷰 기간: {basic_info.get('date_range', 'N/A')}")
    if basic_info.get('sort_type') != 'N/A':
        st.caption(f"🏷️ 정렬 기준: {basic_info.get('sort_type', 'N/A')}")

    st.markdown("---")

    # 2. 고객 만족도
    if satisfaction:
        st.markdown("## ⭐ 고객 만족도")

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "긍정 리뷰",
            f"{satisfaction['positive_ratio']}%",
            f"{satisfaction['positive_count']:,}개"
        )
        col2.metric(
            "부정 리뷰",
            f"{satisfaction['negative_ratio']}%",
            f"{satisfaction['negative_count']:,}개"
        )
        col3.metric("평균 평점", f"{satisfaction['avg_rating']}/5.0")

        # 평점 분포
        import plotly.express as px

        rating_dist = satisfaction.get('rating_distribution', {})
        if rating_dist:
            fig = px.bar(
                x=list(rating_dist.keys()),
                y=list(rating_dist.values()),
                title="평점 분포",
                labels={'x': '평점', 'y': '리뷰 수'},
                text=list(rating_dist.values())
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

    # 3. 키워드 분석
    if keywords:
        st.markdown("## 💬 주요 키워드")

        # 전체 키워드 (긍정/부정 구분 없이)
        overall_keywords = keywords.get('overall_top10', [])
        if overall_keywords:
            st.markdown("### 📊 전체 키워드 TOP 10")

            # 2열로 표시
            col1, col2 = st.columns(2)

            with col1:
                for i, (kw, freq) in enumerate(overall_keywords[:5], 1):
                    st.markdown(f"{i}. **{kw}** ({freq}회)")

            with col2:
                for i, (kw, freq) in enumerate(overall_keywords[5:], 6):
                    st.markdown(f"{i}. **{kw}** ({freq}회)")

            st.markdown("---")

        # 긍정/부정 키워드
        positive_keywords = keywords.get('positive_top5', [])
        negative_keywords = keywords.get('negative_top5', [])

        if positive_keywords or negative_keywords:
            st.markdown("### 🔍 감정별 키워드 분석")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**✅ 긍정 키워드 TOP 5**")
                if positive_keywords:
                    for i, (kw, freq) in enumerate(positive_keywords, 1):
                        st.markdown(f"{i}. **{kw}** ({freq}회)")
                else:
                    st.info("긍정 키워드 없음 (부정 리뷰만 존재)")

            with col2:
                st.markdown("**❌ 부정 키워드 TOP 5**")
                if negative_keywords:
                    for i, (kw, freq) in enumerate(negative_keywords, 1):
                        st.markdown(f"{i}. **{kw}** ({freq}회)")
                else:
                    st.info("부정 키워드 없음 (긍정 리뷰만 존재)")

        st.markdown("---")

    # 4. 트렌드 요약
    if trend:
        st.markdown("## 📈 트렌드 요약")

        col1, col2, col3 = st.columns(3)
        col1.metric("최고 리뷰 달", trend.get('peak_month', 'N/A'), f"{trend.get('peak_count', 0)}개")
        col2.metric("최근 리뷰 달", trend.get('recent_month', 'N/A'), f"{trend.get('recent_count', 0)}개")
        col3.metric("최근 트렌드", trend.get('trend_direction', 'N/A'))

        st.markdown("---")

    # 5. 핵심 인사이트 (규칙 기반)
    st.markdown("## 💡 핵심 인사이트")

    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("생성된 인사이트가 없습니다.")

    st.markdown("---")

    # 보고서 정보
    st.caption(f"📊 V1 Rule-based Report | {report.get('generated_at', '')}")
    st.caption(f"📦 데이터 출처: {basic_info.get('channel', 'N/A')}")

#//==============================================================================//#
# V2: LLM Report
#//==============================================================================//#

def render_v2_llm_report():
    """V2: LLM 기반 보고서"""

    st.subheader("V2: LLM 기반 인사이트 생성")
    st.caption("GPT를 활용한 비즈니스 인사이트 자동 생성")

    # 필터 초기화
    if 'v2_selected_channel' not in st.session_state:
        st.session_state.v2_selected_channel = None
    if 'v2_selected_brand' not in st.session_state:
        st.session_state.v2_selected_brand = None
    if 'v2_selected_product' not in st.session_state:
        st.session_state.v2_selected_product = None
    if 'v2_api_key' not in st.session_state:
        st.session_state.v2_api_key = ""

    # API 키 입력
    st.markdown("#### 🔑 API 설정")
    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.v2_api_key,
        type="password",
        help="GPT 분석을 위해 OpenAI API 키가 필요합니다",
        key="v2_api_input"
    )
    st.session_state.v2_api_key = api_key

    if not api_key:
        st.warning("⚠️ API 키를 입력해야 LLM 보고서를 생성할 수 있습니다.")
    else:
        st.success("✅ API 키 설정 완료")

    st.markdown("---")

    # 필터 UI
    st.markdown("#### 📍 제품 선택")

    col1, col2, col3 = st.columns(3)

    with col1:
        channels = get_available_channels()
        if channels:
            if st.session_state.v2_selected_channel not in channels:
                st.session_state.v2_selected_channel = channels[0]

            selected_channel = st.selectbox(
                "채널",
                channels,
                index=channels.index(st.session_state.v2_selected_channel),
                key="v2_channel"
            )
            st.session_state.v2_selected_channel = selected_channel

    with col2:
        brands = get_brand_list(st.session_state.v2_selected_channel)
        if brands:
            if st.session_state.v2_selected_brand not in brands:
                st.session_state.v2_selected_brand = brands[0]

            selected_brand = st.selectbox(
                "브랜드",
                brands,
                index=brands.index(st.session_state.v2_selected_brand),
                key="v2_brand"
            )
            st.session_state.v2_selected_brand = selected_brand

    with col3:
        products = get_product_list(
            st.session_state.v2_selected_channel,
            st.session_state.v2_selected_brand
        )
        if products:
            if st.session_state.v2_selected_product not in products:
                st.session_state.v2_selected_product = products[0]

            selected_product = st.selectbox(
                "제품",
                products,
                index=products.index(st.session_state.v2_selected_product),
                key="v2_product"
            )
            st.session_state.v2_selected_product = selected_product

    # LLM 보고서 생성 버튼 (2가지 방식)
    st.markdown("#### 🤖 AI 분석 실행")

    col1, col2 = st.columns(2)

    with col1:
        v2a_button = st.button(
            "📊 V2-A: 데이터 직접 분석",
            type="primary",
            use_container_width=True,
            key="v2a_generate",
            help="리뷰 데이터를 GPT가 직접 분석하여 비즈니스 인사이트 생성"
        )

    with col2:
        v2b_button = st.button(
            "🔑 V2-B: 키워드 해석 분석",
            type="primary",
            use_container_width=True,
            key="v2b_generate",
            help="키워드를 먼저 추출한 후 GPT가 해석 및 조언 생성"
        )

    # V2-A 실행
    if v2a_button:

        if not st.session_state.v2_api_key:
            st.error("먼저 API 키를 입력하세요.")
            return

        with st.spinner("AI가 데이터를 분석하고 인사이트를 생성하고 있습니다..."):
            # 데이터 로드
            df = load_filtered_data(
                channel=st.session_state.v2_selected_channel,
                brand=st.session_state.v2_selected_brand,
                product=st.session_state.v2_selected_product
            )

            if df.empty:
                st.error("선택한 제품의 리뷰 데이터가 없습니다.")
                return

            # V2 LLM 보고서 생성
            try:
                from ai_engines.v2_llm_report import generate_llm_report

                report = generate_llm_report(
                    df,
                    st.session_state.v2_selected_channel,
                    st.session_state.v2_api_key
                )

                # 보고서 표시
                display_v2_report(report)

            except Exception as e:
                st.error(f"LLM 보고서 생성 중 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())

    # V2-B 실행
    if v2b_button:

        if not st.session_state.v2_api_key:
            st.error("먼저 API 키를 입력하세요.")
            return

        with st.spinner("키워드를 추출하고 AI가 해석하고 있습니다..."):
            # 데이터 로드
            df = load_filtered_data(
                channel=st.session_state.v2_selected_channel,
                brand=st.session_state.v2_selected_brand,
                product=st.session_state.v2_selected_product
            )

            if df.empty:
                st.error("선택한 제품의 리뷰 데이터가 없습니다.")
                return

            # V2-B 키워드 해석 분석
            try:
                # 1. 먼저 키워드 추출
                from ai_engines.v1_rulebased.keyword_analyzer import extract_overall_keywords

                keywords = extract_overall_keywords(df, st.session_state.v2_selected_channel)

                if not keywords:
                    st.error("키워드 추출에 실패했습니다.")
                    return

                # 2. GPT로 키워드 해석
                from ai_engines.v2_llm_report.keyword_interpreter import generate_keyword_interpretation

                report = generate_keyword_interpretation(
                    df,
                    keywords,
                    st.session_state.v2_selected_channel,
                    st.session_state.v2_api_key
                )

                # 보고서 표시
                display_v2b_report(report, keywords)

            except Exception as e:
                st.error(f"키워드 해석 분석 중 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())


def display_v2_report(report):
    """V2 LLM 보고서 표시"""

    if not report:
        st.error("보고서 생성 실패")
        return

    # 에러 처리
    if 'error' in report and report['error']:
        st.error(f"AI 분석 오류: {report['error']}")
        return

    # 제목
    product_name = report.get('product_name', 'N/A')
    brand = report.get('brand', 'N/A')
    channel = report.get('channel', 'N/A')

    st.markdown(f"# 🤖 AI 분석 보고서")
    st.markdown(f"## {brand} - {product_name}")
    st.caption(f"생성일시: {report.get('generated_at', '')} | 채널: {channel}")

    st.markdown("---")

    # 1. 데이터 요약
    summary = report.get('summary')
    if summary:
        st.markdown("## 📊 데이터 요약")
        st.markdown(summary)
        st.markdown("---")

    # 2. AI 인사이트
    insights = report.get('insights')
    if insights:
        st.markdown("## 💡 AI 생성 인사이트")
        st.markdown(insights)
    else:
        st.warning("AI 인사이트를 생성하지 못했습니다.")

    st.markdown("---")

    # 보고서 정보
    st.caption(f"🤖 V2-A LLM Report (GPT-4o-mini) | {report.get('generated_at', '')}")
    st.caption(f"📦 데이터 출처: {channel}")


def display_v2b_report(report, keywords):
    """V2-B 키워드 해석 보고서 표시"""

    if not report:
        st.error("보고서 생성 실패")
        return

    # 에러 처리
    if 'error' in report and report['error']:
        st.error(f"AI 분석 오류: {report['error']}")
        return

    # 제목
    product_name = report.get('product_name', 'N/A')
    brand = report.get('brand', 'N/A')
    channel = report.get('channel', 'N/A')

    st.markdown(f"# 🔑 AI 키워드 해석 보고서")
    st.markdown(f"## {brand} - {product_name}")
    st.caption(f"생성일시: {report.get('generated_at', '')} | 채널: {channel}")

    st.markdown("---")

    # 1. 기본 정보
    st.markdown("## 📊 분석 기본 정보")

    col1, col2, col3 = st.columns(3)
    col1.metric("총 리뷰 수", f"{report.get('total_reviews', 0):,}개")
    col2.metric("평균 평점", f"{report.get('avg_rating', 0):.2f}/5.0")
    col3.metric("긍정 비율", f"{report.get('positive_ratio', 0):.1f}%")

    st.markdown("---")

    # 2. 추출된 키워드 TOP 20
    st.markdown("## 🔑 추출된 키워드 TOP 20")

    keywords_summary = report.get('keywords_summary', [])
    if keywords_summary:
        # 디버깅: 키워드 개수 확인
        st.caption(f"총 {len(keywords_summary)}개 키워드")
        # 테이블 형태로 표시
        import pandas as pd

        # 키워드 데이터 파싱 (형식: "키워드: 점수")
        keyword_data = []
        for i, kw_str in enumerate(keywords_summary[:20], 1):
            if ':' in kw_str:
                keyword, score = kw_str.split(':', 1)
                keyword_data.append({
                    '순위': i,
                    '키워드': keyword.strip(),
                    '중요도': float(score.strip())
                })
            else:
                keyword_data.append({
                    '순위': i,
                    '키워드': kw_str.strip(),
                    '중요도': 0.0
                })

        # DataFrame 생성
        df_keywords = pd.DataFrame(keyword_data)

        # 2열로 나눠서 표시
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**1-10위**")
            st.dataframe(
                df_keywords.iloc[:10],
                use_container_width=True,
                hide_index=True
            )

        with col2:
            st.markdown("**11-20위**")
            st.dataframe(
                df_keywords.iloc[10:20],
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("키워드 요약 없음")

    st.markdown("---")

    # 3. AI 해석
    interpretation = report.get('interpretation')
    if interpretation:
        st.markdown("## 💡 AI 키워드 해석 및 조언")
        st.markdown(interpretation)
    else:
        st.warning("AI 해석을 생성하지 못했습니다.")

    st.markdown("---")

    # 보고서 정보
    st.caption(f"🔑 V2-B Keyword Interpretation Report (GPT-4o-mini) | {report.get('generated_at', '')}")
    st.caption(f"📦 데이터 출처: {channel}")

#//==============================================================================//#
# V3: Multi-Agent
#//==============================================================================//#

def render_v3_multiagent():
    """V3: Multi-Agent System (챗봇 스타일)"""

    st.subheader("V3: Multi-Agent System")
    st.caption("PlanningAgent → ExecutionAgent → ResponseAgent (벡터 검색 + 필터 검색)")

    st.markdown("""
    ### 💡 동작 방식
    1. **PlanningAgent**: GPT가 사용자 질문을 분석하여 실행 계획 생성
    2. **ExecutionAgent**: 계획에 따라 PostgreSQL + pgvector 검색 (BGE-M3 임베딩)
    3. **ResponseAgent**: GPT가 검색 결과를 자연어 답변으로 변환

    ### 📝 예시 질문
    - "VT 시카크림 보습력 어때?" (벡터 검색)
    - "올리브영 평점 높은 제품은?" (필터 검색 + 통계)
    - "최근 3개월 토리든 평가는?" (벡터 검색 + 날짜 필터)
    - "복합성 피부에 좋은 제품" (필터 검색 + 피부 타입)
    """)

    st.markdown("---")

    # API 키 입력 (세션 상태)
    if 'v3_api_key' not in st.session_state:
        st.session_state.v3_api_key = ""

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.v3_api_key,
        type="password",
        help="Planning Agent와 Response Agent에서 GPT-4o-mini 사용",
        key="v3_api_input"
    )

    if api_key:
        st.session_state.v3_api_key = api_key
        st.success("✅ API 키 설정 완료")
    else:
        st.warning("⚠️ API 키를 입력하세요")

    st.markdown("---")

    # 채팅 히스토리 초기화
    if 'v3_messages' not in st.session_state:
        st.session_state.v3_messages = []

    # 이전 메시지 표시
    for msg in st.session_state.v3_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # 사용자 입력 (챗봇 스타일)
    if prompt := st.chat_input("질문을 입력하세요 (예: VT 시카크림 보습력 어때?)"):

        if not st.session_state.v3_api_key:
            st.error("❌ 먼저 API 키를 입력하세요")
            return

        # 사용자 메시지 추가
        st.session_state.v3_messages.append({'role': 'user', 'content': prompt})

        with st.chat_message('user'):
            st.markdown(prompt)

        # AI 응답
        with st.chat_message('assistant'):
            with st.spinner('🤖 Multi-Agent 시스템 분석 중...'):
                try:
                    from ai_engines.v3_multi_agent import Orchestrator

                    orchestrator = Orchestrator(st.session_state.v3_api_key)
                    result = orchestrator.process_query(prompt)

                    # 답변 표시
                    st.markdown(result['answer'])

                    # 디버그 정보 (Expander)
                    with st.expander("🔍 실행 계획 보기"):
                        st.json(result['plan'])

                    with st.expander("📁 실행 결과 보기"):
                        if result['results']:
                            if result['results'].get('reviews') is not None:
                                reviews = result['results']['reviews']
                                if not reviews.empty:
                                    st.write(f"검색된 리뷰: {len(reviews)}개")
                                    st.dataframe(reviews.head(10))

                            if result['results'].get('stats'):
                                st.write("통계 정보:")
                                st.json(result['results']['stats'])

                    # 응답 저장
                    st.session_state.v3_messages.append({
                        'role': 'assistant',
                        'content': result['answer']
                    })

                except Exception as e:
                    error_msg = f"❌ 오류 발생: {e}"
                    st.error(error_msg)
                    import traceback
                    with st.expander("상세 오류 정보"):
                        st.code(traceback.format_exc())

                    # 오류도 히스토리에 저장
                    st.session_state.v3_messages.append({
                        'role': 'assistant',
                        'content': error_msg
                    })

#//==============================================================================//#
# V4: Playbook Agent
#//==============================================================================//#

def render_v4_playbook():
    """V4: ReAct Agent (계층적 검색 + Map-Reduce)"""

    st.subheader("V4: ReAct Agent")
    st.caption("계층적 검색(Vector→BM25→Hybrid) + Map-Reduce 요약으로 고품질 인사이트 생성")

    # API 키 입력 (메인 영역)
    st.markdown("#### 🔑 API 설정")

    # API 키 초기화
    if 'v4_api_key' not in st.session_state:
        st.session_state.v4_api_key = ""

    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.v4_api_key,
        type="password",
        help="QueryHandler와 Map-Reduce에서 GPT-4o-mini 사용",
        key="v4_api_input"
    )

    if api_key:
        st.session_state.v4_api_key = api_key
        st.success("✅ API 키 설정 완료")
    else:
        st.warning("⚠️ API 키를 입력하세요")

    st.markdown("---")

    # 동작 방식 및 예시 질문 (Expander로 정리)
    with st.expander("💡 동작 방식 및 예시 질문"):
        st.markdown("### 동작 방식")
        st.markdown("""
        **계층적 검색 (3단계)**
        1. Vector 검색 (BGE-M3)
        2. BM25 재정렬
        3. Hybrid 최종 선별

        **Map-Reduce 요약**
        - 200건 → 10개 그룹 요약
        - 최종 통합 보고서 생성
        """)

        st.markdown("### 📝 예시 질문")
        st.markdown("""
        - "토리든 전반적으로 어때?"
        - "VT 시카크림 보습력 어때?"
        - "올리브영이랑 쿠팡에서 떠오르는 키워드 뭐야?"
        - "라운드랩이랑 토리든 비교해줘"
        """)

    st.markdown("---")

    # 채팅 히스토리 초기화
    if 'v4_messages' not in st.session_state:
        st.session_state.v4_messages = []

    # 모든 메시지 표시 (정순: 오래된 것 → 최신 것)
    for msg in st.session_state.v4_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

    # 사용자 입력 (챗봇 스타일)
    if prompt := st.chat_input("질문을 입력하세요 (예: 토리든 전반적으로 어때?)"):

        if not st.session_state.v4_api_key:
            st.error("❌ 먼저 API 키를 입력하세요")
            return

        # 사용자 메시지 추가
        st.session_state.v4_messages.append({'role': 'user', 'content': prompt})

        with st.chat_message('user'):
            st.markdown(prompt)

        # AI 응답
        with st.chat_message('assistant'):
            try:
                from ai_engines.v4_react_agent import Orchestrator

                orchestrator = Orchestrator(st.session_state.v4_api_key)

                # 진행상황을 채팅창에 누적 표시
                def progress_callback(event, data):
                    """진행상황 콜백 - 채팅창에 메시지 추가"""
                    if event == 'query_parsing_start':
                        st.write("🤔 질문 분석 중...")
                    elif event == 'query_parsing_done':
                        intent_msg = orchestrator.create_intent_message(data)
                        st.success(intent_msg)
                    elif event == 'stage1_start':
                        st.write("🔍 **Stage 1: Vector 검색 중...**")
                    elif event == 'stage1_done':
                        st.success(f"✅ Stage 1: {data:,}건 발견")
                    elif event == 'stage2_start':
                        st.write("🎯 **Stage 2: BM25 재정렬 중...**")
                    elif event == 'stage2_done':
                        st.success(f"✅ Stage 2: {data:,}건 선별")
                    elif event == 'stage3_start':
                        st.write("⭐ **Stage 3: Hybrid 최종 선별 중...**")
                    elif event == 'stage3_done':
                        st.success(f"✅ Stage 3: {data:,}건 최종 선별")
                    elif event == 'map_reduce_start':
                        chunks = (data + 19) // 20  # ceil(data / 20)
                        st.write(f"📝 **Map-Reduce 시작:** {data}개 리뷰를 {chunks}개 그룹으로 요약")
                    elif event == 'map_progress':
                        current, total = data
                        st.write(f"   └─ 그룹 {current}/{total} 요약 중...")
                    elif event == 'reduce_start':
                        st.write(f"🔄 **Reduce:** {data}개 그룹 요약을 통합하여 최종 보고서 작성 중...")
                    elif event == 'map_reduce_done':
                        st.success("✅ 최종 보고서 생성 완료!")

                # 실행
                result = orchestrator.process_query(prompt, progress_callback)

                # 구분선 추가
                st.markdown("---")

                # 답변 표시
                st.markdown(result['answer'])

                # 디버그 정보 (Expander)
                with st.expander("🔍 분석 정보 보기"):
                    st.write("**파싱된 쿼리:**")
                    st.json(result['parsed'])

                    st.write("**통계:**")
                    st.write(f"- Stage 1: {result['stats']['stage1']:,}건")
                    st.write(f"- Stage 2: {result['stats']['stage2']:,}건")
                    st.write(f"- Stage 3 (최종): {result['stats']['stage3']:,}건")

                    st.write("**Playbook:**")
                    st.json(result['playbook'])

                # 응답 저장
                st.session_state.v4_messages.append({
                    'role': 'assistant',
                    'content': result['answer']
                })

            except Exception as e:
                error_msg = f"❌ 오류 발생: {e}"
                st.error(error_msg)
                import traceback
                with st.expander("상세 오류 정보"):
                    st.code(traceback.format_exc())

                # 오류도 히스토리에 저장
                st.session_state.v4_messages.append({
                    'role': 'assistant',
                    'content': error_msg
                })

#//==============================================================================//#
# V5: LangGraph Agent
#//==============================================================================//#

def render_v5_langgraph():
    """V5: LangGraph Agent (14개 Tool + 5개 Node)"""

    st.subheader("V5: LangGraph Agent")

    # API 키 초기화
    if 'v5_api_key' not in st.session_state:
        st.session_state.v5_api_key = ""

    # API 키 입력
    api_key = st.text_input(
        "OpenAI API Key",
        value=st.session_state.v5_api_key,
        type="password",
        help="Parser와 Synthesizer Node에서 GPT 사용",
        key="v5_api_input"
    )

    if api_key:
        st.session_state.v5_api_key = api_key
        st.success("✅ API 키 설정 완료")
    else:
        st.warning("⚠️ API 키를 입력하세요")

    st.markdown("---")

    # 채팅 히스토리 초기화
    if 'v5_messages' not in st.session_state:
        st.session_state.v5_messages = []

    # 재질문용 상태 초기화
    if 'v5_pending_query' not in st.session_state:
        st.session_state.v5_pending_query = None

    # 모든 메시지 표시 (정순: 오래된 것 → 최신 것, 입력창이 맨 밑에 오도록)
    for msg in st.session_state.v5_messages:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

            # 재질문 드롭다운이 있는 경우 표시
            if msg.get('show_dropdowns'):
                st.markdown("---")

                available_channels = msg.get('available_channels', [])
                available_brands = msg.get('available_brands', [])
                available_products = msg.get('available_products', [])

                # 드롭다운 3개
                col1, col2, col3 = st.columns(3)

                with col1:
                    selected_channel = st.selectbox(
                        "채널 선택",
                        options=["전체"] + available_channels,
                        key=f"v5_channel_{msg['msg_id']}"
                    )

                with col2:
                    selected_brand = st.selectbox(
                        "브랜드 선택",
                        options=["전체"] + available_brands,
                        key=f"v5_brand_{msg['msg_id']}"
                    )

                with col3:
                    selected_product = st.selectbox(
                        "제품 선택",
                        options=["전체"] + available_products,
                        key=f"v5_product_{msg['msg_id']}"
                    )

                # 분석 실행 버튼
                if st.button("선택 완료 - 분석 시작", key=f"v5_analyze_{msg['msg_id']}"):
                    # 선택된 값으로 새 쿼리 생성
                    intent_map = {
                        'attribute_analysis': '속성 분석해줘',
                        'pros_cons': '장단점 알려줘',
                        'sentiment_analysis': '감성 분석해줘',
                        'comparison': '비교해줘',
                        'full_review': '분석해줘'
                    }
                    intent = msg.get('parsed_query', {}).get('intent', 'full_review')
                    intent_text = intent_map.get(intent, '분석해줘')

                    query_parts = []
                    if selected_channel != "전체":
                        query_parts.append(selected_channel)
                    if selected_brand != "전체":
                        query_parts.append(selected_brand)
                    if selected_product != "전체":
                        query_parts.append(selected_product)
                    query_parts.append(intent_text)

                    new_query = " ".join(query_parts)
                    st.session_state.v5_pending_query = new_query
                    st.rerun()

    # 사용자 입력 (챗봇 스타일, 하단 고정) - 항상 표시
    user_input = st.chat_input("질문을 입력하세요 (예: 빌리프 브랜드 속성 분석해줘)")

    # Pending query 확인 (드롭다운 재질문)
    if st.session_state.v5_pending_query:
        prompt = st.session_state.v5_pending_query
        st.session_state.v5_pending_query = None
    else:
        prompt = user_input

    if prompt:

        if not st.session_state.v5_api_key:
            st.error("❌ 먼저 API 키를 입력하세요")
            return

        # 사용자 메시지 추가
        st.session_state.v5_messages.append({'role': 'user', 'content': prompt})

        with st.chat_message('user'):
            st.markdown(prompt)

        # AI 응답
        with st.chat_message('assistant'):
            try:
                # V5 Agent import
                import os
                ai_engines_dir = os.path.join(dashboard_dir, 'ai_engines')
                if ai_engines_dir not in sys.path:
                    sys.path.insert(0, ai_engines_dir)

                from v5_langgraph_agent import V5Agent

                # Agent 초기화 (API 키 환경변수 설정)
                os.environ['OPENAI_API_KEY'] = st.session_state.v5_api_key

                agent = V5Agent()

                # 진행 상황 표시용 컨테이너
                progress_container = st.container()

                # 스트리밍으로 실행하여 각 노드 출력 표시
                with progress_container:
                    st.write("🤖 **LangGraph 워크플로우 실행 중...**\n")

                    node_icons = {
                        "Parser": "🔍",
                        "Validation": "✅",
                        "Router": "🎯",
                        "Executor": "⚙️",
                        "Synthesizer": "📝"
                    }

                    status_icons = {
                        "processing": "🔄",
                        "success": "✅",
                        "warning": "⚠️",
                        "error": "❌",
                        "info": "ℹ️"
                    }

                    final_state = None

                    for state_update in agent.stream(prompt):
                        # 현재 노드 상태 확인
                        node_name = list(state_update.keys())[0]
                        node_state = state_update[node_name]

                        messages = node_state.get("messages", [])
                        if messages:
                            latest_msg = messages[-1]
                            node_icon = node_icons.get(latest_msg['node'], "•")
                            status_icon = status_icons.get(latest_msg['status'], "•")

                            # 노드 진행 상황 출력
                            status_text = f"{node_icon} **{latest_msg['node']}** {status_icon}"
                            st.write(status_text)

                            # content가 짧으면 전체 출력, 길면 요약
                            content = latest_msg['content']
                            if len(content) <= 150:
                                st.caption(content)
                            else:
                                # 여러 줄인 경우 첫 줄만 표시
                                first_line = content.split('\n')[0]
                                st.caption(f"{first_line}...")

                        # 마지막 상태 저장
                        final_state = node_state

                # 구분선
                st.markdown("---")

                # 최종 응답 전체 실행 (final_response 가져오기)
                if final_state is None:
                    final_state = agent.run(prompt)

                # 최종 응답 표시
                final_response = final_state.get('final_response', '응답 생성 실패')
                st.markdown(final_response)

                # 디버그 정보 (Expander)
                with st.expander("🔍 실행 정보 보기"):
                    st.write("**파싱된 쿼리:**")
                    st.json(final_state.get('parsed_query', {}))

                    st.write("**데이터 검증:**")
                    st.json(final_state.get('data_validation', {}))

                    st.write("**선택된 툴:**")
                    selected_tools = final_state.get('selected_tools', [])
                    st.write(", ".join(selected_tools) if selected_tools else "없음")

                    st.write("**툴 실행 결과:**")
                    tool_results = final_state.get('tool_results', {})
                    for tool_name, result in tool_results.items():
                        status = result.get('status', 'unknown')
                        st.write(f"- {tool_name}: {status}")

                # 응답 저장 (재질문 정보 포함)
                needs_clarification = final_state.get('needs_clarification', False)
                clarification_type = final_state.get('clarification_type', 'none')

                msg_data = {
                    'role': 'assistant',
                    'content': final_response,
                    'msg_id': len(st.session_state.v5_messages),  # 고유 ID
                }

                # 드롭다운 재질문인 경우
                if needs_clarification and clarification_type == 'dropdown':
                    msg_data['show_dropdowns'] = True
                    msg_data['available_channels'] = final_state.get('available_channels', [])
                    msg_data['available_brands'] = final_state.get('available_brands', [])
                    msg_data['available_products'] = final_state.get('available_products', [])
                    msg_data['parsed_query'] = final_state.get('parsed_query', {})

                st.session_state.v5_messages.append(msg_data)

            except Exception as e:
                error_msg = f"❌ 오류 발생: {e}"
                st.error(error_msg)
                import traceback
                with st.expander("상세 오류 정보"):
                    st.code(traceback.format_exc())

                # 오류도 히스토리에 저장
                st.session_state.v5_messages.append({
                    'role': 'assistant',
                    'content': error_msg
                })

#//==============================================================================//#
# 실행
#//==============================================================================//#

if __name__ == "__main__":
    main()
