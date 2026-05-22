"""
Hybrid intent detector — expanded for demo-ready institutional assistant.
"""

from typing import Optional, Tuple, List

# ── Branch name aliases ────────────────────────────────────────────
_BRANCH_ALIASES = {
    "computer":         "computer engineering",
    "cs":               "computer engineering",
    "cse":              "computer engineering",
    "comps":            "computer engineering",
    "it":               "information technology",
    "information tech": "information technology",
    "entc":             "electronics and telecommunication",
    "electronics":      "electronics and telecommunication",
    "e&tc":             "electronics and telecommunication",
    "etc":              "electronics and telecommunication",
    "mechanical":       "mechanical engineering",
    "mech":             "mechanical engineering",
    "civil":            "civil engineering",
    "electrical":       "electrical engineering",
    "ai":               "computer engineering",
    "aiml":             "computer engineering",
}

# ── Strict greeting words ──────────────────────────────────────────
_GREETING_WORDS   = {"hello", "hi", "hey", "howdy", "greetings", "sup", "hiya"}
_GREETING_PHRASES = ["good morning", "good afternoon", "good evening", "good night"]

# ── Intent rules — ORDER MATTERS: specific multi-word phrases before generic ──
# Rule: when two keywords score equally (0.85), the FIRST rule in this list wins.
# So more specific / compound phrases must appear BEFORE generic single-word rules.
_INTENT_RULES = [

    # ── Emergency ─────────────────────────────────────────────────
    ("emergency", None, ["emergency", "fire", "accident", "danger", "sos", "ambulance", "help me", "urgent"]),
    ("alert",     None, ["alert", "unauthorized", "threat", "intruder"]),

    # ── Counseling / Guidance ─────────────────────────────────────
    # MUST be before branches/placements/hostel to catch compound phrases
    ("counseling", "best_branch",      [
        "which branch is best", "best branch", "which branch should i choose",
        "which branch to take", "which course is best", "best course",
        "which department is best", "which branch is better",
        "which branch has better future", "which branch to choose", "which branch is good",
        "which branch should i take", "which branch should i pick",
        "what branch should i take", "what branch should i choose",
        "suggest a branch", "recommend a branch", "help me choose branch",
    ]),
    ("counseling", "cs_vs_it",         [
        "cs vs it", "computer vs it", "cse vs it",
        "difference between cs and it", "cs or it", "computer or it",
        "which is better cs or it",
    ]),
    ("counseling", "ai_vs_it",         [
        "ai vs it", "aiml vs it", "artificial intelligence vs it", "ai or it",
    ]),
    ("counseling", "best_placements",  [
        "which branch has best placement", "best branch for placement",
        "best branch for job", "which branch gets best job",
        "highest paying branch", "which branch has better placement",
        "best placements", "which branch has the best placements",
        "branch with best placement", "best branch placement",
    ]),
    ("counseling", "is_coding_hard",   [
        "is coding difficult", "is coding hard", "coding tough",
        "can i learn coding", "i am scared of coding", "coding scary",
    ]),
    ("counseling", "college_life",     [
        "how is college life", "how is life in college", "college life like",
        "how is campus life", "is college life good", "tell me about college life",
    ]),
    ("counseling", "is_hostel_safe",   [
        "is hostel safe", "hostel safety", "is hostel good",
        "is girls hostel safe", "hostel secure", "hostel safe",
        "is hostel safe for girls", "hostel security",
    ]),
    ("counseling", "attendance_strict", [
        "is attendance strict", "attendance rules", "how strict is attendance",
        "can i bunk", "what if i miss class",
    ]),
    ("counseling", "low_marks",        [
        "low marks", "low percentage", "less marks",
        "can i get admission with low marks", "marks not good",
        "failed", "low score", "low rank",
    ]),
    ("counseling", "should_join",      [
        "should i join this college", "is this college good", "is vit pune good",
        "worth joining", "recommend this college", "good college",
    ]),
    ("counseling", "mechanical_future", [
        "mechanical future", "scope of mechanical", "is mechanical good",
        "mechanical engineering scope",
    ]),
    ("counseling", "civil_future",     [
        "civil future", "scope of civil", "is civil good", "civil engineering scope",
    ]),
    ("counseling", "entc_future",      [
        "entc future", "scope of entc", "electronics future",
        "is entc good", "entc scope",
    ]),
    ("counseling", "hostel_vs_day",    [
        "hostel or day scholar", "should i stay in hostel",
        "hostel vs day scholar", "is hostel worth it",
    ]),
    ("counseling", "first_year_tips",  [
        "tips for first year", "advice for freshers",
        "what to do in first year", "first year guidance",
    ]),
    ("counseling", "software_career",  [
        "how to get software job", "software career",
        "how to crack placement", "how to get placed", "tips for placement",
    ]),
    ("counseling", "lateral_entry_guidance", [
        "lateral entry good", "should i do lateral entry",
        "diploma to engineering", "is lateral entry worth",
    ]),
    ("counseling", "management_quota_guidance", [
        "management quota good", "should i take management quota",
        "management quota worth it",
    ]),

    # ── Office timings ────────────────────────────────────────────
    # MUST be before campus_life to catch "library timing" etc.
    ("office_timing", "exam_cell",  ["exam cell timing", "exam cell hours", "exam office timing"]),
    ("office_timing", "library",    [
        "library timing", "library timings", "library hours", "library open",
        "when is library", "library time", "library schedule", "what time is library",
    ]),
    ("office_timing", "accounts",   ["accounts timing", "accounts office hours"]),
    ("office_timing", "placement",  ["placement cell timing", "placement office hours"]),
    ("office_timing", None,         [
        "office timing", "office hours", "office open", "office close",
        "working hours", "office time", "college timing", "college hours",
        "what time does office", "when office opens", "office schedule",
        "what are the timings", "when is the office", "college open",
    ]),

    # ── Office location ───────────────────────────────────────────
    ("office_location", "admission",  ["where is admission", "admission office location", "where is the admission"]),
    ("office_location", "exam_cell",  ["where is exam cell", "exam cell location"]),
    ("office_location", "library",    ["where is library", "library location"]),
    ("office_location", "hostel",     ["where is hostel office", "hostel office location"]),
    ("office_location", "placement",  ["where is placement", "placement cell location"]),
    ("office_location", "principal",  ["where is principal", "principal office location"]),
    ("office_location", None,         [
        "where is the office", "office location", "how to reach",
        "where can i find", "directions to", "location of office",
        "where is college", "college address", "college location",
    ]),

    # ── Scholarship ───────────────────────────────────────────────
    # MUST be before fees to catch "fee waiver"
    ("scholarship", None, [
        "scholarship", "financial aid", "fee waiver", "ebc",
        "obc scholarship", "free education", "mahadbt",
        "merit scholarship", "sc st scholarship", "minority scholarship",
    ]),

    # ── Admission dates / deadlines ───────────────────────────────
    # MUST be before fees — "fee payment deadline", "last date to pay fees" etc.
    ("admission_dates", "last_date",   [
        "last date", "deadline", "last day", "closing date",
        "apply by", "apply before", "application deadline",
        "due date", "submission deadline", "final date",
        "fee payment deadline", "deadline for payment", "last date to pay",
        "last date for fee", "fee submission deadline", "when to pay fees",
        "fee due date", "payment deadline", "when is the deadline",
    ]),
    ("admission_dates", "merit_list",  [
        "merit list", "result date", "when result", "merit result",
        "selection list", "shortlist",
    ]),
    ("admission_dates", "class_start", [
        "classes begin", "classes start", "college start", "when classes",
        "orientation", "induction", "first day of college",
    ]),
    ("admission_dates", "spot_round",  ["spot round", "spot admission", "vacant seats", "remaining seats"]),
    ("admission_dates", None,          [
        "admission date", "admission schedule", "application start", "admission open",
        "when apply", "when can i apply", "when does admission", "admission 2025",
    ]),

    # ── Fees ──────────────────────────────────────────────────────
    ("fees", "hostel_fee",  [
        "hostel fee", "hostel cost", "hostel charges",
        "hostel amount", "hostel expenses", "mess fee", "hostel rent",
    ]),
    ("fees", "exam_fee",    ["exam fee", "examination fee", "exam charges"]),
    ("fees", "total_cost",  [
        "total cost", "total fees", "how much does it cost",
        "total expense", "yearly expense", "annual cost",
    ]),
    ("fees", "installment", ["installment", "fee installment", "pay in parts", "emi", "fee payment plan"]),
    ("fees", "refund",      ["refund", "fee refund", "money back", "cancellation fee", "withdrawal fee"]),
    ("fees", "branch_fee",  ["branch fee", "fee for", "fees for", "which branch fee"]),
    ("fees", None,          [
        "fee", "fees", "tuition", "cost", "charges", "payment",
        "how much", "fee structure", "annual fee", "yearly fee",
    ]),

    # ── Hostel ────────────────────────────────────────────────────
    # MUST be before campus_life to catch "hostel facilities"
    ("hostel", "facilities", [
        "hostel facility", "hostel facilities", "hostel amenities",
        "hostel wifi", "hostel gym", "hostel laundry",
    ]),
    ("hostel", "boys",  ["boys hostel", "gents hostel", "male hostel"]),
    ("hostel", "girls", ["girls hostel", "ladies hostel", "female hostel", "women hostel"]),
    ("hostel", "mess",  [
        "mess timing", "mess food", "hostel mess",
        "breakfast time", "dinner time", "lunch time",
        "breakfast", "dinner", "mess timings", "what time is breakfast",
        "what time is lunch", "what time is dinner", "mess schedule",
    ]),
    ("hostel", None,    [
        "hostel", "accommodation", "boarding", "stay on campus",
        "room available", "on campus stay", "pg", "paying guest",
    ]),

    # ── Campus Life ───────────────────────────────────────────────
    ("campus_life", "clubs",        [
        "club", "clubs", "student club", "technical club", "coding club",
        "robotics club", "ieee", "cultural club", "nss", "ncc",
        "e-cell", "entrepreneurship cell",
    ]),
    ("campus_life", "events",       [
        "fest", "festival", "techfest", "cultural fest", "hackathon",
        "event", "competition", "techvit", "viva", "spardha", "annual event",
    ]),
    ("campus_life", "sports",       [
        "sports", "cricket", "football", "basketball", "badminton",
        "gym", "gymnasium", "athletics", "sports facility", "playground",
    ]),
    ("campus_life", "cafeteria",    [
        "cafeteria", "canteen", "food", "mess food", "college food",
        "eating", "restaurant", "snacks",
    ]),
    ("campus_life", "library",      [
        "library", "books", "reading room", "digital library",
        "ieee xplore", "study room",
    ]),
    ("campus_life", "transport",    [
        "bus", "college bus", "transport", "how to reach college",
        "bus route", "bus pass", "metro", "commute",
    ]),
    ("campus_life", "coding_culture", [
        "coding culture", "competitive programming", "leetcode",
        "hackerrank", "codeforces", "open source", "github", "coding community",
    ]),
    ("campus_life", "internet",     [
        "wifi", "wi-fi", "internet", "internet speed", "campus wifi", "network",
    ]),
    ("campus_life", None,           [
        "campus", "campus life", "infrastructure", "facilities",
        "college facilities", "campus facilities", "what is there in college",
    ]),

    # ── Academics ─────────────────────────────────────────────────
    ("academics", "grading",    [
        "grading system", "cgpa", "sgpa", "how is grading",
        "marks system", "grade system", "how are marks calculated",
    ]),
    ("academics", "attendance", [
        "attendance percentage", "minimum attendance", "attendance requirement",
        "75 percent attendance", "attendance criteria",
    ]),
    ("academics", "exams",      [
        "exam pattern", "exam schedule", "when are exams", "exam timetable",
        "university exam", "internal exam", "end sem", "mid sem",
    ]),
    ("academics", "projects",   [
        "project", "final year project", "mini project",
        "project topics", "project guidance",
    ]),
    ("academics", "internship", [
        "industrial training", "academic internship", "college internship program",
    ]),
    ("academics", None,         [
        "academic", "academics", "syllabus overview", "curriculum", "study", "learning",
    ]),

    # ── RAG intents ───────────────────────────────────────────────
    ("hostel_rules",      None, [
        "hostel rule", "hostel policy", "hostel timing", "visitor rule",
        "hostel regulation", "hostel curfew", "hostel discipline",
    ]),
    ("syllabus_query",    None, [
        "syllabus", "subject", "unit", "module", "topic",
        "curriculum", "taught", "course content", "what subjects",
    ]),
    ("policy_query",      None, ["policy", "regulation", "guideline", "code of conduct", "discipline"]),
    ("admission_process", None, [
        "admission process", "how to apply", "apply for admission", "steps to apply",
        "procedure", "admission procedure", "cap process", "cap round",
        "how does admission work", "what is the process", "how to take admission",
        "admission steps", "how do i apply", "counseling process",
        "admission counseling", "how to get admission", "admission procedure steps",
    ]),

    # ── Documents ─────────────────────────────────────────────────
    ("documents", "submission_location", [
        "where to submit", "where do i submit", "submission location", "where submit",
    ]),
    ("documents", "submission_timing",   [
        "when to submit", "submission time", "submission date", "when submit",
    ]),
    ("documents", "required_docs",       [
        "what documents", "which documents", "documents required",
        "documents needed", "certificates needed", "what papers",
    ]),
    ("documents", "gap_certificate",     ["gap certificate", "gap year", "gap affidavit"]),
    ("documents", "originals",           ["original documents", "originals required", "do i need originals"]),
    ("documents", None,                  [
        "document", "certificate", "marksheet", "papers",
        "tc", "aadhar", "migration", "domicile", "anti ragging",
    ]),

    # ── Cutoff / Eligibility ──────────────────────────────────────
    ("cutoff",      None, [
        "cutoff", "cut off", "cut-off", "minimum marks",
        "percentage required", "minimum percentage", "what marks needed", "marks required",
    ]),
    ("eligibility", None, [
        "eligible", "eligibility", "qualification", "criteria",
        "who can apply", "requirement", "can i apply", "am i eligible",
    ]),

    # ── Placements ───────────────────────────────────────────────
    # MUST be before branches — "branch wise placements", "highest package", etc.
    ("placements", "by_branch",      [
        "placement in", "package in", "salary in", "placement for", "jobs in",
        "branch wise placement", "branch wise placements", "branchwise placement",
        "placement by branch", "placements by branch",
    ]),
    ("placements", "highest_package", [
        "highest package", "highest salary", "highest ctc", "maximum package",
        "best package", "top package", "highest paying", "maximum salary",
    ]),
    ("placements", "average_package", [
        "average package", "average salary", "average ctc", "mean package",
        "typical salary", "average lpa",
    ]),
    ("placements", "internship",     [
        "internship stipend", "placement internship", "internship companies",
        "internship opportunity", "where to do internship", "summer internship",
        "internship", "industrial training",
    ]),
    ("placements", "training",       [
        "placement training", "aptitude training", "interview preparation",
        "mock interview", "coding training",
    ]),
    ("placements", "higher_studies", ["gate", "gre", "ms abroad", "higher studies", "mba", "upsc", "mpsc"]),
    ("placements", "recruiters",     [
        "recruiter", "recruiters", "which companies recruit", "companies visit",
        "companies come", "which companies come", "top companies", "hiring companies",
        "which company", "company list",
    ]),
    ("placements", None,             [
        "placement", "placements", "package", "salary", "lpa", "ctc",
        "hiring", "campus recruitment", "on campus", "off campus",
        "job", "placed", "placement rate", "placement percentage",
        "placement record", "placement statistics",
    ]),

    # ── Branches ─────────────────────────────────────────────────
    # AFTER placements — so "branch wise placements" hits placements first
    ("branches", None, [
        "branch", "branches", "which courses", "courses offered", "what courses",
        "available courses", "department", "stream", "what engineering",
        "how many branches", "list of branches",
    ]),

    # ── Database / Personal ───────────────────────────────────────
    ("attendance",  None, ["attendance", "present", "absent", "missed class", "attendance record", "my attendance"]),
    ("timetable",   None, ["timetable", "schedule", "class schedule", "lecture time", "when is my next class", "my timetable"]),
    ("assignments", None, ["assignment", "homework", "task", "submission", "due", "pending work", "my assignment"]),
    ("notices",     None, ["notice", "announcement", "circular", "update", "notification", "latest news"]),

    # ── Contact ──────────────────────────────────────────────────
    ("contact", "email",    ["email", "mail id", "email id", "email address"]),
    ("contact", "website",  ["website", "web address", "online portal", "url", "official site", "college website"]),
    ("contact", "helpline", ["helpline", "toll free", "emergency number", "anti ragging number"]),
    ("contact", None,       [
        "contact", "phone", "number", "reach", "call",
        "office number", "contact number", "phone number",
    ]),

    # ── Thanks / Farewell ─────────────────────────────────────────
    ("thanks",   None, ["thank you", "thanks", "thank u", "thx", "appreciate", "helpful", "that helps"]),
    ("farewell", None, ["goodbye", "good bye", "see you", "bye", "exit", "quit", "take care"]),
]


