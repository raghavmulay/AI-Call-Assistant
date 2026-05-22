import sys
import os

# Ensure project root is on path for app.* imports
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:

from backend.app.ai.rag.rag_pipeline import get_rag_answer

FALLBACK = "I could not find that information in the documents."


def handle_rag(query: str) -> str:
    """
    Called ONLY for intents that genuinely need document retrieval:
    hostel_rules, syllabus_query, policy_query, admission_process.
    """
    result = get_rag_answer(query)
    return result if result else FALLBACK
