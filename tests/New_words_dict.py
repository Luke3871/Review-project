# import os, re, math
# import pandas as pd
# import numpy as np
# from collections import Counter, defaultdict
# from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer, TfidfTransformer
# from sklearn.preprocessing import minmax_scale

# # ======================
# # 0) 설정
# # ======================
# CSV_PATH = r"./data/merged_all.csv"  # 상대 경로로 변경  
# OUT_DIR  = r"./outputs"; os.makedirs(OUT_DIR, exist_ok=True)

# RECENT_DAYS    = 90
# MIN_TOKEN_LEN  = 2
# LOWERCASE_EN   = True
# eps = 1e-9

# # 불용어는 과도하게 빼지 말고, 기능어/감탄사 위주로만
# STOPWORDS = {
#     "제품","사용","정말","그냥","조금","그리고","하지만","또한","합니다","했어요",
#     "있어요","입니다","습니다","같아요","같은","있는","없는","해서","이번","지난",
#     "거의","계속","살짝","이거","저는","제가","그게","그건","그때","근데","그래서"
# }

# # ===== 토큰화: 한글+영문+숫자+하이픈(mlbb, tone-up, spf50) 보존 =====
# token_pat = re.compile(r"[가-힣a-zA-Z0-9][가-힣a-zA-Z0-9\-]{%d,}" % (MIN_TOKEN_LEN-1))

# def normalize_text(s: str) -> str:
#     s = str(s)
#     # 반복 문자 정규화(넘치는 ㅋㅋㅋ, ㅎㅎㅎ, ~~ → 2개로)
#     s = re.sub(r"(.)\1{2,}", r"\1\1", s)
#     # 영문 소문자
#     if LOWERCASE_EN:
#         s = s.lower()
#     # 토큰 추출
#     toks = token_pat.findall(s)
#     # 불용어 제거
#     toks = [t for t in toks if t not in STOPWORDS]
#     return " ".join(toks)

# # ===== 데이터 로드 =====
# df = pd.read_csv(CSV_PATH, encoding="utf-8", low_memory=False)
# df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
# df = df.dropna(subset=["Review"]).copy()

# docs_all    = df["Review"].astype(str).map(normalize_text).tolist()
# cutoff      = df["Date"].max() - pd.Timedelta(days=RECENT_DAYS)
# idx_recent  = (df["Date"] >= cutoff).to_numpy()
# idx_prev    = ~idx_recent
# n_recent    = max(1, idx_recent.sum())
# n_prev      = max(1, idx_prev.sum())

# def rare_bursty_terms(docs_all, idx_recent, idx_prev, ngram=(1,1), topk=100,
#                       df_prev_max=1, df_recent_min=5, lift_min=5.0,
#                       add_examples=True, colname="term"):
#     # (1) DF 계산용: binary=True
#     cv_df = CountVectorizer(ngram_range=ngram, token_pattern=r"(?u)\b[^\s]{%d,}\b" % MIN_TOKEN_LEN,
#                             lowercase=False, binary=True)
#     X_all_df  = cv_df.fit_transform(docs_all)
#     terms     = cv_df.get_feature_names_out()

#     X_prev_df   = X_all_df[idx_prev]
#     X_recent_df = X_all_df[idx_recent]
#     df_prev     = np.asarray(X_prev_df.sum(axis=0)).ravel()
#     df_recent   = np.asarray(X_recent_df.sum(axis=0)).ravel()
#     df_all      = np.asarray(X_all_df.sum(axis=0)).ravel()

#     rate_prev   = (df_prev   + eps) / (idx_prev.sum()   + eps)
#     rate_recent = (df_recent + eps) / (idx_recent.sum() + eps)
#     lift        = rate_recent / (rate_prev + eps)

