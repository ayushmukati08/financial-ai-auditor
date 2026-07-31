SYSTEM_INSTRUCTION = """
You are an expert financial filing assistant.

Answer accurately.

If you don't know,
reply exactly:

I don't know.
""".strip()


def build_answer_prompt(question: str):

    return f"""
{SYSTEM_INSTRUCTION}
    
Question:
{question}
    
Answer:
""".strip()