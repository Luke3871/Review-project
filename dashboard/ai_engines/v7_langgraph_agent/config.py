#//==============================================================================//#
"""
config.py
V7 LangGraph Agent 설정

last_updated: 2025.11.02
"""
#//==============================================================================//#

# 1. 데이터베이스 설정
DB_CONFIG = {
    'dbname': 'cosmetic_reviews',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': 5432
}

# 테이블명
REVIEWS_TABLE = "reviews"  # 314,285건
PREPROCESSED_TABLE = "preprocessed_reviews"  # 5,000건 (GPT-4o-mini 분석 완료)

# 통계적 신뢰도를 위한 최소 리뷰 수
MIN_REVIEW_COUNT = 1


# 2. LLM 설정
LLM_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "max_tokens": 4096,

    # 노드별 temperature 설정
    "temperature": {
        "agent": 0.1,                    # Agent의 추론 (약간의 유연성)
        "entity_parser": 0.0,            # 정확한 엔티티 추출
        "capability_detector": 0.0,      # 정확한 capability 판단
        "sql_generator": 0.0,            # 정확한 SQL 생성
        "sql_refiner": 0.0,              # 정확한 SQL 수정
        "output_generator": 0.3,         # 자연스러운 텍스트 생성
    }
}


# 3. Agent 설정 (V7 신규)
AGENT_CONFIG = {
    "model": "gpt-4o",                   # Agent는 GPT-4o 사용 (더 똑똑하게)
    "temperature": 0.1,                  # 추론용 낮은 temperature
    "max_iterations": 15,                # 최대 ReAct 루프 반복 횟수
    "max_tokens": 4096,

    # Tool 호출 관련
    "tool_choice": "auto",               # LLM이 자동으로 Tool 선택
    "parallel_tool_calls": False,        # 순차적 Tool 호출 (의존성 있음)

    # 타임아웃
    "timeout": 120,                      # 전체 Agent 실행 타임아웃 (초)
    "tool_timeout": 30,                  # 개별 Tool 실행 타임아웃 (초)

    # Thought 표시 설정 (하이브리드 방식)
    "show_thoughts": True,
    "thought_display": {
        "mode": "hybrid",                # hybrid | always | never
        "realtime": True,                # 실시간 업데이트
        "expander_default": False,       # 기본은 접힌 상태
        "icon": "💭",
        "show_duration": True,           # 각 단계 소요 시간 표시
        "show_step_number": True,        # Step 번호 표시
        "animate": True,                 # 타이핑 애니메이션 효과
        "color": "blue"                  # Streamlit 색상
    },

    # 로그 저장
    "logging": {
        "save_messages": True,           # messages 전체 저장
        "save_thoughts": True,           # Thought만 별도 저장
        "save_to_file": True,            # JSON 파일로 저장
        "log_dir": "dashboard/logs/v7_agent/",
        "verbose_level": "normal"        # minimal | normal | verbose
    }
}


# 4. JSONB 필드 매핑
# preprocessed_reviews 테이블의 analysis JSONB 구조
JSONB_PATHS = {
    # 제품 정보
    "원본_제품명": "analysis->'원본_제품명'",
    "표준_브랜드": "analysis->'표준_브랜드'",
    "표준_제품명": "analysis->'표준_제품명'",
    "제품_카테고리": "analysis->'제품_카테고리'",
    "용량_및_수량": "analysis->'용량_및_수량'",
    "색상_옵션": "analysis->'색상_옵션'",
    "기획여부": "analysis->'기획여부'",

    # 분석 결과
    "제품특성": "analysis->'제품특성'",
    "기획정보": "analysis->'기획정보'",
    "감정요약": "analysis->'감정요약'",
    "장점": "analysis->'장점'",
    "단점": "analysis->'단점'",
    "불만사항": "analysis->'불만사항'",
    "구매동기": "analysis->'구매동기'",
    "타제품비교": "analysis->'타제품비교'",
    "키워드": "analysis->'키워드'"
}

