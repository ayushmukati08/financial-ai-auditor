"""
citation_prompt.py
Strict prompt templates and context formatting for citation-forced financial auditor generation.
"""

AUDITOR_SYSTEM_PROMPT = """You are a senior financial auditor AI assistant. You answer user queries using ONLY the retrieved context chunks provided below.

Strict Financial Auditing Rules:
1. Every factual sentence or numerical statement MUST be immediately cited using its citation tag, e.g. [C1] or [C2].
2. If multiple chunks support a statement, combine citation tags like [C1][C3].
3. For financial numbers:
   - Always state the exact currency units ($ in millions, billions, thousands, or per share) as reported in the source.
   - Always state the exact fiscal period (e.g. Fiscal Year 2025, Year Ended December 31, 2023, Three Months Ended September 27, 2025).
4. If the retrieved context does not contain sufficient facts to answer all parts of the question, answer what is present and explicitly state what is missing:
   "Based on the provided documents, [available facts]. The retrieved documents do not contain information regarding [missing item]."
5. Do NOT hallucinate, extrapolate, or use external knowledge not present in the context.
""".strip()


def build_auditor_prompt(question: str, evidence: list[dict]) -> str:
    """
    Builds the complete auditor prompt with formatted citation context blocks.
    """
    context_blocks = []
    for ev in evidence:
        citation_id = ev.get("citation_id", "[C?]")
        chunk_type = ev.get("chunk_type", "TEXT")
        doc_name = ev.get("document_name", "unknown")
        page = ev.get("page", "N/A")
        section = ev.get("section", "N/A")
        content = ev.get("content", "")

        block = (
            f"--- {citation_id} ({chunk_type} | Source: {doc_name} | {page} | Section: '{section}') ---\n"
            f"{content}"
        )
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)
    max_c = len(evidence)

    prompt = f"""{AUDITOR_SYSTEM_PROMPT}

Context:
{context_text}

Question:
{question}

Audited Answer (with [C1]..[C{max_c}] citations):"""

    return prompt
