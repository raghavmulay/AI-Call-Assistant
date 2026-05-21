"""
Lightweight in-memory session for conversational context.
Resets on restart. Replace with DB-backed session later.
"""

session = {
    "last_intent": None,
    "last_sub_intent": None,
    "branch": None,
    "prn": None,
    "pending_question": None,   # what the assistant is waiting for
}


def update(intent=None, sub_intent=None, branch=None, prn=None, pending=None):
    if intent is not None:
        session["last_intent"] = intent
    if sub_intent is not None:
        session["last_sub_intent"] = sub_intent
    if branch is not None:
        session["branch"] = branch
    if prn is not None:
        session["prn"] = prn
    session["pending_question"] = pending


def get():
    return session


def clear_pending():
    session["pending_question"] = None
