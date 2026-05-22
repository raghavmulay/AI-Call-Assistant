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
                return f"The tuition fee for {entity.title()} is {fee}. This is fixed for all four years of the course."
        if sub_intent == "hostel_fee":
            hf = data.get("hostel_fee", {})
            fee = hf.get("per_year", "") if isinstance(hf, dict) else str(hf)
            return f"The hostel fee is approximately {fee}. This includes both accommodation and mess facilities — three meals a day."
        if sub_intent == "exam_fee":
            ef = data.get("other_fees", {}).get("exam_fee", "Rs. 2,000 per semester")
            return f"The examination fee is {ef}."
        if sub_intent == "total_cost":
            total = data.get("total_annual_cost", {})
            day = total.get("day_scholar", "approximately Rs. 1,30,000 per year")
            hosteller = total.get("hosteller", "approximately Rs. 1,95,000 per year")
            return f"As a day scholar, the total annual cost is {day}. If you stay in the hostel, it comes to {hosteller} including accommodation and meals."
        if sub_intent == "installment":
            inst = data.get("installment_options", {})
            return f"Yes, fees can be paid in installments. {inst.get('details', 'Two installments per year are allowed.')}"
        if sub_intent == "refund":
            refund = data.get("refund_policy", {})
            return f"Regarding the refund policy — {refund.get('before_cutoff', 'full refund before cutoff')}. {refund.get('after_cutoff', 'Partial refund after cutoff as per DTE norms.')}"
        # General fees
        by_branch = data.get("by_branch", {})
        lines = ", ".join(f"{b.title()}: {f}" for b, f in list(by_branch.items())[:3])
        hostel = data.get("hostel_fee", {})
        hostel_fee = hostel.get("per_year", "Rs. 60,000") if isinstance(hostel, dict) else str(hostel)
        hidden = data.get("hidden_charges", "There are no hidden charges.")
        return f"The tuition fees vary by branch — {lines}, and more. The hostel fee is {hostel_fee} including mess. {hidden}"

    # ── Hostel ────────────────────────────────────────────────────────────────
    def _fmt_hostel(self, data, sub_intent, entity):
        if sub_intent == "facilities":
            facilities = data.get("facilities", [])
            if isinstance(facilities, list):
                fac_str = ", ".join(facilities[:6])
            else:
                fac_str = str(facilities)
            return f"The hostel is well-equipped with {fac_str}, and more."
        if sub_intent == "boys":
            boys = data.get("boys_hostel", {})
            if isinstance(boys, dict):
                return f"Yes, we have a boys hostel with a capacity of {boys.get('capacity', 300)} students. {boys.get('rooms', 'Single, double, and triple sharing rooms are available.')} Contact: {boys.get('contact', '020-99988877')}."
            return f"Boys hostel: {boys}"
        if sub_intent == "girls":
            girls = data.get("girls_hostel", {})
            if isinstance(girls, dict):
                return f"Yes, we have a girls hostel with a capacity of {girls.get('capacity', 200)} students. {girls.get('note', 'It has dedicated female security staff.')} Contact: {girls.get('contact', '020-99988866')}."
            return f"Girls hostel: {girls}"
        if sub_intent == "mess":
            mess = data.get("mess", {})
            if isinstance(mess, dict):
                timings = mess.get("timings", {})
                return (f"The mess serves three meals a day. Breakfast: {timings.get('breakfast', '7-9 AM')}, "
                        f"Lunch: {timings.get('lunch', '12-2 PM')}, Dinner: {timings.get('dinner', '7-9 PM')}. "
                        f"{mess.get('type', 'Both vegetarian and non-vegetarian options are available.')}")
        fee = data.get("fee", "Rs. 60,000 per year including mess")
        boys = data.get("boys_hostel", {})
        girls = data.get("girls_hostel", {})
        boys_cap = boys.get("capacity", 300) if isinstance(boys, dict) else "available"
        girls_cap = girls.get("capacity", 200) if isinstance(girls, dict) else "available"
        facilities = data.get("facilities", [])
        fac_str = ", ".join(facilities[:4]) if isinstance(facilities, list) else str(facilities)
        return (f"The hostel fee is {fee}. We have a boys hostel with capacity for {boys_cap} students "
                f"and a girls hostel for {girls_cap} students. Facilities include {fac_str}, and more.")

    # ── Documents ─────────────────────────────────────────────────────────────
    def _fmt_documents(self, data, sub_intent, entity):
        if sub_intent == "submission_location":
            office = data.get("document_submission", {}).get("office", "Student Section, Ground Floor, Admin Block")
            return f"Documents should be submitted at the {office}."
        if sub_intent == "submission_timing":
            timing = data.get("document_submission", {}).get("timing", "9 AM to 4 PM on working days")
            return f"Document submission timing is {timing}."
        if sub_intent == "gap_certificate":
            gap = data.get("gap_certificate", {})
            return f"A gap certificate is required if there is a gap year after 12th. {gap.get('format', 'It is an affidavit on Rs. 100 stamp paper stating the reason for the gap.')} It needs to be notarized."
        if sub_intent == "originals":
            return f"Yes, original documents are required for verification. {data.get('notes', 'You also need to bring 2 self-attested photocopies of each document. Originals will be returned after verification.')}"
        required = data.get("required_documents", [])
        top = ", ".join(required[:5]) if required else "10th and 12th marksheets, TC, Aadhar Card, photographs"
        submission = data.get("document_submission", {})
        office = submission.get("office", "Student Section, Ground Floor")
        timing = submission.get("timing", "9 AM to 4 PM on working days")
        return (f"The key documents required are: {top}, and a few more. "
                f"Please bring originals along with 2 self-attested photocopies. "
                f"Submit them at {office} between {timing}.")

    # ── Admission dates ───────────────────────────────────────────────────────
    def _fmt_admission_dates(self, data, sub_intent, entity):
        s = data if isinstance(data, dict) else {}
        if sub_intent == "last_date":
            return f"The application deadline is {s.get('application_end', 'June 30th, 2025')}. Make sure to apply before this date."
        if sub_intent == "merit_list":
            return f"The first merit list will be released on {s.get('merit_list_1', 'July 10th, 2025')}, and the second merit list on {s.get('merit_list_2', 'July 20th, 2025')}."
        if sub_intent == "class_start":
            return f"Classes are scheduled to begin on {s.get('classes_begin', 'August 1st, 2025')}. There will be an orientation program for new students before classes start."
        if sub_intent == "spot_round":
            return f"A spot round is conducted in {s.get('spot_round', 'late July 2025')} if seats remain vacant after the CAP rounds. It's a great opportunity if you missed the earlier rounds."
        return (f"Admissions for 2025 are open from {s.get('application_start', 'June 1st')} "
                f"to {s.get('application_end', 'June 30th')}. "
                f"Document verification is from {s.get('document_verification', 'July 11th to 15th')}. "
                f"Classes begin on {s.get('classes_begin', 'August 1st, 2025')}.")

    # ── Branches ──────────────────────────────────────────────────────────────
    def _fmt_branches(self, data, sub_intent, entity):
        branches = data.get("available", [])
        intake = data.get("intake_by_branch", {})
        if isinstance(branches, list) and branches:
            branch_list = ", ".join(branches)
            total = data.get("total_intake", "720 seats")
            return (f"The college offers {len(branches)} engineering branches: {branch_list}. "
                    f"Total intake is {total}. Computer Engineering and IT are the most popular branches.")
        return "The college offers Computer Engineering, IT, Electronics and Telecommunication, Mechanical, Civil, and Electrical Engineering."

    # ── Placements ────────────────────────────────────────────────────────────
    def _fmt_placements(self, data, sub_intent, entity):
        if entity and "by_branch" in data:
            info = data["by_branch"].get(entity.lower())
            if isinstance(info, dict):
                return (f"For {entity.title()}, the average package is {info.get('average', 'Rs. 4.5 LPA')} "
                        f"and the highest package is {info.get('highest', '')}. "
                        f"Placement rate is {info.get('placement_rate', '')}. "
                        f"Top recruiters include {', '.join(info.get('top_companies', [])[:4])}.")
            elif info:
                return f"Placements for {entity.title()}: {info}."
        if sub_intent == "internship":
            intern = data.get("internships", {})
            return (f"Yes, internship opportunities are available. {intern.get('details', 'Internships are encouraged in 6th and 7th semester.')} "
                    f"Stipend ranges from {intern.get('stipend_range', 'Rs. 5,000 to Rs. 25,000 per month')}.")
        if sub_intent == "training":
            training = data.get("placement_training", {})
            details = training.get("details", "Aptitude, coding, communication skills, and mock interviews are covered.')}")
            return f"The college provides year-round placement training covering aptitude, coding, communication skills, and mock interviews. {training.get('coding_platforms', '')}"
        if sub_intent == "higher_studies":
            hs = data.get("higher_studies", {})
            pct = hs.get("percentage_pursuing", "approximately 15%")
            return (f"About {pct} of students pursue higher studies after graduation. "
                    f"GATE coaching is available on campus. GRE/GMAT and MBA preparation guidance is also provided.")
        overview = data.get("overview", {})
        avg = overview.get("average_package", "Rs. 4.5 LPA")
        highest = overview.get("highest_package", "Rs. 18 LPA")
        rate = overview.get("placement_rate", "85% of eligible students placed")
        # Strip trailing "placed" if already in rate string to avoid duplication
        rate_clean = rate.rstrip(".").rstrip()
        if not rate_clean.endswith("placed"):
            rate_clean += " placed"
        companies = overview.get("companies_visited", "120+ companies")
        return (f"Our placement record is strong — {rate_clean}. "
                f"The average package is {avg} and the highest package offered is {highest}. "
                f"{companies} visit our campus annually.")

    # ── Cutoff ────────────────────────────────────────────────────────────────
    def _fmt_cutoff(self, data, sub_intent, entity):
        cutoff = data.get("cutoff", data)
        if entity and "by_branch" in cutoff:
            branch_cutoff = cutoff["by_branch"].get(entity.lower())
            if branch_cutoff:
                return f"The cutoff for {entity.title()} is approximately {branch_cutoff}. These vary each year based on demand."
        general = cutoff.get("general", "above 75% in PCM")
        obc = cutoff.get("obc", "above 65%")
        sc_st = cutoff.get("sc_st", "above 50%")
        note = cutoff.get("note", "")
        return f"The cutoff for General category is {general}, OBC is {obc}, and SC/ST is {sc_st}. {note}"

    # ── Eligibility ───────────────────────────────────────────────────────────
    def _fmt_eligibility(self, data, sub_intent, entity):
        e = data.get("eligibility", data)
        qual = e.get("qualification", "12th pass with Physics, Chemistry, Mathematics")
        pct = e.get("percentage", "50% aggregate (45% for reserved categories)")
        exam = e.get("entrance_exam", "MHT-CET or JEE Main score required")
        lateral = e.get("lateral_entry", "Diploma holders can apply for direct second year admission.")
        return (f"To be eligible, you need to have passed 12th with PCM — {qual}. "
                f"Minimum {pct}. {exam}. {lateral}")

    # ── Admission process ─────────────────────────────────────────────────────
    def _fmt_admission_process(self, data, sub_intent, entity):
        steps = data.get("steps", []) if isinstance(data, dict) else []
        portal = data.get("portal", "cetcell.mahacet.org") if isinstance(data, dict) else ""
        if steps:
            step_str = "; ".join(steps[:4])
            return f"The admission process involves: {step_str}. The official portal is {portal}."
        return "Appear for MHT-CET, register on the CAP portal at cetcell.mahacet.org, fill the preference form, attend document verification, and pay fees after allotment."

    # ── Scholarship ───────────────────────────────────────────────────────────
    def _fmt_scholarship(self, data, sub_intent, entity):
        s = data.get("scholarship", data)
        govt = s.get("government", "Government scholarships like EBC, OBC, SC/ST are available via MahaDBT portal.")
        inst = s.get("institute", "Merit scholarship for students with CGPA above 9.0.")
        contact = s.get("contact", "scholarship@college.edu")
        deadline = s.get("deadline", "Applications typically open in September.")
        return f"{govt} {inst} {deadline} For more details, contact {contact}."

    # ── Office timing ─────────────────────────────────────────────────────────
    def _fmt_office_timing(self, data, sub_intent, entity):
        timings = data.get("timings", data)
        if sub_intent and sub_intent in timings:
            return f"The {sub_intent.replace('_', ' ')} is open {timings[sub_intent]}."
        general = timings.get("general", "9 AM to 5 PM, Monday to Saturday")
        lib = timings.get("library", "8 AM to 8 PM")
        return f"General office hours are {general}. The library is open {lib}."

    # ── Office location ───────────────────────────────────────────────────────
    def _fmt_office_location(self, data, sub_intent, entity):
        locations = data.get("locations", data)
        if sub_intent:
            key = sub_intent if sub_intent in locations else f"{sub_intent}_office"
            loc = locations.get(key) or locations.get(sub_intent)
            if loc:
                return f"The {sub_intent.replace('_', ' ')} is located at {loc}."
        admission = locations.get("admission_office", "Ground Floor, Admin Block, near Main Gate")
        return f"The admission office is at {admission}. The principal's office is on the First Floor of the Admin Block."

    # ── Contact ───────────────────────────────────────────────────────────────
    def _fmt_contact(self, data, sub_intent, entity):
        contacts = data.get("contacts", {})
        emails = data.get("email", {})
        website = data.get("website", "www.college.edu")
        if sub_intent == "email":
            return f"You can reach us at {emails.get('general', 'info@college.edu')} for general queries, or {emails.get('admissions', 'admissions@college.edu')} for admission-related queries."
        if sub_intent == "website":
            return f"The official college website is {website}. You can find all information including admission forms and notices there."
        if sub_intent == "helpline":
            return f"The anti-ragging helpline is 1800-180-5522. For general helpline, call {contacts.get('helpline', contacts.get('admission_office', '020-12345678'))}."
        helpline = contacts.get("helpline", contacts.get("admission_office", "020-12345678"))
        return f"You can reach the college at {helpline}. Email: {emails.get('general', 'info@college.edu')}. Website: {website}."

    # ── Campus Life ───────────────────────────────────────────────────────────
    def _fmt_campus_life(self, data, sub_intent, entity):
        if sub_intent == "clubs":
            tech = data.get("clubs", {}).get("technical", [])
            cultural = data.get("clubs", {}).get("cultural", [])
            tech_str = ", ".join([c.split(" —")[0] for c in tech[:4]])
            cultural_str = ", ".join([c.split(" —")[0] for c in cultural[:3]])
            return (f"The college has a vibrant club culture. Technical clubs include {tech_str}. "
                    f"Cultural clubs include {cultural_str}. There's also NSS, NCC, and an active E-Cell for entrepreneurs.")
        if sub_intent == "events":
            events = data.get("events", {})
            tech_fest = events.get("technical_fest", {})
            cultural_fest = events.get("cultural_fest", {})
            return (f"The college hosts {tech_fest.get('name', 'TechVIT')}, our annual technical festival with hackathons and coding competitions. "
                    f"{cultural_fest.get('name', 'Viva')} is our cultural fest with music, dance, and celebrity performances. "
                    f"Multiple hackathons are also organized throughout the year.")
        if sub_intent == "sports":
            sports = data.get("sports", {})
            outdoor = ", ".join(sports.get("outdoor", [])[:4])
            return (f"The campus has excellent sports facilities including {outdoor}. "
                    f"There's also a fully equipped gymnasium open from 6 AM to 9 PM. "
                    f"College teams participate in inter-university tournaments regularly.")
        if sub_intent == "cafeteria":
            cafe = data.get("infrastructure", {}).get("cafeteria", {})
            return (f"The college cafeteria is open {cafe.get('timing', '8 AM to 8 PM')} with multiple food stalls. "
                    f"{cafe.get('options', 'North Indian, South Indian, Chinese, and fast food options are available.')} "
                    f"{cafe.get('price_range', 'Meals start from Rs. 40 — very affordable.')}")
        if sub_intent == "library":
            lib = data.get("infrastructure", {}).get("library", {})
            # books field may already say "50,000+ books and reference materials" — extract just the count
            books_raw = lib.get("books", "50,000+")
            books = books_raw.split(" books")[0] if " books" in books_raw else books_raw
            digital = lib.get("digital", "IEEE Xplore, Springer, and NPTEL digital libraries")
            timing = lib.get("timing", "8 AM to 8 PM, Monday to Saturday")
            return (f"The library has {books} books and reference materials. "
                    f"Students also have access to {digital}. "
                    f"Library timing: {timing}.")
        if sub_intent == "transport":
            transport = data.get("transportation", {})
            routes = transport.get("college_bus", "Swargate, Katraj, Hadapsar, Kothrud, Wakad, and Hinjewadi")
            return (f"College bus service is available from major areas in Pune including {routes}. "
                    f"Semester bus passes are available at subsidized rates.")
        if sub_intent == "coding_culture":
            coding = data.get("coding_culture", {})
            return (f"{coding.get('description', 'VIT Pune has a strong coding culture.')} "
                    f"{coding.get('achievements', 'Students have cleared Google, Microsoft, and Amazon interviews.')} "
                    f"{coding.get('open_source', 'Active open source contribution culture.')}")
        if sub_intent == "internet":
            internet = data.get("internet", "campus-wide Wi-Fi with 1 Gbps internet connectivity")
            return f"The campus has {internet.lower()}. Hostel rooms also have high-speed Wi-Fi."
        # General campus life
        coding = data.get("coding_culture", {}).get("description", "")
        events = data.get("events", {})
        fest = events.get("technical_fest", {}).get("name", "TechVIT")
        return (f"Campus life at VIT Pune is vibrant and well-rounded. There are active technical and cultural clubs, "
                f"annual fests like {fest}, hackathons, sports facilities, a gym, cafeteria, and a well-stocked library. "
                f"{coding} It's a great environment to grow both technically and personally.")

    # ── Counseling ────────────────────────────────────────────────────────────
    def _fmt_counseling(self, data, sub_intent, entity):
        guidance_map = {
            "best_branch":           ("branch_guidance", "best_branch_overall"),
            "cs_vs_it":              ("branch_guidance", "cs_vs_it"),
            "ai_vs_it":              ("branch_guidance", "ai_vs_it"),
            "best_placements":       ("branch_guidance", "best_for_placements"),
            "is_coding_hard":        ("college_life_guidance", "is_coding_difficult"),
            "college_life":          ("college_life_guidance", "how_is_college_life"),
            "is_hostel_safe":        ("college_life_guidance", "is_hostel_safe"),
            "attendance_strict":     ("college_life_guidance", "is_attendance_strict"),
            "low_marks":             ("admission_guidance", "low_marks"),
            "should_join":           ("admission_guidance", "should_choose_college"),
            "mechanical_future":     ("branch_guidance", "mechanical_future"),
            "civil_future":          ("branch_guidance", "civil_future"),
            "entc_future":           ("branch_guidance", "entc_future"),
            "hostel_vs_day":         ("college_life_guidance", "hostel_vs_day_scholar"),
            "first_year_tips":       ("college_life_guidance", "first_year_tips"),
            "software_career":       ("career_guidance", "software_career"),
            "lateral_entry_guidance":("admission_guidance", "lateral_entry"),
            "management_quota_guidance": ("admission_guidance", "management_quota"),
        }
        if sub_intent and sub_intent in guidance_map:
            section, key = guidance_map[sub_intent]
            response = data.get(section, {}).get(key, "")
            if response:
                return response
        # Fallback — return best_branch_overall
        return data.get("branch_guidance", {}).get("best_branch_overall",
               "I'd be happy to guide you. Could you tell me more about your interests so I can suggest the best branch for you?")

    # ── Academics ─────────────────────────────────────────────────────────────
    def _fmt_academics(self, data, sub_intent, entity):
        if sub_intent == "grading":
            return ("The college follows a credit-based grading system under Savitribai Phule Pune University. "
                    "CGPA is calculated on a 10-point scale. You need a minimum CGPA of 5.0 to pass each semester. "
                    "A CGPA above 9.0 qualifies you for the merit scholarship.")
        if sub_intent == "attendance":
            return ("A minimum of 75% attendance is required in each subject to be eligible for university exams. "
                    "Medical emergencies are considered with proper documentation. "
                    "It's important to be regular — attendance directly impacts your exam eligibility.")
        if sub_intent == "exams":
            return ("The academic year has two semesters. Each semester has internal assessments (unit tests, assignments) "
                    "and a final university examination. Internal marks are 40% and external exam is 60% of total marks.")
        if sub_intent == "projects":
            return ("Final year students work on a major project in groups of 3-4 students under faculty guidance. "
                    "Mini projects are also done in 3rd year. Projects can be in any domain — AI, web, IoT, robotics, etc. "
                    "Good projects significantly improve your placement prospects.")
        if sub_intent == "internship":
            return ("Internships are strongly encouraged in the 6th and 7th semester. "
                    "The placement cell helps connect students with internship opportunities. "
                    "Many companies that offer internships also give pre-placement offers (PPOs).")
        return ("Academics at VIT Pune follow the Savitribai Phule Pune University curriculum. "
                "The grading is on a 10-point CGPA scale. Minimum 75% attendance is required. "
                "The college has well-equipped labs and experienced faculty.")

    # ── DB intents (attendance, timetable) ────────────────────────────────────
    def serialize_attendance(self, data: Any) -> str:
        if not data or not hasattr(data, 'records'):
            return "No attendance records found."
        lines = ["Here's your attendance summary:"]
        for r in data.records:
            lines.append(f"{r.subject_name}: {r.attendance_percent}%")
        lines.append(f"Overall average: {data.overall_average}%")
        return " ".join(lines)

    def serialize_timetable(self, data: Any) -> str:
        if not data:
            return "No timetable available."
        lines = []
        for slot in data:
            lines.append(f"{slot.day} {slot.time}: {slot.subject_name}")
        return "Your schedule: " + ", ".join(lines)

    def serialize_generic(self, data: Any, header: str = "") -> str:
        if isinstance(data, dict):
            parts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in list(data.items())[:5]]
            return ". ".join(parts)
        return str(data)


serializer = PromptSerializer()