#     # (2) TF-IDF: 동일 vocab으로 카운트 → Transformer
#     cv_cnt = CountVectorizer(ngram_range=ngram, token_pattern=r"(?u)\b[^\s]{%d,}\b" % MIN_TOKEN_LEN,
#                              lowercase=False, vocabulary=cv_df.vocabulary_, binary=False)
#     X_all_cnt = cv_cnt.fit_transform(docs_all)
#     tfidf_tr  = TfidfTransformer().fit(X_all_cnt[idx_prev])       # 과거 기준 IDF
#     recent_tfidf_mean = tfidf_tr.transform(X_all_cnt[idx_recent]).mean(axis=0).A1

#     # (3) 필터: 과거 희귀 & 최근 충분, lift 큼
#     mask = (df_prev <= df_prev_max) & (df_recent >= df_recent_min) & (lift >= lift_min)
#     cand_terms = terms[mask]
#     out = pd.DataFrame({
#         colname: cand_terms,
#         "df_prev": df_prev[mask],
#         "df_recent": df_recent[mask],
#         "df_all": df_all[mask],
#         "lift": lift[mask],
#         "recent_tfidf": recent_tfidf_mean[mask],
#     }).sort_values(["lift","recent_tfidf","df_recent"], ascending=False).head(topk)

#     if add_examples and len(out) > 0:
#         # 간단 예문 2개 샘플링
#         def sample_examples(term):
#             # 원문 검색을 위해 정규화 전 리뷰 사용
#             cnt, ex = 0, []
#             for raw in df.loc[idx_recent, "Review"]:
#                 if isinstance(raw, str) and term in normalize_text(raw):
#                     ex.append(raw.strip().replace("\n"," ")[:120])
#                     cnt += 1
#                     if cnt >= 2: break
#             return " | ".join(ex)
#         out["examples"] = out[colname].map(sample_examples)
#     return out

# # === 실행: 유니그램/빅그램 ===
# uni = rare_bursty_terms(docs_all, idx_recent, idx_prev, ngram=(1,1), topk=100,
#                         df_prev_max=1, df_recent_min=5, lift_min=5.0, colname="term")
# bi  = rare_bursty_terms(docs_all, idx_recent, idx_prev, ngram=(2,2), topk=100,
#                         df_prev_max=1, df_recent_min=3, lift_min=4.0, colname="bigram")

# uni.to_csv(os.path.join(OUT_DIR, "rare_bursty_unigram.csv"), index=False, encoding="utf-8-sig")
# bi.to_csv (os.path.join(OUT_DIR, "rare_bursty_bigram.csv"), index=False, encoding="utf-8-sig")
# print("saved:", OUT_DIR)



"""
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
"""

import os, re, json, time, random
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# ================= 설정 =================
CSV_PATH   = r"./data/merged_all.csv"      # 데이터 경로 (상대 경로로 변경)
OUT_DIR    = r"./outputs"; os.makedirs(OUT_DIR, exist_ok=True)
MODEL_NAME = "gpt-4o-mini"
CHUNK_SIZE = 400        # 한 번에 보낼 문장 수 (200~500 권장)
TEMPERATURE = 0.2
TOP_K_PER_RESP = 20     # 모델 응답 내 최대 후보 수(프롬프트에 반영)

