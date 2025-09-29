import pandas as pd, re, hashlib
from pathlib import Path
from datetime import datetime

# ===== 하드코딩 경로 (OLIVEYOUNG) =====
IN_DIR  = Path(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data\data_oliveyoung\raw_data\reviews_oliveyoung")
OUT_DIR = Path(r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data\data_oliveyoung\processed_data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV     = OUT_DIR / "reviews_oliveyoung.csv"
OUT_PARQUET = OUT_DIR / "reviews_oliveyoung.parquet"

# ===== 최종 컬럼 =====
FINAL_COLS = [
    "product_url","product_name","product_price_sale","product_price_origin",
    "category","sort_type","ranking","reviewer_name","rating","review_date",
    "review_text","selected_option","helpful_count","channel","brand",
    "category_use","captured_at","review_id"
]

def safe_read_csv(p: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig","cp949","utf-8"):
        try:
            return pd.read_csv(p, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(p, engine="python")

def norm(s):
    if s is None or (isinstance(s,float) and pd.isna(s)): return ""
    return re.sub(r"\s+"," ", str(s).strip())

def parse_date_loose(v):
    if v is None or (isinstance(v,float) and pd.isna(v)): return None
    s = str(v).replace("년","-").replace("월","-").replace("일"," ")
    s = s.replace(".", "-").replace("/", "-")
    dt = pd.to_datetime(s, errors="coerce")
    return dt.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(dt) else str(v)

def to_int_or_none(x):
    if x is None or (isinstance(x,float) and pd.isna(x)): return None
    s = re.sub(r"[^\d]","", str(x))
    return int(s) if s.isdigit() else None

def sha16(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def pick_col(cols_lower, original_cols, keys):
    cand = [c for c in original_cols if any(k in c.lower() for k in keys)]
    return cand[0] if cand else None

rows = []
captured_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

files = sorted(IN_DIR.glob("*_reviews.csv"))  # 하위폴더 없으면 glob, 있으면 rglob로 교체
if not files:
    raise SystemExit(f"파일을 찾지 못했습니다: {IN_DIR}")

for fp in files:
    df = safe_read_csv(fp)
    if df is None or df.empty: 
        continue

    orig = list(df.columns)
    lower = [str(c).lower() for c in orig]

    c_url    = pick_col(lower, orig, ["url","link","주소"])
    c_pname  = pick_col(lower, orig, ["product","상품","제품","name","품명"])
    c_price_s= pick_col(lower, orig, ["sale","할인","판매가","판매","세일"])
    c_price_o= pick_col(lower, orig, ["origin","정상","정가","원가"])
    c_cat    = pick_col(lower, orig, ["category","카테고리","대분류"])
    c_sort   = pick_col(lower, orig, ["sort","정렬"])
    c_rank   = pick_col(lower, orig, ["rank","순위"])
    c_rname  = pick_col(lower, orig, ["작성자","리뷰어","author","닉네임","name"])
    c_rating = pick_col(lower, orig, ["rating","평점","별점"])
    c_rdate  = pick_col(lower, orig, ["created","작성","등록","date","날짜"])
    c_rtext  = pick_col(lower, orig, ["text","review","내용","리뷰","comment","본문"])
    c_opt    = pick_col(lower, orig, ["option","옵션","기획","세트","구성","색상","호수"])
    c_help   = pick_col(lower, orig, ["help","도움","helpful","유용"])
    c_brand  = pick_col(lower, orig, ["brand","브랜드"])
    c_cuse   = pick_col(lower, orig, ["세분류","subcategory","category_use","용도"])

    for _, r in df.iterrows():
        brand = norm(r.get(c_brand)) if c_brand else ""
        pname = norm(r.get(c_pname)) if c_pname else ""
        rtext = norm(r.get(c_rtext)) if c_rtext else ""
        rdate_raw = r.get(c_rdate) if c_rdate else None
        review_date = parse_date_loose(rdate_raw) if rdate_raw is not None else None

        key = "|".join([
            "oliveyoung", brand, pname,
            str(rdate_raw if rdate_raw is not None else review_date or ""),
            (rtext[:80] if rtext else "")
        ])

        rows.append
