from backend.app.ai.intent.intent_detector import detect_intent, _extract_branch
from backend.app.ai.session.session import get as get_session, update as update_session, clear_pending

from backend.app.ai.handlers.greeting_handler    import handle_greeting, handle_thanks, handle_farewell
from backend.app.ai.handlers.fees_handler         import handle_fees
from backend.app.ai.handlers.documents_handler    import handle_documents
from backend.app.ai.handlers.counseling_handler   import handle_counseling
from backend.app.ai.handlers.admission_handler    import (
    handle_cutoff, handle_eligibility, handle_admission_dates,
    handle_admission_process, handle_branches, handle_placements,
    handle_scholarship, handle_hostel, handle_contact,
    handle_office_timing, handle_office_location,
)
from backend.app.ai.handlers.rag_handler          import handle_rag
from backend.app.ai.handlers.general_chat_handler import handle_general_chat
from backend.app.ai.handlers.emergency_handler    import handle_emergency, handle_alert

_ROUTER = {
    "greeting":           lambda q, s, e: handle_greeting(),
    "thanks":             lambda q, s, e: handle_thanks(),
    "farewell":           lambda q, s, e: handle_farewell(),

    "fees":               lambda q, s, e: handle_fees(q, s, e),
    "documents":          lambda q, s, e: handle_documents(q, s),
    "cutoff":             lambda q, s, e: handle_cutoff(),
    "eligibility":        lambda q, s, e: handle_eligibility(),
    "admission_dates":    lambda q, s, e: handle_admission_dates(q, s),
    "admission_process":  lambda q, s, e: handle_admission_process(),
    "branches":           lambda q, s, e: handle_branches(),
    "placements":         lambda q, s, e: handle_placements(q, s, e),
    "scholarship":        lambda q, s, e: handle_scholarship(),
    "hostel":             lambda q, s, e: handle_hostel(q, s),
    "contact":            lambda q, s, e: handle_contact(q, s),
    "office_timing":      lambda q, s, e: handle_office_timing(q, s),
    "office_location":    lambda q, s, e: handle_office_location(q, s),
    "counseling":         lambda q, s, e: handle_counseling(q, s),

    "hostel_rules":       lambda q, s, e: handle_rag(q),
    "syllabus_query":     lambda q, s, e: handle_rag(q),
    "policy_query":       lambda q, s, e: handle_rag(q),

    "emergency":          lambda q, s, e: handle_emergency(),
    "alert":              lambda q, s, e: handle_alert(),

    "general_chat":       lambda q, s, e: handle_general_chat(q),
}


def get_answer(query: str) -> str:
    session = get_session()

    # ── Handle pending follow-up (e.g. waiting for branch after fee query) ──
    if session["pending_question"] == "branch":
        branch = _extract_branch(query)
        if branch:
            update_session(branch=branch, pending=None)
            return handle_fees(query, "branch_fee", branch)
        # User didn't say a branch — ask again
        return "Sorry, which branch? Computer, IT, Mechanical, Civil, Electrical, or ENTC?"

    intent, sub_intent, confidence, entity = detect_intent(query)
    print(f"[Intent]: {intent} | sub={sub_intent} | entity={entity} | conf={confidence}")

    # ── Session memory: persist branch across turns ────────────────
    if entity:
        update_session(branch=entity)
    elif session["branch"] and intent in ("fees", "placements"):
        entity = session["branch"]   # reuse remembered branch

    # ── Ask for branch if fees query has no branch ─────────────────
    if intent == "fees" and not entity and sub_intent not in ("hostel_fee", "exam_fee"):
        update_session(intent=intent, sub_intent=sub_intent, pending="branch")
        return "Which branch would you like the fee for?"

    update_session(intent=intent, sub_intent=sub_intent, pending=None)

    handler = _ROUTER.get(intent, lambda q, s, e: handle_general_chat(q))
    return handler(query, sub_intent, entity)
