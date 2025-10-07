# build_chunks.py
import os, re, pandas as pd

BASE = r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data"
STD_DIR = os.path.join(BASE, "data_oliveyoung", "processed_data", "reviews_oliveyoung")
OUT = os.path.join(BASE, "processed", "chunks.parquet")

SENT_RE = re.compile(r'(?<=[\.!?…\n])\s+')

def split_sents(t):
    s = [x.strip() for x in SENT_RE.split(str(t)) if str(x).strip()]
    return s if s else [str(t)]

def slide(sents, minc=200, maxc=500, stride=80):
    buf, out = "", []
    for s in sents:
        if len(buf) + len(s) + 1 <= maxc:
            buf = (buf + " " + s).strip()
        else:
            if len(buf) >= minc: out.append(buf)
            buf = (buf[-stride:] + " " + s).strip()
    if len(buf) >= minc: out.append(buf)
    return out

rows = []
for fn in os.listdir(STD_DIR):
    if not fn.endswith("_std.csv"): continue
    df = pd.read_csv(os.path.join(STD_DIR, fn), encoding="utf-8-sig")
    df["source_file"] = fn
    for _, r in df.iterrows():
        txt = str(r.get("review_text","")).strip()
        if len(txt) < 30: continue
        for chunk in slide(split_sents(txt)):
            rows.append({
                "text": chunk,
                "product_name": r.get("product_name",""),
                "brand": r.get("brand",""),
                "rating": r.get("rating", ""),
                "review_date": r.get("review_date",""),
                "url": r.get("product_url",""),
                "channel": r.get("channel","OliveYoung"),
                "source_file": fn,
            })

chunks = pd.DataFrame(rows)
chunks.to_parquet(OUT, index=False)
print(f"[OK] chunks -> {OUT}, rows={len(chunks)}")

import psycopg2
