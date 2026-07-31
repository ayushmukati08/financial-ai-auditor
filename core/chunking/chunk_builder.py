"""
Build retrieval-ready chunks from document sections.
Structure-aware chunking logic.
Promote clean logic here from experiments/step4_chunking.py.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter


def build_chunks(
    sections: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Split each section into overlapping chunks while preserving metadata.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = []

    chunk_id = 0

    for section in sections:

        # Convert spans into plain text
        text = "\n".join(
            span["text"]
            for span in section["spans"]
        )

        split_chunks = splitter.split_text(text)

        for piece in split_chunks:

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": piece,
                    "section": section["title"],
                    "document_name": section["document_name"],
                    "start_page": section["start_page"],
                    "end_page": section["end_page"],
                }
            )

            chunk_id += 1

    return chunks