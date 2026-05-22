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
        # Check if query is specifically about fee payment deadline
        q = query.lower()
        if any(w in q for w in ("fee", "payment", "pay", "tuition")):
            return (
                f"The fee payment deadline is {s['fee_payment_deadline']}. "
                f"Make sure to pay before this date to confirm your admission. "
                f"Application deadline is {s['application_end']}."
            )
        return (
            f"Application deadline: {s['application_end']}. "
            f"Fee payment deadline: {s['fee_payment_deadline']}."
        )
    if sub_intent == "merit_list":
        return f"Merit list 1: {s['merit_list_1']}. Merit list 2: {s['merit_list_2']}."
    if sub_intent == "class_start":
        return f"Classes begin {s['classes_begin']}."
    if sub_intent == "spot_round":
        return f"Spot round: {s['spot_round']}."
    return (
        f"Applications open {s['application_start']} to {s['application_end']}. "
        f"Merit list 1: {s['merit_list_1']}. "
        f"Fee payment deadline: {s['fee_payment_deadline']}. "
        f"Classes begin: {s['classes_begin']}."
    )


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
    ov = p.get("overview", {})

    # ── Branch-specific placement query ───────────────────────────
    if entity and entity in p.get("by_branch", {}):
        b = p["by_branch"][entity]
        companies = ", ".join(b["top_companies"][:5])
        return (
            f"{entity.title()} placements: average {b['average']}, "
            f"highest {b['highest']}, placement rate {b['placement_rate']}. "
            f"Top recruiters: {companies}."
        )

    # ── Branch-wise overview ───────────────────────────────────────
    if sub_intent == "by_branch":
        lines = []
        for branch, b in p.get("by_branch", {}).items():
            lines.append(f"{branch.title()}: avg {b['average']}, highest {b['highest']}, rate {b['placement_rate']}")
        return "Branch-wise placements — " + "; ".join(lines) + "."

    # ── Highest package ───────────────────────────────────────────
    if sub_intent == "highest_package":
        return (
            f"The highest package offered is {ov.get('highest_package', 'Rs. 18 LPA')}. "
            f"Computer Engineering leads with Rs. 18 LPA from top tech companies. "
            f"Overall, {ov.get('placement_rate', '85%')} of eligible students are placed."
        )

    # ── Average package ───────────────────────────────────────────
    if sub_intent == "average_package":
        return (
            f"The average package is {ov.get('average_package', 'Rs. 4.5 LPA')} across all branches. "
            f"Computer Engineering averages Rs. 6 LPA, IT averages Rs. 5.5 LPA. "
            f"{ov.get('companies_visited', '120+ companies')} visit campus every year."
        )

    # ── Recruiters ────────────────────────────────────────────────
    if sub_intent == "recruiters":
        recruiters = ", ".join(p["top_recruiters"][:10])
        return (
            f"Top recruiters include: {recruiters}. "
            f"{ov.get('companies_visited', '120+ companies')} visit campus annually."
        )

    # ── Internships ───────────────────────────────────────────────
    if sub_intent == "internship":
        i = p.get("internships", {})
        return (
            f"Internships are available in the {i.get('semester', '6th and 7th semester')}. "
            f"Stipend ranges from {i.get('stipend_range', 'Rs. 5,000 to Rs. 25,000 per month')}. "
            f"{i.get('note', 'Students with internship experience have higher placement rates')}."
        )

    # ── Training ──────────────────────────────────────────────────
    if sub_intent == "training":
        t = p.get("placement_training", {})
        return (
            f"Placement training: {t.get('details', 'Year-round aptitude, coding, and mock interview sessions')}. "
            f"Platforms: {t.get('coding_platforms', 'HackerRank, LeetCode, CodeChef')}."
        )

    # ── Higher studies ────────────────────────────────────────────
    if sub_intent == "higher_studies":
        h = p.get("higher_studies", {})
        return (
            f"{h.get('gate_coaching', 'GATE coaching available')}. "
            f"{h.get('gre_gmat', 'GRE/GMAT guidance available')}. "
            f"{h.get('percentage_pursuing', 'About 15% students pursue higher studies')}."
        )

    # ── Default overview ──────────────────────────────────────────
    recruiters = ", ".join(p["top_recruiters"][:6])
    return (
        f"Placements at VIT Pune ({ov.get('year', '2024-25')}): "
        f"average package {ov.get('average_package', 'Rs. 4.5 LPA')}, "
        f"highest package {ov.get('highest_package', 'Rs. 18 LPA')}, "
        f"placement rate {ov.get('placement_rate', '85%')}. "
        f"{ov.get('companies_visited', '120+ companies')} visit campus. "
        f"Top recruiters: {recruiters}."
    )


def handle_scholarship(_=None) -> str:
    from backend.app.ai.knowledge.placements import placements as _pl
    s = _pl.load()["scholarship"]
    return f"{s['government']}. Merit scholarship for CGPA above 9.0."


def handle_hostel(query: str = "", sub_intent: str = None) -> str:
    from backend.app.ai.knowledge.hostel import hostel as _hs
    h = _hs.load()
    if sub_intent == "facilities":
        facilities = h.get("facilities", [])
        fac_str = ", ".join(facilities[:6]) if isinstance(facilities, list) else str(facilities)
        mess = h.get("mess", {})
        timings = mess.get("timings", {})
        mess_str = (
            f"Breakfast {timings.get('breakfast', '')}, "
            f"Lunch {timings.get('lunch', '')}, "
            f"Dinner {timings.get('dinner', '')}"
        )
        return f"Hostel facilities: {fac_str}. Mess timings — {mess_str}."
    if sub_intent == "boys":
        b = h.get("boys_hostel", {})
        return (
            f"Boys hostel capacity: {b.get('capacity', 300)} students. "
            f"{b.get('rooms', 'Single, double, and triple sharing rooms')}. "
            f"Warden: {b.get('warden', '')}. Contact: {b.get('contact', '')}."
        )
    if sub_intent == "girls":
        g = h.get("girls_hostel", {})
        return (
            f"Girls hostel capacity: {g.get('capacity', 200)} students. "
            f"{g.get('rooms', 'Single and double sharing rooms')}. "
            f"{g.get('note', '')} Warden: {g.get('warden', '')}. Contact: {g.get('contact', '')}."
        )
    if sub_intent == "mess":
        mess = h.get("mess", {})
        timings = mess.get("timings", {})
        return (
            f"Mess timings — Breakfast: {timings.get('breakfast', '')}, "
            f"Lunch: {timings.get('lunch', '')}, "
            f"Snacks: {timings.get('snacks', '')}, "
            f"Dinner: {timings.get('dinner', '')}. "
            f"{mess.get('type', '')}."
        )
    # Default hostel overview — use fee_breakdown to avoid duplication
    fb = h.get("fee_breakdown", {})
    fee_str = h.get("fee", "Rs. 60,000 per year")
    boys = h.get("boys_hostel", {})
    girls = h.get("girls_hostel", {})
    return (
        f"Hostel is available on campus. "
        f"Boys hostel: {boys.get('capacity', 300)} seats. "
        f"Girls hostel: {girls.get('capacity', 200)} seats. "
        f"Fee: {fee_str} (accommodation Rs. {fb.get('accommodation', 'Rs. 40,000')}, "
        f"mess Rs. {fb.get('mess', 'Rs. 20,000')})."
    )


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
