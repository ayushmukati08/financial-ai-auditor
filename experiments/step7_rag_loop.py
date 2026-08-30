"""
step7_rag_loop.py
End-to-End RAG Loop Test:
Runs user queries through the full Financial AI Auditor Pipeline:
1. Hybrid Retrieval (Dense BGE + Lexical BM25 -> RRF -> Cross-Encoder)
2. Evidence Context Assembly with [C1]..[C5] tags
3. Cited Financial Auditor Answer Generation with Gemini
"""

from core.pipeline import FinancialAIAuditorPipeline
from core.config import GEMINI_API_KEY, GEMINI_MODEL


SAMPLE_AUDIT_QUERIES = [
    "What were Apple's net sales and percentage change across Europe, Greater China, and Japan for 2025 compared to 2024?",
    "What factors drove the increase in Apple's research and development expenses in fiscal year 2025?",
    "What were Tesla's automotive revenues, automotive regulatory credits, and total revenues in 2023?",
    "What were Apple's share repurchase amounts and average prices paid per share in the three months ended September 27, 2025?",
]


def run_rag_loop():
    print("=" * 100)
    print("STEP 7: END-TO-END RAG SYNTHESIS LOOP (Hybrid Retrieval + Gemini Citations)")
    print("=" * 100)
    print(f"Gemini Model Configured : {GEMINI_MODEL}")
    print(f"GEMINI_API_KEY Detected : {'YES (Live Generation Active)' if (GEMINI_API_KEY and GEMINI_API_KEY.strip()) else 'NO (Set GEMINI_API_KEY in .env for Live LLM Output)'}")
    print("=" * 100 + "\n")

    pipeline = FinancialAIAuditorPipeline()

    for idx, query in enumerate(SAMPLE_AUDIT_QUERIES, start=1):
        print("\n" + "#" * 100)
        print(f"QUERY {idx}: \"{query}\"")
        print("#" * 100)

        result = pipeline.ask(question=query, top_k=5)

        print("\n--- 1. RETRIEVED EVIDENCE CHUNKS (Top 5 Ranked) ---")
        for ev in result["evidence"]:
            print(f"  {ev['citation_id']} | Type: {ev['chunk_type']:<5} | Score: {ev['rerank_score']:+.4f} | {ev['document_name']} | {ev['page']} | Section: '{ev['section']}'")
            lines = [l.strip() for l in ev["content"].split("\n") if l.strip()]
            snippet = "\n        ".join(lines[:3])
            print(f"      Snippet:\n        {snippet}")
            if len(lines) > 3:
                print("        ... [truncated]")

        print("\n--- 2. FINANCIAL AUDITOR RESPONSE ---")
        print(result["answer"])
        print("-" * 100)


if __name__ == "__main__":
    run_rag_loop()
