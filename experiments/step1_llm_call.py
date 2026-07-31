"""
step1_llm_call.py
Goal: confirm we can call the LLM API and get a clean response back.
No context, no RAG yet — just the raw mechanic.
"""

from core.llm.service import generate_answer

def main():
    question = "What is a 10-Q filing, in one sentence?"
    # question = "How are you?"
    answer = generate_answer(question)

    print("QUESTION:", question)
    if answer is None:
        print("Couldn't contact Gemini.")
    else:
        print("ANSWER:", answer)


if __name__ == "__main__":
    main()
