import os, re, hashlib, unicodedata, glob
import numpy as np
import pandas as pd

# === 경로 ===
BASE = r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data"
IN_DIR  = os.path.join(BASE, "data_oliveyoung", "raw_data", "reviews_oliveyoung")         # 원본 csv들이 있는 폴더
OUT_DIR = os.path.join(BASE, "data_oliveyoung", "processed_data", "reviews_oliveyoung")  # 표준화 저장
REP_DIR = os.path.join(BASE, "processed", "reports")
os.makedirs(OUT_DIR, exist_ok=True); os.makedirs(REP_DIR, exist_ok=True)

KEEP_COLS = [
    'review_id','captured_at','channel','product_url','product_name','brand','category',
    'category_use','product_price_sale','product_price_origin','sort_type','ranking',
    'reviewer_name','rating','review_date','selected_option','review_text','helpful_count',
    'review_text_raw' 
]

# ===== 유틸 =====
URL_RE   = re.compile(r"https?://\S+|www\.\S+")
HTML_RE  = re.compile(r"<[^>]+>")
EMOJI_RE = re.compile("[" "\U0001F300-\U0001F6FF" "\U0001F900-\U0001F9FF" "\U0001FA70-\U0001FAFF" "\u2600-\u27BF" "]+")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-\s]?)?\d{2,4}[-\s]?\d{3,4}[-\s]?\d{4}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def norm_text(s: str) -> str:
    if pd.isna(s): return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = HTML_RE.sub(" ", s)
    s = URL_RE.sub(" ", s)
    s = EMOJI_RE.sub(" ", s)
    s = EMAIL_RE.sub(" ", s)
    s = PHONE_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_date_any(x):
    if pd.isna(x): return pd.NaT
    x = str(x).strip()
    m = re.fullmatch(r"(\d{4})[-/\.]?(\d{2})[-/\.]?(\d{2})", x)
    if m:
        y, mo, d = m.groups()
        try: return pd.Timestamp(f"{y}-{mo}-{d}")
        except: return pd.NaT
    return pd.to_datetime(x, errors="coerce")

def to_int(x, default=0):
    try:
        if pd.isna(x) or str(x).strip()=="":
            return default
        return int(str(x).replace(",","").strip())
    except:
        return default

def to_money(x):
    if pd.isna(x) or str(x).strip()=="":
        return np.nan
    s = re.sub(r"[^\d\.]", "", str(x))
    try: return float(s)
    except: return np.nan

def to_rating_0_5(x):
    if pd.isna(x): return np.nan
    nums = re.findall(r"\d+(?:\.\d+)?", str(x))
    if not nums: return np.nan
    v = float(nums[-1])
    # 0~5/1~5 혼재 가능 → 0~5로 clip (필요시 후에 +1 쉬프트 등 조정)
    return float(np.clip(v, 0.0, 5.0))

def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def read_csv_safe(path):
    for enc in ("utf-8-sig","utf-8","cp949","euc-kr"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path, sep=None, engine="python")

# 브랜드 추출(비어있을 때만): 제품명 맨 앞 토큰/괄호 앞부분 등 단순 휴리스틱
def brand_after_brackets(product_name: str) -> str:
    """제품명 앞단의 [..]/(..)/{..}/〈..〉/【..】/<..> 태그를 모두 떼고,
    바로 뒤에 오는 첫 단어를 브랜드로 추출."""
    if not isinstance(product_name, str):
        return ""
    s = product_name.strip()

    # 선행 태그들 반복 제거
    s = re.sub(
        r'^\s*(?:\[[^\]]*\]|\([^)]+\)|\{[^}]+\}|〈[^〉]+〉|【[^】]+】|<[^>]+>)*\s*',
        '',
        s
    )

    # 첫 단어(한/영/숫자 및 몇몇 기호 허용)
    m = re.match(r'([가-힣A-Za-z0-9&.\-]+)', s)
    return m.group(1) if m else ""

