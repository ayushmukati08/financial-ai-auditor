"""
Build retrieval-ready chunks from document sections.
Structure-aware chunking preserving text order, systematic context injection,
and first-class dual-format table chunks.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_chunks(
    sections: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Split each section into chunks while preserving exact document order,
    injecting systematic Section and Table Context, and producing a unified
    chunk schema for both text and table chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    chunk_counter = 0

    for section in sections:
        section_title = section.get("title", "Untitled Section")
        doc_name = section.get("document_name", "unknown")

        # Accumulator for consecutive narrative text spans
        text_buffer = []
        buffer_start_page = section.get("start_page", 1)
        buffer_end_page = section.get("start_page", 1)

        def flush_text_buffer():
            nonlocal chunk_counter, text_buffer, buffer_start_page, buffer_end_page
            if not text_buffer:
                return

            full_text = "\n".join(text_buffer).strip()
            text_buffer = []
            if not full_text:
                return

            pieces = splitter.split_text(full_text)
            for piece in pieces:
                chunk_id_str = f"{doc_name}_{chunk_counter:04d}"
                # Systematic text chunk content with section context
                formatted_content = f"Section: {section_title}\n\n{piece}"

                chunks.append({
                    "chunk_id": chunk_id_str,
                    "chunk_type": "text",
                    "document_name": doc_name,
                    "section_title": section_title,
                    "start_page": buffer_start_page,
                    "end_page": buffer_end_page,
                    "content": formatted_content,
                    "table_metadata": None,
                    "table_data": None,
                })
                chunk_counter += 1

        for item in section.get("content", []):
            if item["type"] == "span":
                sp = item["data"]
                text = sp.get("text", "").strip()
                if text:
                    if not text_buffer:
                        buffer_start_page = sp.get("page_number", section.get("start_page", 1))
                    buffer_end_page = sp.get("page_number", buffer_start_page)
                    text_buffer.append(text)

            elif item["type"] == "table":
                t = item["data"]
                raw_grid = t.get("data", [])
                raw_metadata = t.get("metadata", [])

                # 1. Capture preceding descriptive narrative context from text buffer before flushing
                preceding_context = ""
                if text_buffer:
                    for line in reversed(text_buffer[-6:]):
                        clean_line = line.strip()
                        words = clean_line.split()
                        # Search backward for the nearest meaningful narrative sentence.
                        # Avoid numeric/table-fragment lines that may appear immediately before
                        # the detected table because of imperfect PDF table extraction.
                        if len(words) < 3:
                            continue

                        if not any(ch.isalpha() for ch in clean_line):
                            continue

                        # Avoid lines that are mostly numeric/table-like
                        alpha_chars = sum(ch.isalpha() for ch in clean_line)
                        digit_chars = sum(ch.isdigit() for ch in clean_line)

                        if digit_chars > alpha_chars:
                            continue

                        preceding_context = clean_line
                        break

                # 2. Flush preceding narrative text first to preserve document order
                flush_text_buffer()

                # 3. Clean raw grid and build systematic Markdown table + clean 2D data
                clean_grid, table_md = _format_table_to_markdown(
                    raw_grid,
                    raw_metadata,
                    section_title,
                    preceding_context=preceding_context,
                )

                if clean_grid and table_md.strip():
                    chunk_id_str = f"{doc_name}_{chunk_counter:04d}"
                    t_page = t.get("page_number", section.get("start_page", 1))

                    chunks.append({
                        "chunk_id": chunk_id_str,
                        "chunk_type": "table",
                        "document_name": doc_name,
                        "section_title": section_title,
                        "start_page": t_page,
                        "end_page": t_page,
                        "content": table_md,
                        "table_metadata": raw_metadata if raw_metadata else None,
                        "table_data": clean_grid,
                    })
                    chunk_counter += 1

        # Flush any trailing text in the section
        flush_text_buffer()

    return chunks


CURRENCY_SYMBOLS = {"$", "₹", "Rs", "Rs.", "€", "£", "¥"}


def _format_table_to_markdown(
    grid: list[list],
    metadata: list[str],
    section_title: str,
    preceding_context: str = "",
) -> tuple[list[list[str]], str]:
    """
    Cleans raw 2D grid from PyMuPDF and converts it into a systematic Markdown table.
    Fuses isolated currency symbols ($, ₹, €, £, ¥) and percentage signs (%) at the row level,
    removes empty padding columns, and formats clean headers without dummy Col_X labels.
    Returns: (cleaned_2d_list, formatted_markdown_str)
    """
    if not grid:
        return [], ""

    # 1. Clean cells & remove completely empty rows
    cleaned_rows = []
    for row in grid:
        cleaned_row = [
            str(c).replace("\n", " ").strip() if c is not None else ""
            for c in row
        ]
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return [], ""

    # 2. Ensure rectangular grid
    num_cols = max(len(r) for r in cleaned_rows)
    for r in cleaned_rows:
        if len(r) < num_cols:
            r.extend([""] * (num_cols - len(r)))

    # 3. Normalize spaces in percentages and currencies in-place
    for r in range(len(cleaned_rows)):
        for c in range(len(cleaned_rows[0])):
            val = cleaned_rows[r][c]
            if "%" in val and val != "%":
                cleaned_rows[r][c] = val.replace(" %", "%").replace(" %", "%")
            for sym in {"$", "₹", "€", "£", "¥"}:
                if val.startswith(sym):
                    cleaned_rows[r][c] = sym + val[len(sym):].strip()
                    break

    # 4. Column-level dedicated currency symbol merge
    c = 0
    while c < len(cleaned_rows[0]) - 1:
        col_vals = [cleaned_rows[r][c] for r in range(len(cleaned_rows))]
        non_empty = [v for v in col_vals if v]
        if non_empty and all(v in CURRENCY_SYMBOLS for v in non_empty):
            for r in range(len(cleaned_rows)):
                sym = cleaned_rows[r][c]
                if sym:
                    val = cleaned_rows[r][c + 1]
                    merged = f"{sym}{val}" if sym in {"$", "₹", "€", "£", "¥"} else f"{sym} {val}"
                    cleaned_rows[r][c + 1] = merged
            for r in range(len(cleaned_rows)):
                cleaned_rows[r].pop(c)
            continue
        c += 1

    # 5. Column-level dedicated percentage symbol merge
    c = 1
    while c < len(cleaned_rows[0]):
        col_vals = [cleaned_rows[r][c] for r in range(len(cleaned_rows))]
        non_empty = [v for v in col_vals if v]
        if non_empty and all(v == "%" for v in non_empty):
            for r in range(len(cleaned_rows)):
                pct = cleaned_rows[r][c]
                if pct and cleaned_rows[r][c - 1]:
                    cleaned_rows[r][c - 1] = f"{cleaned_rows[r][c - 1]}%"
            for r in range(len(cleaned_rows)):
                cleaned_rows[r].pop(c)
            continue
        c += 1

    # 6. In-place row-level fallback for any remaining isolated symbols
    for r in range(len(cleaned_rows)):
        row = cleaned_rows[r]
        for c in range(len(row)):
            if row[c] in CURRENCY_SYMBOLS:
                next_c = c + 1
                while next_c < len(row) and not row[next_c]:
                    next_c += 1
                if next_c < len(row):
                    val = row[next_c]
                    merged = f"{row[c]}{val}" if row[c] in {"$", "₹", "€", "£", "¥"} else f"{row[c]} {val}"
                    row[next_c] = merged
                    row[c] = ""
            elif row[c] == "%":
                for prev_c in range(c - 1, -1, -1):
                    if row[prev_c]:
                        row[prev_c] = f"{row[prev_c]}%"
                        row[c] = ""
                        break

    # 7. Drop columns that are completely empty across the entire table
    final_cols = len(cleaned_rows[0])
    non_empty_indices = [
        col_idx for col_idx in range(final_cols)
        if any(cleaned_rows[r][col_idx] != "" for r in range(len(cleaned_rows)))
    ]
    if not non_empty_indices:
        return [], ""

    final_rows = [
        [cleaned_rows[r][col_idx] for col_idx in non_empty_indices]
        for r in range(len(cleaned_rows))
    ]

    # 8. Format systematic Markdown representation
    lines = [f"Section: {section_title}"]

    # Systematic context block
    context_parts = []
    if preceding_context:
        context_parts.append(preceding_context)
    if metadata:
        context_parts.append(" | ".join(metadata))

    if context_parts:
        lines.append("")
        lines.append("Table context:")
        lines.append(" — ".join(context_parts))

    # 9. Header resolution for Markdown representation (honest 3-case rule)
    num_final_cols = len(final_rows[0])
    clean_meta = [m.strip() for m in metadata if m.strip()] if metadata else []

    if clean_meta and len(clean_meta) == num_final_cols:
        header_cells = [c if c else " " for c in clean_meta]
        data_rows = final_rows
    elif clean_meta and len(clean_meta) == num_final_cols - 1:
        header_cells = [""] + [c if c else " " for c in clean_meta]
        data_rows = final_rows
    else:
        header_cells = [""] * num_final_cols
        data_rows = final_rows

    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("| " + " | ".join(["---"] * len(header_cells)) + " |")

    # Data rows
    for row in data_rows:
        padded_row = row[:len(header_cells)] + [""] * max(0, len(header_cells) - len(row))
        lines.append("| " + " | ".join(padded_row) + " |")

    return final_rows, "\n".join(lines)