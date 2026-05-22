import json
import os

_KB = os.path.join(os.path.dirname(__file__), "..", "knowledge", "admission", "dates.json")


def _load():
    with open(_KB, encoding="utf-8") as f:
        return json.load(f)["fees"]


def handle_fees(query: str = "", sub_intent: str = None, entity: str = None) -> str:
    data = _load()

    if sub_intent == "hostel_fee":
        # Pull from hostel knowledge to avoid hardcoded duplication
        try:
            from backend.app.ai.knowledge.hostel import hostel as _hs
            h = _hs.load()
            fb = h.get("fee_breakdown", {})
            return (
                f"Hostel fee is {h.get('fee', 'Rs. 60,000 per year')}. "
                f"Breakdown: accommodation {fb.get('accommodation', 'Rs. 40,000')}, "
                f"mess {fb.get('mess', 'Rs. 20,000')} per year."
            )
        except Exception:
            return "Hostel fee: Rs. 60,000 per year (accommodation + mess)."

    if sub_intent == "exam_fee":
        return f"Exam fee: {data['exam_fee']}."

    if entity and entity in data["by_branch"]:
        return f"{entity.title()} fee: {data['by_branch'][entity]}."

    words = set(query.lower().split())
    if "scholarship" in query.lower() or "sc/st" in query.lower() or {"sc", "st", "obc"} & words:
        return data["scholarship_note"]

    modes = ", ".join(data["payment_modes"])
    return f"Tuition fee: {data['tuition_per_year']} per year. Payment via: {modes}."
