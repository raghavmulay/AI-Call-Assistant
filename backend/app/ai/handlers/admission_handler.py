import json
import os

_ADMISSION = os.path.join(os.path.dirname(__file__), "..", "knowledge", "admission", "dates.json")
_OFFICE    = os.path.join(os.path.dirname(__file__), "..", "knowledge", "office", "office.json")


def _adm():
    with open(_ADMISSION, encoding="utf-8") as f:
        return json.load(f)


def _off():
    with open(_OFFICE, encoding="utf-8") as f:
        return json.load(f)


def handle_cutoff(_=None) -> str:
    d = _adm()["cutoff"]
    return f"General: {d['general']}. OBC: {d['obc']}. SC/ST: {d['sc_st']}."


def handle_eligibility(_=None) -> str:
    e = _adm()["eligibility"]
    return f"{e['qualification']}, {e['percentage']}. {e['entrance_exam']}."


def handle_admission_dates(query: str = "", sub_intent: str = None) -> str:
    s = _adm()["schedule"]
    if sub_intent == "last_date":
        return f"Last date: {s['application_end']}. Fee deadline: {s['fee_payment_deadline']}."
    if sub_intent == "merit_list":
        return f"Merit list 1: {s['merit_list_1']}. Merit list 2: {s['merit_list_2']}."
    if sub_intent == "class_start":
        return f"Classes begin {s['classes_begin']}."
    return f"Applications: {s['application_start']} to {s['application_end']}. Merit list: {s['merit_list_1']}. Classes: {s['classes_begin']}."


def handle_admission_process(_=None) -> str:
    p = _adm()["process"]
    steps = ". ".join(p["steps"])
    return f"Steps: {steps}. Portal: {p['portal']}."


def handle_branches(_=None) -> str:
    b = _adm()["branches"]
    return f"Branches: {', '.join(b['available'])}. Total intake: {b['total_intake']}."


def handle_placements(query: str = "", sub_intent: str = None, entity: str = None) -> str:
    from backend.app.ai.knowledge.placements import placements as _pl
    p = _pl.load()
    if entity and entity in p.get("by_branch", {}):
        return f"{entity.title()}: {p['by_branch'][entity]}."
    recruiters = ", ".join(p["top_recruiters"][:4])
    return f"Average {p['average_package']}, highest {p['highest_package']}. Recruiters: {recruiters}."


def handle_scholarship(_=None) -> str:
    from backend.app.ai.knowledge.placements import placements as _pl
    s = _pl.load()["scholarship"]
    return f"{s['government']}. Merit scholarship for CGPA above 9.0."


def handle_hostel(query: str = "", sub_intent: str = None) -> str:
    from backend.app.ai.knowledge.hostel import hostel as _hs
    h = _hs.load()
    if sub_intent == "facilities":
        return f"Facilities: {h['facilities']}. Mess: {h['mess_timings']}."
    return f"Boys: {h['boys_hostel']}, Girls: {h['girls_hostel']}. Fee: {h['fee']}."


def handle_contact(query: str = "", sub_intent: str = None) -> str:
    o = _off()
    if sub_intent == "email":
        return f"Email: {o['email']['admissions']}."
    if sub_intent == "website":
        return f"Website: {o['website']}."
    c = o["contacts"]
    return f"Phone: {c['admission_office']}. Email: {o['email']['admissions']}. Hours: {o['timings']['general']}."


def handle_office_timing(query: str = "", sub_intent: str = None) -> str:
    t = _off()["timings"]
    if sub_intent == "exam_cell":
        return f"Exam cell: {t['exam_cell']}."
    if sub_intent == "library":
        return f"Library: {t['library']}."
    if sub_intent == "accounts":
        return f"Accounts office: {t['accounts']}."
    if sub_intent == "placement":
        return f"Placement cell: {t['placement_cell']}."
    return f"Office hours: {t['general']}."


def handle_office_location(query: str = "", sub_intent: str = None) -> str:
    loc = _off()["locations"]
    if sub_intent == "admission":
        return f"Admission office: {loc['admission_office']}."
    if sub_intent == "exam_cell":
        return f"Exam cell: {loc['exam_cell']}."
    if sub_intent == "library":
        return f"Library: {loc['library']}."
    if sub_intent == "hostel":
        return f"Hostel office: {loc['hostel_office']}."
    if sub_intent == "placement":
        return f"Placement cell: {loc['placement_cell']}."
    if sub_intent == "principal":
        return f"Principal's office: {loc['principal_office']}."
    # fallback — try to detect from query
    q = query.lower()
    for key in ("admission", "exam", "library", "hostel", "placement", "principal", "accounts"):
        if key in q:
            mapped = {
                "admission": "admission_office", "exam": "exam_cell",
                "library": "library", "hostel": "hostel_office",
                "placement": "placement_cell", "principal": "principal_office",
                "accounts": "accounts"
            }
            return f"{key.title()}: {loc[mapped[key]]}."
    return f"Admission office: {loc['admission_office']}."
