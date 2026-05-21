import ollama
import time

MODEL = "phi3:mini"

SYSTEM_PROMPT = (
    "You are a college assistant for general conversation only. "
    "NEVER invent or guess college-specific data such as timings, phone numbers, building names, fees, dates, or staff names. "
    "If the user asks anything college-specific (office, fees, timings, location, admission, documents, hostel, placements), "
    "respond with exactly: 'I don't have that information. Please contact the admin office at 020-12345678.' "
    "Only answer general knowledge questions, greetings, or conversational queries. "
    "Keep all responses under 2 sentences."
)

RAG_SYSTEM_PROMPT = (
    "You are a college syllabus assistant. "
    "Answer ONLY using the context provided below. "
    "Do NOT use any prior knowledge or make assumptions beyond the context. "
    "If the answer is not present in the context, respond with exactly: "
    "'I could not find that in the syllabus.' "
    "Be specific — list subject names, unit topics, or details exactly as they appear in the context."
)


def _chat(system: str, user: str) -> str:
    start = time.time()
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        options={
            "num_predict": 100,   # short responses for voice
            "temperature": 0.1,
            "top_k": 20,
            "top_p": 0.7,
        },
    )
    print(f"[LLM Time]: {time.time() - start:.2f}s")
    return response["message"]["content"].strip()


def generate_response(text: str) -> str:
    """Plain LLM — only for non-syllabus intents (time, contact, etc.)."""
    return _chat(SYSTEM_PROMPT, text)


def generate_rag_response(query: str, context: str) -> str:
    """RAG call — answer must be grounded in retrieved context."""
    user_message = (
        f"Context from syllabus documents:\n"
        f"---\n{context}\n---\n\n"
        f"Question: {query}"
    )
    return _chat(RAG_SYSTEM_PROMPT, user_message)
