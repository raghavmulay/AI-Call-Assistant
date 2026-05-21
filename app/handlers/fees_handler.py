import json
import os

_KB = os.path.join(os.path.dirname(__file__), "..", "knowledge", "admission", "dates.json")


def _load():
    with open(_KB, encoding="utf-8") as f:
        return json.load(f)["fees"]


def handle_fees(query: str = "", sub_intent: str = None, entity: str = None) -> str:
    data = _load()

    if sub_intent == "hostel_fee":
        return f"Hostel fee: Rs. 60,000 per year including mess."

    if sub_intent == "exam_fee":
        return f"Exam fee: {data['exam_fee']}."

    if entity and entity in data["by_branch"]:
        return f"{entity.title()} fee: {data['by_branch'][entity]}."

    words = set(query.lower().split())
    if "scholarship" in query.lower() or "sc/st" in query.lower() or {"sc", "st", "obc"} & words:
        return data["scholarship_note"]

    modes = ", ".join(data["payment_modes"])
    return f"Tuition fee: {data['tuition_per_year']} per year. Payment via: {modes}."
