import sys
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:

from backend.app.ai.llm.ollama_llm import generate_response

# If any of these words appear, don't let LLM answer — route to safe fallback
_COLLEGE_KEYWORDS = {
    "office", "timing", "timings", "fee", "fees", "hostel", "admission",
    "document", "certificate", "placement", "scholarship", "branch", "cutoff",
    "eligibility", "contact", "phone", "number", "address", "location",
    "building", "block", "floor", "email", "website", "portal", "deadline",
    "merit", "classes", "semester", "exam", "library", "accounts", "principal",
}

_SAFE_FALLBACK = "I don't have that information. Please contact the admin office at 020-12345678."


def handle_general_chat(query: str) -> str:
    words = set(query.lower().split())
    if words & _COLLEGE_KEYWORDS:
        return _SAFE_FALLBACK
    return generate_response(query)