# 제품특성 하위 속성들 (전체)
PRODUCT_ATTRIBUTES = [
    # 기본 속성
    "제형", "보습력", "발림성", "흡수력", "끈적임",
    "향", "가격",

    # 메이크업 속성
    "발색", "커버력", "지속력", "밀착력", "날림",

    # 클렌징 속성
    "세정력", "자극", "촉촉함", "산뜻함",

    # 선케어 속성
    "백탁",

    # 마스크/팩 속성
    # (밀착력은 메이크업과 공통)

    # 기타
    "사용감", "용량"
]

# 카테고리별 분석 속성 매핑
CATEGORY_ATTRIBUTES = {
    "스킨/토너": ["제형", "흡수력", "보습력", "산뜻함", "향", "가격"],
    "에센스/세럼/앰플": ["제형", "흡수력", "보습력", "끈적임", "향", "가격"],
    "크림": ["제형", "보습력", "발림성", "끈적임", "향", "가격"],
    "로션": ["제형", "보습력", "발림성", "끈적임", "향", "가격"],
    "미스트/오일": ["제형", "흡수력", "보습력", "끈적임", "향", "가격"],
    "스킨케어세트": ["제형", "보습력", "향", "가격"],
    "스킨케어 디바이스": ["사용감", "가격"],
    "선케어": ["제형", "백탁", "보습력", "끈적임", "향", "가격"],
    "마스크/팩": ["제형", "밀착력", "보습력", "향", "가격"],
    "클렌징": ["제형", "세정력", "자극", "촉촉함", "향", "가격"],
    "아이케어": ["제형", "보습력", "흡수력", "향", "가격"],
    "립메이크업": ["제형", "발색", "지속력", "촉촉함", "향", "가격"],
    "베이스메이크업": ["제형", "발색", "커버력", "지속력", "밀착력", "향", "가격"],
    "아이메이크업": ["제형", "발색", "지속력", "발림성", "날림", "향", "가격"],
    "기타": ["제형", "사용감", "향", "가격"]
}

# 불만사항 유형
COMPLAINT_TYPES = [
    "용기/패키지 디자인",
    "용기 내구성",
    "내용물 문제",
    "용량 부족",
    "색상/향 불만",
    "광고와 다름",
    "성분 문제",
    "사진과 다름",
    "가짜 의심",
    "유통기한"
]

# 구매동기 유형
PURCHASE_MOTIVATION_TYPES = [
    "인플루언서",
    "지인추천",
    "온라인커뮤니티",
    "광고",
    "매장",
    "브랜드인지도",
    "재구매",
    "기타"
]


# 5. 시각화 설정
VISUALIZATION_CONFIG = {
    "mode": "hybrid",  # auto | suggest | hybrid

    # Confidence threshold
    "auto_threshold": 0.7,      # 이상이면 자동 시각화 생성
    "suggest_threshold": 0.4,   # 이상이면 시각화 옵션 제안

    # Confidence 계산 규칙
    "confidence_rules": {
        "time_series": {
            "min_points": 3,
            "weight": 0.7
        },
        "multi_comparison": {
            "min_entities": 2,
            "max_entities": 10,
            "weight": 0.35
        },
        "distribution": {
            "min_categories": 5,
            "weight": 0.3
        },
        "keyword_cloud": {
            "min_keywords": 20,
            "weight": 0.35
        },
        "large_dataset": {
            "min_rows": 50,
            "weight": 0.15
        }
    },

    # 스트리밍 설정
    "streaming": {
        "text_first": True,   # 텍스트 먼저 스트리밍
        "chart_async": True   # 차트 비동기 로딩
    }
}


# 6. Progress Tracker 설정
PROGRESS_CONFIG = {
    "enabled": True,
    "show_substeps": True,
    "show_timing": True,
    "show_data_counts": True,

    "streaming": {
        "update_interval": 0.1,  # 0.1초마다 UI 업데이트
        "buffer_size": 10
    },

    "display": {
        "icons": True,
        "progress_bar": True,
        "estimated_time": True,
        "compact_mode": False
    },

    "logging": {
        "save_to_state": True,
        "save_to_db": False,       # V7에서는 DB 로깅 비활성화 (단순화)
        "save_to_file": True,      # JSON 파일로 로그 저장
        "verbose_level": "normal"  # minimal | normal | verbose
    }
}