def _extract_branch(query: str) -> Optional[str]:
    q = query.lower()
    # Use word-boundary matching to avoid false positives like "it" in "tuition"
    import re
    for alias, canonical in _BRANCH_ALIASES.items():
        # Match alias as a whole word (surrounded by non-alphanumeric chars or string boundaries)
        pattern = r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])'
        if re.search(pattern, q):
            return canonical
    return None


def _is_greeting(query: str) -> bool:
    q = query.lower().strip()
    words = set(q.split())
    if q in _GREETING_PHRASES:
        return True
    for phrase in _GREETING_PHRASES:
        if q.startswith(phrase):
            return True
    return bool(words & _GREETING_WORDS)


def detect_intent(query: str) -> Tuple[str, Optional[str], float, Optional[str]]:
    """
    Returns (intent, sub_intent, confidence, extracted_entity).
    Scoring: exact word-boundary match = 0.85, partial = len(kw)/len(q) clamped [0.4, 1.0].
    When scores tie, the FIRST matching rule wins — so order matters.
    """
    import re as _re
    q = query.lower().strip()
    # Strip trailing punctuation for cleaner matching
    q_clean = _re.sub(r'[?!.,;:]+$', '', q).strip()
    entity = _extract_branch(q_clean)

    if _is_greeting(q_clean):
        return "greeting", None, 1.0, None

    best_match = ("general_chat", None, 0.0)

    for intent, sub_intent, keywords in _INTENT_RULES:
        for kw in keywords:
            if kw in q_clean:
                # Word-boundary check: keyword surrounded by spaces or string edges
                if f" {kw} " in f" {q_clean} ":
                    score = 0.85
                else:
                    score = len(kw) / len(q_clean) if len(q_clean) > 0 else 0
                score = max(0.4, min(1.0, score))
                if score > best_match[2]:
                    best_match = (intent, sub_intent, score)

    return best_match[0], best_match[1], best_match[2], entity
