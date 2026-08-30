"""
Comprehensive Retrieval Testing Suite (Step 6 Extended)

Runs an extensive battery of 8 financial audit queries testing:
1. Exact financial metric lookup in tables
2. Footnote / fine-print text lookup
3. Narrative MD&A causal explanations
4. Cross-filing separation (Apple vs Tesla)
5. Metadata filtering (tables only vs text only)
6. Complex multi-term financial queries
"""

import sys
from core.retrieval.vector_store import get_vector_store
from core.retrieval.retriever import retrieve_with_scores


TEST_QUERIES = [
    {
        "id": "T1_TABLE_REPURCHASE",
        "category": "Table Lookup",
        "query": "What was the average price paid per share for Apple's common stock purchases between August 3, 2025 and August 30, 2025?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 22,
        "filter": None,
    },
    {
        "id": "T2_TABLE_SEGMENT_SALES",
        "category": "Table Lookup",
        "query": "What were Apple's net sales in Greater China in 2025, 2024, and 2023?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 25,
        "filter": None,
    },
    {
        "id": "T3_TABLE_GROSS_MARGIN",
        "category": "Table Lookup",
        "query": "What was Apple's Services gross margin percentage in 2025 and 2024?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 27,
        "filter": None,
    },
    {
        "id": "T4_FOOTNOTE_REPURCHASE_PLAN",
        "category": "Footnote / Program Authorization",
        "query": "How much was authorized under Apple's May 2024 and May 2025 share repurchase programs?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 22,
        "filter": None,
    },
    {
        "id": "T5_NARRATIVE_OPEX_DRIVERS",
        "category": "Narrative Explanation (MD&A)",
        "query": "What factors drove the increase in selling, general and administrative expenses during 2025?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 28,
        "filter": None,
    },
    {
        "id": "T6_TESLA_CYBERTRUCK_RD",
        "category": "Cross-Filing (Tesla)",
        "query": "Why did Tesla's research and development expenses increase in 2023?",
        "expected_doc": "tesla_10K.pdf",
        "expected_page": 42,
        "filter": {"document_name": "tesla_10K.pdf"},
    },
    {
        "id": "T7_FILTERED_TABLES_ONLY",
        "category": "Metadata Filtered (Tables Only)",
        "query": "Consolidated Balance Sheets total assets, total liabilities and shareholders equity",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 34,
        "filter": {"document_name": "apple_10k.pdf", "chunk_type": "table"},
    },
    {
        "id": "T8_TAX_DISPUTE_STATE_AID",
        "category": "Legal / Tax Footnote",
        "query": "What was the outcome and financial impact of the European Commission State Aid decision for Apple?",
        "expected_doc": "apple_10k.pdf",
        "expected_page": 44,
        "filter": None,
    },
]


def run_test_suite(top_k: int = 3):
    print("=" * 95)
    print("FINANCIAL RETRIEVAL EVALUATION SUITE")
    print("=" * 95)

    vector_store = get_vector_store()
    total_docs = vector_store._collection.count()
    print(f"Connected to ChromaDB: {total_docs} total chunk vectors loaded.\n")

    passed_tests = 0

    for idx, test in enumerate(TEST_QUERIES, start=1):
        print("=" * 95)
        print(f"TEST {idx:02d} / {len(TEST_QUERIES)}: [{test['category']}] (ID: {test['id']})")
        print("=" * 95)
        print(f"  Query        : \"{test['query']}\"")
        if test["filter"]:
            print(f"  Filter       : {test['filter']}")
        print(f"  Target Expectation : Doc: '{test['expected_doc']}' | Near Page: {test['expected_page']}\n")

        results = retrieve_with_scores(
            query=test["query"],
            top_k=top_k,
            filter_dict=test["filter"],
        )

        matched_target = False
        for rank, (doc, score) in enumerate(results, start=1):
            meta = doc.metadata
            doc_name = meta.get("document_name", "")
            start_p = meta.get("start_page", 0)
            end_p = meta.get("end_page", 0)
            chunk_type = meta.get("chunk_type", "")
            chunk_id = meta.get("chunk_id", "")
            section = meta.get("section", "")

            # Check if this rank matches expected doc and is within 2 pages of target
            is_match = (
                doc_name == test["expected_doc"]
                and (start_p - 2 <= test["expected_page"] <= end_p + 2)
            )
            if is_match and not matched_target:
                matched_target = True
                match_tag = f"[*] [TARGET HIT - Rank {rank}]"
            else:
                match_tag = ""

            print(f"  --- [Rank {rank}] {match_tag} | Distance: {score:.4f} | Type: {chunk_type.upper()} ---")
            print(f"      ID      : {chunk_id} | Doc: {doc_name} | Pages: {start_p}-{end_p}")
            print(f"      Section : {section}")
            
            # 4-line snippet
            lines = [line.strip() for line in doc.page_content.split("\n") if line.strip()]
            snippet = "\n      ".join(lines[:4])
            print(f"      Snippet :\n      {snippet}")
            if len(lines) > 4:
                print("      ... [truncated]")
            print()

        if matched_target:
            passed_tests += 1
            print(f"  >>> RESULT: PASS (Target chunk successfully retrieved in Top-{top_k})\n")
        else:
            print(f"  >>> RESULT: REVIEW (Target was not within Top-{top_k})\n")

    print("=" * 95)
    print(f"FINAL AUDIT SCORE: {passed_tests} / {len(TEST_QUERIES)} TESTS PASSED ({passed_tests/len(TEST_QUERIES)*100:.1f}%)")
    print("=" * 95)


def query_interactive():
    vector_store = get_vector_store()
    print("\n" + "=" * 80)
    print("INTERACTIVE RETRIEVAL CLI")
    print("Type your query (or 'exit' to quit):")
    print("=" * 80)

    while True:
        try:
            user_q = input("\nEnter query: ").strip()
            if not user_q or user_q.lower() in {"exit", "quit", "q"}:
                break

            results = retrieve_with_scores(query=user_q, top_k=3)
            print(f"\nTop 3 results for: \"{user_q}\"\n")
            for rank, (doc, score) in enumerate(results, start=1):
                meta = doc.metadata
                print(f"[{rank}] Distance: {score:.4f} | {meta.get('document_name')} | Page {meta.get('start_page')}-{meta.get('end_page')} | Type: {meta.get('chunk_type')}")
                print(f"    Section: {meta.get('section')}")
                lines = [l.strip() for l in doc.page_content.split("\n") if l.strip()]
                print(f"    Preview: {' | '.join(lines[:3])}\n")
        except (KeyboardInterrupt, EOFError):
            break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        query_interactive()
    else:
        run_test_suite(top_k=3)
