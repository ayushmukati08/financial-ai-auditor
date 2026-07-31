from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

API_KEY=os.getenv("GEMINI_API_KEY")
MODEL=os.getenv("GEMINI_MODEL")

persistent_directory = "db/chroma_db"
client = genai.Client(api_key=API_KEY)

# Load embeddings and vector store
embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

db = Chroma(
    persist_directory=persistent_directory,
    embedding_function=embedding_model,
    collection_metadata={"hnsw:space": "cosine"}  
)

# Search for relevant documents
def retrieve_chunks(query: str, k: int = 5):
# def retrieve_chunks(query: str, k: int = 5, score_threshold: float = 0.3):
    # retriever = db.as_retriever(search_kwargs={"k": 5})

    # retriever = db.as_retriever(
    #     search_type="mmr",
    #     search_kwargs={
    #         "k": 5,
    #         "fetch_k": 20
    #     }
    # )

    # retriever = db.as_retriever(
    #     search_type="similarity_score_threshold",
    #     search_kwargs={
    #         "k": k,
    #         "score_threshold": score_threshold  # Only return chunks with cosine similarity ≥ 0.3
    #     }
    # )
    
    # return retriever.invoke(query)
    
    # replace as_retriever() temporarily with similarity_search_with_relevance_scores() returns (Document, Score)
    results = db.similarity_search_with_relevance_scores(
        query=query,
        k=k
    )
    return results
    
    
def build_citation_prompt(query: str, results) -> str:
    """
    Assigns each retrieved chunk a short id (C1, C2, ...) and instructs
    the model to tag every factual sentence with the id it relied on.
    """
    context_blocks = []
    
    # used by the as_retriever() in the retrieve_chunks()
    # for i, doc in enumerate(chunks, 1):
    #     context_blocks.append(f"[C{i}] (source: {doc.metadata.get('source')}, page {doc.metadata.get('page', 0) + 1})\n{doc.page_content}")
    
    # used by the similarity_search_with_relevance_scores() in the retrieve_chunks()
    for i, (doc, score) in enumerate(results, 1):
        context_blocks.append(
            f"[C{i}] (Source: {doc.metadata['source']}, "
            f"Page: {doc.metadata['page'] + 1})\n"
            f"{doc.page_content}"
        )
        
    context_text = "\n\n".join(context_blocks)

    return f"""You must answer using ONLY the context chunks provided below.

Every sentence in your answer that makes a factual claim MUST end with a
citation tag referencing the chunk it came from, like [C1] or [C2].
If a sentence combines information from multiple chunks, include all
relevant tags, like [C1][C3].
If the answer cannot be fully answered from the provided context,
respond exactly:
"I don't have enough information in the retrieved documents."
Do not use outside knowledge.

Context:
{context_text}

Question: {query}

Answer (with citation tags on every factual sentence):"""


def ask_with_citations(query: str) -> str:
    # while using as_retriever() in retrieve_chunks()
    # chunks = retrieve_chunks(query)
    # if not chunks:
    #         return "No relevant context found for this question."
    
    # when using similarity_search_with_relevance_scores() in retrieve_chunks()
    results = retrieve_chunks(query)
    
    if not results:
        return "No relevant context found for this question."

    print("\nRetrieved Chunks")
    print("=" * 60)

    for i, (doc, score) in enumerate(results, 1):
        print(f"C{i}")
        print(f"Score  : {score:.3f}")
        print(f"Page   : {doc.metadata['page'] + 1}")
        print(f"Source : {os.path.basename(doc.metadata['source'])}")
        print("-" * 60)

    prompt = build_citation_prompt(query, results)
    
    response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
    
    return response.text
    
    
# def main():
#     query = "What is chronic kidney disease?"
#     answer = ask_with_citations(query)
    
#     print("QUESTION:", query)
#     print("\n--- CITED ANSWER ---")
#     print(answer)
    
    
def main():
    print("=" * 60)
    print("Financial AI Auditor")
    print("=" * 60)
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        query = input("Ask a question: ").strip()

        if query.lower() in {"exit", "quit"}:
            print("\nExiting...")
            break

        if not query:
            print("Please enter a question.\n")
            continue

        answer = ask_with_citations(query)

        print("\n" + "=" * 60)
        print("QUESTION:")
        print(query)
        print("\nANSWER:")
        print(answer)
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()


# relevant_docs = retriever.invoke(query)

# print(f"User Query: {query}")
# # Display results
# print("--- Context ---")
# for i, doc in enumerate(relevant_docs, 1):
#     print(f"Source : {doc.metadata['source']}\n")
#     print(f"Page   : {doc.metadata['page'] + 1}\n")
#     print(f"Document {i}:\n{doc.page_content}\n")
    
    
# # Combine the query and the relevant document contents
# combined_input = f"""Based on the following documents, please answer this question: {query}

# Documents:
# {chr(10).join([f"- {doc.page_content}" for doc in relevant_docs])}

# Please provide a clear, helpful answer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer that question based on the provided documents."
# """

# # Create a ChatOpenAI model
# model = genai.Client(api_key=API_KEY)

# # Define the messages for the model
# messages = f"""
# You are a helpful assistant.

# {combined_input}
# """

# # Invoke the model with the combined input
# result = model.models.generate_content(
#             model=MODEL,
#             contents=messages
#         )
# # Display the full result and content only
# print("\n--- Generated Response ---")
# # print("Full result:")
# # print(result)
# print("Content only:")
# print(result.text)