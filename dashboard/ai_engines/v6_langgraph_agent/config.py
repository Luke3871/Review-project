#//==============================================================================//#
"""
config.py
V6 LangGraph Agent 설정

last_updated: 2025.11.02
"""
#//==============================================================================//#

import logging
import os

# 0. 로깅 설정
LOGGING_CONFIG = {
    "level": os.getenv("V6_LOG_LEVEL", "INFO"),  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "log_file": None,  # None이면 파일 저장 안 함, 경로 지정하면 파일에 저장
    "console_output": True  # 콘솔 출력 여부
}

def setup_logging():
    """V6 Agent 로깅 설정"""
    level = getattr(logging, LOGGING_CONFIG["level"])

    # 루트 로거 설정
    logger = logging.getLogger("v6_agent")
    logger.setLevel(level)

    # 포맷터
    formatter = logging.Formatter(
        LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"]
    )

    # 콘솔 핸들러
    if LOGGING_CONFIG["console_output"]:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 파일 핸들러 (옵션)
    if LOGGING_CONFIG["log_file"]:
        file_handler = logging.FileHandler(LOGGING_CONFIG["log_file"])
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

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
    "max_tokens": 16384,  # 4096 → 16384 (gpt-4o-mini 최대 출력)

    # 노드별 temperature 설정
    "temperature": {
        "entity_parser": 0.0,        # 정확한 엔티티 추출
        "capability_detector": 0.0,  # 정확한 capability 판단
        "sql_generator": 0.0,        # 정확한 SQL 생성
        "response_planner": 0.0,     # 정확한 시각화 판단
        "output_generator": 0.3,     # 자연스러운 텍스트 생성
        "synthesizer": 0.3           # 자연스러운 최종 답변
    }
}


# 3. JSONB 필드 매핑
# preprocessed_reviews 테이블의 analysis JSONB 구조
JSONB_PATHS = {
    "제품특성": "analysis->'제품특성'",
    "감정요약": "analysis->'감정요약'",
    "장점": "analysis->'장점'",
    "단점": "analysis->'단점'",
    "구매동기": "analysis->'구매동기'",
    "키워드": "analysis->'키워드'"
}

# 제품특성 하위 속성들
PRODUCT_ATTRIBUTES = [
    "보습력", "발림성", "향", "지속력", "커버력",
    "흡수력", "끈적임", "자극", "가격", "용량"
]


# 4. 시각화 설정
VISUALIZATION_CONFIG = {
    "mode": "hybrid",  # auto | suggest | hybrid

    # Confidence threshold
    "auto_threshold": 0.7,      # 이상이면 자동 시각화 생성 (0.8 → 0.7로 낮춤)
    "suggest_threshold": 0.4,   # 이상이면 시각화 옵션 제안

    # Confidence 계산 규칙
    "confidence_rules": {
        "time_series": {
            "min_points": 3,
            "weight": 0.7  # 0.4 → 0.7 (시계열은 무조건 그래프 필요)
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

    # 사용자 선호도 학습
    "user_preference": {
        "enabled": True,
        "adjust_threshold": True,
        "min_interactions": 5
    },

    # 스트리밍 설정
    "streaming": {
        "text_first": True,   # 텍스트 먼저 스트리밍
        "chart_async": True   # 차트 비동기 로딩
    }
}


# 5. Progress Tracker 설정
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
        "save_to_db": True,        # DB에 로그 저장
        "save_to_file": True,      # JSON 파일로 로그 저장
        "verbose_level": "normal"  # minimal | normal | verbose
    }
}


# 6. 노드별 아이콘
NODE_ICONS = {
    "EntityParser": "🔍",
    "CapabilityDetector": "📊",
    "SQLGenerator": "💾",
    "Executor": "⚡",
    "ResponsePlanner": "🎯",
    "OutputGenerator": "🎨",
    "Synthesizer": "✨"
}


# 7. 채널 매핑
CHANNEL_MAPPING = {
    "올리브영": "OliveYoung",
    "쿠팡": "Coupang",
    "다이소": "Daiso"
}


