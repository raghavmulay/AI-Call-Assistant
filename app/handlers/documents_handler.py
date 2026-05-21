import json
import os

_KB = os.path.join(os.path.dirname(__file__), "..", "knowledge", "admission", "dates.json")


def _load():
    with open(_KB, encoding="utf-8") as f:
        return json.load(f)["documents"]


def handle_documents(query: str = "", sub_intent: str = None) -> str:
    data = _load()
    sub = data["submission"]

    if sub_intent == "submission_location":
        return f"Submit at: {sub['office']}."

    if sub_intent == "submission_timing":
        return f"Submission timings: {sub['timing']}."

    if sub_intent == "required_docs":
        docs = ", ".join(data["required"][:5])
        return f"Required: {docs}, and more."

    docs = ", ".join(data["required"][:4])
    return f"Bring: {docs}, and more. Submit at {sub['office']}, {sub['timing']}."
