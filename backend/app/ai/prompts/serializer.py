"""
serializer.py — Direct natural language response generator.
Bypasses LLM for structured intents — sub-100ms responses.
"""
from typing import Any, Optional


class PromptSerializer:

    def serialize(self, intent: str, data: Any, sub_intent: str = None, entity: str = None) -> str:
        if not data:
            return ""
        try:
            fn = getattr(self, f"_fmt_{intent}", None)
            if fn:
                return fn(data, sub_intent, entity)
        except Exception:
            pass
        return self.serialize_generic(data)

    # ── Fees ──────────────────────────────────────────────────────────────────
    def _fmt_fees(self, data, sub_intent, entity):
        if entity and "by_branch" in data:
            fee = data["by_branch"].get(entity.lower())
            if fee:
                return f"The tuition fee for {entity.title()} is {fee}."
        if sub_intent == "hostel_fee":
            hf = data.get("hostel_fee", {}).get("per_year", "")
            return f"The hostel fee is {hf}." if hf else ""
        if sub_intent == "exam_fee":
            ef = data.get("other_fees", {}).get("exam_fee", "")
            return f"The exam fee is {ef}." if ef else ""
        # General fees
        by_branch = data.get("by_branch", {})
        lines = ", ".join(f"{b.title()}: {f}" for b, f in list(by_branch.items())[:3])
        hostel = data.get("hostel_fee", {}).get("per_year", "")
        return f"Tuition fees vary by branch — {lines}, and more. Hostel fee is {hostel}."

    # ── Hostel ────────────────────────────────────────────────────────────────
    def _fmt_hostel(self, data, sub_intent, entity):
        fee = data.get("fee", "")
        boys = data.get("boys_hostel", "")
        girls = data.get("girls_hostel", "")
        facilities = data.get("facilities", "")
        return f"The hostel fee is {fee}. Boys hostel: {boys}, Girls hostel: {girls}. Facilities include {facilities}."

    # ── Documents ─────────────────────────────────────────────────────────────
    def _fmt_documents(self, data, sub_intent, entity):
        docs = data.get("documents", data)
        required = docs.get("required", [])
        submission = docs.get("submission", {})
        if sub_intent == "submission_location":
            return f"Documents should be submitted at {submission.get('office', 'the admission office')}."
        if sub_intent == "submission_timing":
            return f"Document submission timing is {submission.get('timing', '9 AM to 4 PM on working days')}."
        top = ", ".join(required[:4]) if required else "marksheets, TC, Aadhar"
        office = submission.get("office", "Student Section")
        timing = submission.get("timing", "9 AM to 4 PM")
        return f"Required documents include {top}, and more. Submit at {office} between {timing}."

    # ── Admission dates ───────────────────────────────────────────────────────
    def _fmt_admission_dates(self, data, sub_intent, entity):
        s = data if isinstance(data, dict) else {}
        if sub_intent == "last_date":
            return f"The application deadline is {s.get('application_end', 'June 30th 2025')}."
        if sub_intent == "merit_list":
            return f"The first merit list will be released on {s.get('merit_list_1', 'July 10th 2025')}."
        if sub_intent == "class_start":
            return f"Classes begin on {s.get('classes_begin', 'August 1st 2025')}."
        return (f"Applications open from {s.get('application_start', 'June 1st')} "
                f"to {s.get('application_end', 'June 30th')}. "
                f"Classes begin {s.get('classes_begin', 'August 1st 2025')}.")

    # ── Branches ──────────────────────────────────────────────────────────────
    def _fmt_branches(self, data, sub_intent, entity):
        branches = data.get("available", data.get("branches", {}).get("available", []))
        if isinstance(branches, list) and branches:
            return f"The college offers {len(branches)} branches: {', '.join(branches)}."
        return "The college offers Computer, IT, ENTC, Mechanical, Civil, and Electrical Engineering."

    # ── Placements ────────────────────────────────────────────────────────────
    def _fmt_placements(self, data, sub_intent, entity):
        if entity and "by_branch" in data:
            info = data["by_branch"].get(entity.lower())
            if info:
                return f"Placements for {entity.title()}: {info}."
        avg = data.get("average_package", "")
        highest = data.get("highest_package", "")
        rate = data.get("placement_rate", "")
        return f"Overall placement rate is {rate}. Average package: {avg}, highest: {highest}."

    # ── Cutoff ────────────────────────────────────────────────────────────────
    def _fmt_cutoff(self, data, sub_intent, entity):
        cutoff = data.get("cutoff", data)
        general = cutoff.get("general", "above 75% in PCM")
        obc = cutoff.get("obc", "above 65%")
        sc_st = cutoff.get("sc_st", "above 50%")
        return f"Cutoff: General category {general}, OBC {obc}, SC/ST {sc_st}."

    # ── Eligibility ───────────────────────────────────────────────────────────
    def _fmt_eligibility(self, data, sub_intent, entity):
        e = data.get("eligibility", data)
        qual = e.get("qualification", "12th pass with PCM")
        pct = e.get("percentage", "50% aggregate")
        exam = e.get("entrance_exam", "MHT-CET or JEE Main")
        return f"Eligibility: {qual}, minimum {pct}. {exam} score required."

    # ── Admission process ─────────────────────────────────────────────────────
    def _fmt_admission_process(self, data, sub_intent, entity):
        steps = data.get("steps", []) if isinstance(data, dict) else []
        portal = data.get("portal", "cetcell.mahacet.org") if isinstance(data, dict) else ""
        if steps:
            return f"Admission process: {'; '.join(steps[:3])}. Apply via {portal}."
        return "Register on MHT-CET portal, fill CAP form, upload documents, attend verification, then pay fees."

    # ── Scholarship ───────────────────────────────────────────────────────────
    def _fmt_scholarship(self, data, sub_intent, entity):
        s = data.get("scholarship", data)
        govt = s.get("government", "")
        inst = s.get("institute", "")
        contact = s.get("contact", "scholarship@college.edu")
        return f"{govt}. {inst}. Contact {contact} for details."

    # ── Office timing ─────────────────────────────────────────────────────────
    def _fmt_office_timing(self, data, sub_intent, entity):
        timings = data.get("timings", data)
        if sub_intent and sub_intent in timings:
            return f"The {sub_intent.replace('_', ' ')} is open {timings[sub_intent]}."
        general = timings.get("general", "9 AM to 5 PM, Monday to Saturday")
        return f"General office hours are {general}."

    # ── Office location ───────────────────────────────────────────────────────
    def _fmt_office_location(self, data, sub_intent, entity):
        locations = data.get("locations", data)
        if sub_intent:
            key = sub_intent if sub_intent in locations else f"{sub_intent}_office"
            loc = locations.get(key) or locations.get(sub_intent)
            if loc:
                return f"The {sub_intent.replace('_', ' ')} is located at {loc}."
        return f"The admission office is at {locations.get('admission_office', 'Ground Floor, Admin Block')}."

    # ── Contact ───────────────────────────────────────────────────────────────
    def _fmt_contact(self, data, sub_intent, entity):
        contacts = data.get("contacts", {})
        emails = data.get("email", {})
        website = data.get("website", "www.college.edu")
        if sub_intent == "email":
            return f"General email: {emails.get('general', 'info@college.edu')}. Admissions: {emails.get('admissions', '')}."
        if sub_intent == "website":
            return f"The college website is {website}."
        helpline = contacts.get("helpline", contacts.get("admission_office", "020-12345678"))
        return f"Helpline: {helpline}. Email: {emails.get('general', 'info@college.edu')}. Website: {website}."

    # ── DB intents (attendance, timetable) ────────────────────────────────────
    def serialize_attendance(self, data: Any) -> str:
        if not data or not hasattr(data, 'records'):
            return "No attendance records found."
        lines = ["Attendance:"]
        for r in data.records:
            lines.append(f"{r.subject_name}: {r.attendance_percent}%")
        lines.append(f"Overall: {data.overall_average}%")
        return " ".join(lines)

    def serialize_timetable(self, data: Any) -> str:
        if not data:
            return "No timetable available."
        lines = []
        for slot in data:
            lines.append(f"{slot.day} {slot.time}: {slot.subject_name}")
        return "Schedule: " + ", ".join(lines)

    def serialize_generic(self, data: Any, header: str = "Retrieved Data") -> str:
        if isinstance(data, dict):
            parts = [f"{k.replace('_',' ').title()}: {v}" for k, v in list(data.items())[:5]]
            return ". ".join(parts)
        return str(data)


serializer = PromptSerializer()