# 7. Tool 아이콘 (V7)
TOOL_ICONS = {
    "agent": "🤖",
    "parse_entities": "🔍",
    "detect_capabilities": "📊",
    "generate_sql": "💾",
    "execute_sql": "⚡",
    "refine_sql": "🔧",
    "generate_output": "🎨",
}


# 8. 채널 매핑
CHANNEL_MAPPING = {
    "올리브영": "OliveYoung",
    "쿠팡": "Coupang",
    "다이소": "Daiso"
}


# 9. 에러 메시지
ERROR_MESSAGES = {
    "no_data": "조건에 맞는 리뷰 데이터를 찾을 수 없습니다.",
    "sql_error": "데이터베이스 쿼리 실행 중 오류가 발생했습니다.",
    "timeout": "쿼리 실행 시간이 초과되었습니다. 더 구체적인 조건을 추가해보세요.",
    "invalid_query": "질문을 이해할 수 없습니다. 다시 입력해주세요.",
    "insufficient_data": "신뢰할 수 있는 분석을 위한 데이터가 부족합니다. (최소 {min}건 필요)",
    "max_iterations": "최대 반복 횟수에 도달했습니다. 질문을 더 구체적으로 해주세요.",
    "tool_error": "도구 실행 중 오류가 발생했습니다: {error}"
}


# 10. 브랜드 정보
import os

def _load_brand_list():
    """브랜드 리스트 로드"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        brand_file = os.path.join(base_dir, "brand_list.txt")

        with open(brand_file, 'r', encoding='utf-8') as f:
            brands = [line.strip() for line in f if line.strip()]
        return brands
    except Exception as e:
        print(f"Warning: Failed to load brand_list.txt: {e}")
        return []

def _load_brand_mapping():
    """브랜드 매핑 로드 (영문 → 한글)"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        mapping_file = os.path.join(base_dir, "brand_mapping.txt")

        mapping = {}
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '→' in line:
                    eng, kor = line.split('→')
                    mapping[eng.strip()] = kor.strip()
        return mapping
    except Exception as e:
        print(f"Warning: Failed to load brand_mapping.txt: {e}")
        return {}

# 브랜드 리스트 (576개)
BRAND_LIST = _load_brand_list()

# 브랜드 매핑 (영문 → 한글)
BRAND_MAPPING = _load_brand_mapping()


# 11. 카테고리 및 속성 정보
CATEGORIES = [
    "스킨/토너",
    "에센스/세럼/앰플",
    "크림",
    "로션",
    "미스트/오일",
    "스킨케어세트",
    "스킨케어 디바이스",
    "립메이크업",
    "베이스메이크업",
    "아이메이크업",
    "선케어",
    "마스크/팩",
    "클렌징",
    "아이케어",
    "기타"
]

# 속성 설명
ATTRIBUTE_DESCRIPTIONS = {
    "제형": "텍스처, 타입, 사용감",
    "흡수력": "피부에 스며드는 속도",
    "보습력": "수분 유지 능력",
    "끈적임": "발림 후 끈적거림 (낮을수록 좋음)",
    "발색": "색상의 선명도",
    "커버력": "피부 고민 커버 능력",
    "세정력": "메이크업 제거 능력",
    "백탁": "선케어 제품의 하얗게 뜨는 정도",
    "지속력": "효과 유지 시간",
    "향": "제품의 향",
    "가격": "가성비",
    "밀착력": "피부에 밀착되는 정도",
    "자극": "피부 자극 정도",
    "촉촉함": "촉촉한 느낌",
    "산뜻함": "산뜻한 느낌",
    "발림성": "발랐을 때의 느낌",
    "날림": "파우더/아이섀도우 날림"
}