# ================= 환경 변수/클라이언트 =================
load_dotenv()
os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()
# ================= 프롬프트 템플릿 =================
PROMPT_TEMPLATE = f"""
역할: 당신은 한국어 화장품 리뷰 텍스트에서 "실제로 등장한 신조어 후보"만 엄격하게 추출하는 필터입니다. 
환각 생성 금지. 입력에 없는 단어 금지. 결과가 없으면 빈 배열([])을 반환합니다.

[정의]
신조어 후보 = 다음 중 하나에 해당하며, 입력 텍스트 "그대로의 표면형"이 존재하는 표현
- morph(형태 파생/의태·의성/조어): 예) 뽀용하다, 화잘먹
- abbrev(약어/축약/철자 변형)

[배제 규칙(모두 충족)]
- 일상 일반어/감탄사/평범한 수식어: 좋아요, 촉촉하다, 매우, 진짜, 가성비, 생각보다 등 → 제외

- 입력에 "직접 등장하지 않은" 추측 단어 생성 금지
- 한국어 사전에 흔한 일반 품사 단어만으로 된 표현(예: ‘부드럽다’, ‘자극적이다’) → 제외

[출력 형식(반드시 JSON 배열, 그 외 텍스트 금지)]  
"term": "<입력에 실제로 등장한 표면형 그대로>",
"type": "<morph|hybrid|slang|abbrev>",
"variants": ["<동일 의미의 변형 표기들(입력에 실제로 등장한 것만)>"],
"definition": "<문맥에 근거한 한 줄 의미 추정(모호하면 '확실하지않음')>",
"evidence": ["<입력에서 그대로 복사한 문장1>", "<문장2>"]

"""

def normalize_text(s: str) -> str:
    s = str(s)
    s = re.sub(r"(.)\1{2,}", r"\1\1", s)  # ㅋㅋㅋㅋ -> ㅋㅋ
    return s

def sentences_from_reviews(series: pd.Series):
    sents = []
    for txt in series.astype(str):
        txt = normalize_text(txt)
        # 줄바꿈/마침표/물음표/느낌표 기준 단순 분할
        for s in re.split(r"[\n\.!?]+", txt):
            s = s.strip()
            if len(s) >= 6:
                sents.append(s)
    return sents

def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def call_gpt(prompt: str, retries=5):
    for attempt in range(1, retries+1):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role":"user","content":prompt}],
                temperature=TEMPERATURE
            )
            txt = resp.choices[0].message.content.strip()
            # 코드블록 제거
            txt = re.sub(r"^```json|```$", "", txt, flags=re.I|re.M).strip()
            data = json.loads(txt)
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            # 지수 백오프
            time.sleep(min(10, 2**attempt) + random.random())
            if attempt == retries:
                return []

def main():
    # 데이터 로드
    df = pd.read_csv(CSV_PATH, low_memory=False)
    assert "Review" in df.columns, "Review 컬럼이 필요합니다."
    df = df.dropna(subset=["Review"])

    sents = sentences_from_reviews(df["Review"])
    print(f"문장 수: {len(sents)}")

    rows = []
    for cid, chunk in enumerate(chunks(sents, CHUNK_SIZE), start=1):
        chunk_text = "\n".join(chunk)
        prompt = PROMPT_TEMPLATE.replace("{{REVIEW_CHUNK}}", chunk_text)
        items = call_gpt(prompt)
        for it in items:
            term = str(it.get("term","")).strip()
            if not term:
                continue
            variants = it.get("variants", [])
            if isinstance(variants, str):
                variants = [variants]
            rows.append({
                "chunk_id": cid,
                "term": term,
                "variants": ";".join([v.strip() for v in variants if v]),
                "type": it.get("type",""),
                "definition": it.get("definition",""),
                "evidence": " | ".join(it.get("evidence", [])[:2])
            })

    raw = pd.DataFrame(rows)
    raw_path = os.path.join(OUT_DIR, "gpt_slang_candidates_raw.csv")
    raw.to_csv(raw_path, index=False, encoding="utf-8-sig")
    print("원본 후보:", raw_path)

    if not raw.empty:
        agg = (raw.groupby("term", as_index=False)
                  .agg({
                      "variants":"first",
                      "type":"first",
                      "definition":"first",
                      "evidence":"first",
                      "chunk_id":"nunique"
                  })
                  .rename(columns={"chunk_id":"support_chunks"})
               )
        agg = agg.sort_values(["support_chunks"], ascending=False)
        agg_path = os.path.join(OUT_DIR, "gpt_slang_candidates_agg.csv")
        agg.to_csv(agg_path, index=False, encoding="utf-8-sig")
        print("집계 후보:", agg_path)

if __name__ == "__main__":
    main()