# ===== 한 파일 표준화 =====
def standardize_one(path):
    src = read_csv_safe(path)
    orig_len = len(src)

    # 동의어 컬럼 매핑 테이블(있는 것만 사용)
    alias = {
        'product_url': ['product_url','product_u','url'],
        'product_name':['product_name','product_n','item_name'],
        'brand':['brand'],
        'category':['category'],
        'category_use':['category_use','category_u','category_mid','category_large'],
        'product_price_origin':['product_price_origin','product_price_before','original_price'],
        'product_price_sale':['product_price_sale','product_price_after','sale_price'],
        'sort_type':['sort_type'],
        'ranking':['ranking'],
        'reviewer_name':['reviewer_name'],
        'reviewer_rank':['reviewer_rank'],
        'reviewer_skin_features':['reviewer_skin_features','피부타입','피부고민','자극도'],  # 한국어 컬럼을 합쳐 넣을 수도 있음
        'rating':['rating','star'],
        'review_date':['review_date'],
        'selected_option':['selected_option'],
        'review_text':['review_text','review_content','review_co','review_tex'],
        'helpful_count':['helpful_count','helpful_co','voted_count']
    }

    def pick(colnames):
        for c in colnames:
            if c in src.columns: return src[c]
        return pd.Series([np.nan]*orig_len)

    df = pd.DataFrame({
        'product_url'          : pick(alias['product_url']).map(norm_text),
        'product_name'         : pick(alias['product_name']).map(norm_text),
        'brand'                : pick(alias['brand']).map(norm_text),
        'category'             : pick(alias['category']).map(norm_text),
        'category_use'         : pick(alias['category_use']).map(norm_text),
        'product_price_sale'   : pick(alias['product_price_sale']).map(to_money),
        'product_price_origin' : pick(alias['product_price_origin']).map(to_money),
        'sort_type'            : pick(alias['sort_type']).map(norm_text),
        'ranking'              : pick(alias['ranking']).map(to_int),
        'reviewer_name'        : pick(alias['reviewer_name']).map(norm_text),
        'rating'               : pick(alias['rating']).map(to_rating_0_5),
        'review_date'          : pick(alias['review_date']).map(parse_date_any).dt.date,
        'selected_option'      : pick(alias['selected_option']).map(norm_text),
        'helpful_count'        : pick(alias['helpful_count']).map(to_int),
    })
    # (정규화 전에) 원문 보존
    _raw_review = pick(alias['review_text'])
    df['review_text_raw'] = _raw_review

    # 정규화본 생성
    df['review_text'] = _raw_review.map(norm_text)
    # reviewer_skin_features/한국어 속성 합치기(참고용 문자열, 표준 스키마엔 안 넣음)
    if 'reviewer_skin_features' in alias and any(c in src.columns for c in alias['reviewer_skin_features']):
        feat_cols = [c for c in alias['reviewer_skin_features'] if c in src.columns]
        tmp = src[feat_cols].astype(str).agg(lambda r: " / ".join([norm_text(v) for v in r if str(v).strip()!='']), axis=1)
        df['reviewer_skin_features'] = tmp.replace({"": np.nan})

    # 채널/캡처시각/브랜드 보정
    df['channel'] = "OliveYoung"
    df['captured_at'] = pd.Timestamp.now(tz="Asia/Seoul")
    need_brand = df['brand'].isna() | (df['brand'].astype(str).str.strip() == "")
    df.loc[need_brand, 'brand'] = df.loc[need_brand, 'product_name'].map(brand_after_brackets)

    # review_id 생성(없으면): url+텍스트 해시
    base_key = (df['product_url'].fillna('') + "|" + df['review_text'].fillna('')).map(lambda s: md5(s))
    df['review_id'] = base_key

    # category_use는 이번 라운드 비워두기(요청사항)
    if 'category_use' not in df.columns:
        df['category_use'] = np.nan
    df['category_use'] = df['category_use'].where(df['category_use'].notna(), "")

    # 품질 필터
    too_short = df['review_text'].str.len().fillna(0) < 20
    link_only = df['review_text'].str.fullmatch(r"(?:https?://\S+|\S+\.com)+", na=False)
    df = df.loc[~(too_short | link_only)].copy()

    # 중복 제거: review_id 기준 1차 → 동일 url+텍스트 해시 2차
    df = df.drop_duplicates(subset=['review_id'], keep='first')
    dup2 = (df['product_url'].fillna('') + "|" + df['review_text'].fillna('')).map(md5)
    df['__dup__'] = dup2
    df = df.drop_duplicates(subset='__dup__', keep='first').drop(columns='__dup__')

    # 표준 컬럼 순서로 정렬 & 누락 컬럼 보충
    for col in KEEP_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[KEEP_COLS].copy()

    # 저장
    out_name = os.path.splitext(os.path.basename(path))[0] + "_std.csv"
    out_path = os.path.join(OUT_DIR, out_name)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    # 리포트
    rpt = {
        "file": os.path.basename(path),
        "rows_out": len(df),
        "date_min": str(df['review_date'].min()),
        "date_max": str(df['review_date'].max()),
        "rating_min": float(df['rating'].min()) if df['rating'].notna().any() else np.nan,
        "rating_max": float(df['rating'].max()) if df['rating'].notna().any() else np.nan,
        "unique_urls": int(df['product_url'].nunique()),
        "unique_reviewers": int(df['reviewer_name'].nunique()),
    }
    return df, rpt

# === 실행 ===
reports = []
for f in glob.glob(os.path.join(IN_DIR, "*.csv")):
    try:
        df_out, rpt = standardize_one(f)
        reports.append(rpt)
        print(f"[OK] {os.path.basename(f)} → rows={rpt['rows_out']}")
    except Exception as e:
        print(f"[ERR] {os.path.basename(f)} :: {e}")

pd.DataFrame(reports).to_csv(os.path.join(REP_DIR, "oliveyoung_std_reports.csv"), index=False, encoding="utf-8-sig")
print("[DONE] 모든 파일 표준화 완료")



from sentence_transformers import SentenceTransformer


def search_reviews(question, top_k=5):
    q_vec = model.encode