from app.llm.ollama_llm import generate_response

# Fixed responses for known intents — keyword : response
INTENT_MAP = {
    "time":    "College is open from 9 AM to 5 PM, Monday to Saturday.",
    "contact": "You can contact the administration at 020-12345678 or admin@college.edu.",
    "alert":   "Security Alert: Unauthorized access was detected near Gate 2 at 3:45 PM. Please stay vigilant.",
    "notice":  "Notice: Mid-semester exams are scheduled from 15th to 20th of this month. Check the notice board for details.",
}

def get_answer(text: str) -> str:
    """Check rule-based intents first; fall back to LLM if no match."""
    lowered = text.lower()
    for keyword, response in INTENT_MAP.items():
        if keyword in lowered:
            return response
    return generate_response(text)