# 8. 에러 메시지
ERROR_MESSAGES = {
    "no_data": "조건에 맞는 리뷰 데이터를 찾을 수 없습니다.",
    "sql_error": "데이터베이스 쿼리 실행 중 오류가 발생했습니다.",
    "timeout": "쿼리 실행 시간이 초과되었습니다. 더 구체적인 조건을 추가해보세요.",
    "invalid_query": "질문을 이해할 수 없습니다. 다시 입력해주세요.",
    "insufficient_data": "신뢰할 수 있는 분석을 위한 데이터가 부족합니다. (최소 {min}건 필요)"
}


# 9. 피드백 옵션
FEEDBACK_REASONS = {
    "positive": [
        "원하는 정보를 정확히 얻었어요",
        "시각화가 이해하기 좋았어요",
        "빠르게 답변을 받았어요",
        "설명이 명확했어요"
    ],
    "negative": [
        "원하는 정보가 아니에요",
        "결과가 부정확해요",
        "시각화가 이해하기 어려워요",
        "답변이 너무 느려요",
        "오류가 발생했어요"
    ]
}


# 10. 브랜드 정보 (brand_list.txt, brand_mapping.txt에서 로드)
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

# 카테고리별 속성
CATEGORY_ATTRIBUTES = {
    "스킨/토너": ["제형", "흡수력", "보습력", "산뜻함", "향", "가격"],
    "에센스/세럼/앰플": ["제형", "흡수력", "보습력", "끈적임", "향", "가격"],
    "크림": ["제형", "보습력", "발림성", "끈적임", "향", "가격"],
    "로션": ["제형", "보습력", "발림성", "끈적임", "향", "가격"],
    "미스트/오일": ["제형", "흡수력", "보습력", "끈적임", "향", "가격"],
    "스킨케어세트": ["제형", "보습력", "향", "가격"],
    "스킨케어 디바이스": ["사용감", "효과", "가격"],
    "선케어": ["제형", "백탁", "보습력", "끈적임", "향", "가격"],
    "마스크/팩": ["제형", "밀착력", "보습력", "향", "가격"],
    "클렌징": ["제형", "세정력", "자극", "촉촉함", "향", "가격"],
    "아이케어": ["제형", "보습력", "흡수력", "향", "가격"],
    "립메이크업": ["제형", "발색", "지속력", "촉촉함", "향", "가격"],
    "베이스메이크업": ["제형", "발색", "커버력", "지속력", "밀착력", "향", "가격"],
    "아이메이크업": ["제형", "발색", "지속력", "발림성", "날림", "향", "가격"],
    "기타": ["제형", "사용감", "향", "가격"]
}

# 속성 설명
ATTRIBUTE_DESCRIPTIONS = {
    "제형": "텍스처, 타입, 사용감",
    "흡수력": "피부에 스며드는 속도",
    "보습력": "수분 유지 능력",
    "끈적임": "발림 후 끈적거림 (낮을수록 좋음 - 산뜻, 가벼움이 긍정)",
    "발색": "색상의 선명도",
    "커버력": "피부 고민(기미, 잡티 등) 커버 능력",
    "세정력": "클렌징 제품 특유의 속성, 메이크업이 잘 지워지는 것",
    "백탁": "선케어 제품 특유의 속성, 발랐을 때 하얗게 뜨는 것",
    "지속력": "효과 유지 시간",
    "향": "제품의 향",
    "가격": "가성비",
    "밀착력": "피부에 밀착되는 정도",
    "자극": "피부 자극 정도",
    "촉촉함": "촉촉한 느낌",
    "산뜻함": "산뜻한 느낌",
    "발림성": "발랐을 때의 느낌",
    "날림": "파우더/아이섀도우 등이 날리는 정도"
}

# 분석 관련 키워드 (검증 완화용)
ANALYSIS_KEYWORDS = [
    "평점", "트렌드", "리뷰", "장점", "단점", "분포", "비교",
    "평가", "반응", "의견", "피드백", "후기", "감상", "분석"
]


# 12. Debug 모드 설정 (Phase 2: UI 피드백 개선)
DEBUG_CONFIG = {
    "enabled": False,  # Streamlit sidebar에서 동적 토글 가능
    "show_llm_prompts": True,  # LLM 프롬프트 표시
    "show_llm_responses": True,  # LLM 원본 응답 표시
    "show_sql_generation_process": True,  # SQL 생성 과정 상세 표시
    "max_prompt_length": 1000,  # 프롬프트 표시 최대 길이 (너무 길면 잘라냄)
    "max_response_length": 1000,  # 응답 표시 최대 길이
}
