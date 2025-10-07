from rag_pipeline import answer_with_rag
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    q = input("질문: ")
    label, ans = answer_with_rag(q, client)
    print(f"[label] {label}\n")
    print(ans)