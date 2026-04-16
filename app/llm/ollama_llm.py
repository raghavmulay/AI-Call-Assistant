import ollama

SYSTEM_PROMPT = (
    "You are a college administration assistant. "
    "Answer questions about the college briefly and directly. "
    "Keep responses under 2 sentences. "
    "If you don't know something, say: 'I don't have that information. Please contact the admin office.'"
)

def generate_response(text: str) -> str:
    """Send user query to local Phi-3 Mini via Ollama and return the response."""
    response = ollama.chat(
        model="phi3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": text},
        ]
    )
    return response["message"]["content"].strip()
