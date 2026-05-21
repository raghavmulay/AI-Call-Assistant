"""
Hybrid intent detector.
- Greetings use STRICT whole-word matching.
- Sub-intents for contact, documents, fees, office for finer routing.
- Branch extraction for queries like "What is IT branch fees?"
- Returns (intent, sub_intent, confidence, extracted_entity)
"""

# ── Branch name aliases ────────────────────────────────────────────
_BRANCH_ALIASES = {
    "computer":         "computer engineering",
    "cs":               "computer engineering",
    "cse":              "computer engineering",
    "it":               "information technology",
    "information tech": "information technology",
    "entc":             "electronics and telecommunication",
    "electronics":      "electronics and telecommunication",
    "mechanical":       "mechanical engineering",
    "mech":             "mechanical engineering",
    "civil":            "civil engineering",
    "electrical":       "electrical engineering",
    "ai":               "computer engineering",
}

# ── Strict greeting words ──────────────────────────────────────────
_GREETING_WORDS   = {"hello", "hi", "hey", "howdy", "greetings", "sup"}
_GREETING_PHRASES = ["good morning", "good afternoon", "good evening", "good night"]

# ── Intent rules — order matters: specific before generic ─────────
_INTENT_RULES = [

    # ── Emergency ─────────────────────────────────────────────────
    ("emergency", None,        ["emergency", "fire", "accident", "danger", "sos", "ambulance"]),
    ("alert",     None,        ["alert", "unauthorized", "threat", "intruder"]),

    # ── RAG intents ───────────────────────────────────────────────
    ("hostel_rules",      None, ["hostel rule", "hostel policy", "hostel timing", "visitor rule", "hostel regulation", "hostel curfew"]),
    ("syllabus_query",    None, ["syllabus", "subject", "unit", "module", "topic", "curriculum", "taught", "course content"]),
    ("policy_query",      None, ["policy", "regulation", "guideline", "code of conduct", "discipline"]),
    ("admission_process", None, ["admission process", "how to apply", "apply for admission", "steps to apply",
                                  "procedure", "admission procedure", "cap process", "cap round",
                                  "how does admission work", "what is the process"]),

    # ── Office timings ────────────────────────────────────────────
    ("office_timing", "exam_cell",    ["exam cell timing", "exam cell hours", "exam office timing"]),
    ("office_timing", "library",      ["library timing", "library hours", "library open", "when is library"]),
    ("office_timing", "accounts",     ["accounts timing", "accounts office hours"]),
    ("office_timing", "placement",    ["placement cell timing", "placement office hours"]),
    ("office_timing", None,           ["office timing", "office hours", "office open", "office close",
                                       "working hours", "office time", "college timing", "college hours",
                                       "what time does office", "when office opens", "office schedule",
                                       "what are the timings", "when is the office"]),

    # ── Office location ───────────────────────────────────────────
    ("office_location", "admission",  ["where is admission", "admission office location", "where is the admission"]),
    ("office_location", "exam_cell",  ["where is exam cell", "exam cell location"]),
    ("office_location", "library",    ["where is library", "library location"]),
    ("office_location", "hostel",     ["where is hostel office", "hostel office location"]),
    ("office_location", "placement",  ["where is placement", "placement cell location"]),
    ("office_location", "principal",  ["where is principal", "principal office location"]),
    ("office_location", None,         ["where is the office", "office location", "how to reach", "address of",
                                       "where can i find", "directions to", "location of office",
                                       "where is college", "college address", "college location"]),

    # ── Fees ──────────────────────────────────────────────────────
    ("fees", "hostel_fee",  ["hostel fee", "hostel cost", "hostel charges"]),
    ("fees", "exam_fee",    ["exam fee", "examination fee"]),
    ("fees", "branch_fee",  ["branch fee", "fee for", "fees for", "which branch fee"]),
    ("fees", None,          ["fee", "fees", "tuition", "cost", "charges", "payment", "how much"]),

    # ── Documents ─────────────────────────────────────────────────
    ("documents", "submission_location", ["where to submit", "where do i submit", "submission location", "where submit"]),
    ("documents", "submission_timing",   ["when to submit", "submission time", "submission date", "when submit"]),
    ("documents", "required_docs",       ["what documents", "which documents", "documents required", "documents needed", "certificates needed"]),
    ("documents", None,                  ["document", "certificate", "marksheet", "papers", "tc", "aadhar"]),

    # ── Admission dates / deadlines ───────────────────────────────
    ("admission_dates", "last_date",   ["last date", "deadline", "last day", "closing date",
                                        "apply by", "apply before", "application deadline",
                                        "due date", "submission deadline", "final date"]),
    ("admission_dates", "merit_list",  ["merit list", "result date", "when result", "merit result",
                                        "selection list", "shortlist"]),
    ("admission_dates", "class_start", ["classes begin", "classes start", "college start", "when classes",
                                        "orientation", "induction", "first day of college"]),
    ("admission_dates", None,          ["admission date", "admission schedule", "application start", "admission open",
                                        "when apply", "when can i apply", "when does admission", "admission 2025"]),

    # ── Cutoff / Eligibility ──────────────────────────────────────
    ("cutoff",      None, ["cutoff", "cut off", "cut-off", "minimum marks", "percentage required", "minimum percentage"]),
    ("eligibility", None, ["eligible", "eligibility", "qualification", "criteria", "who can apply", "requirement", "can i apply"]),

    # ── Branches ─────────────────────────────────────────────────
    ("branches", None, ["branch", "branches", "which courses", "courses offered", "what courses",
                        "available courses", "department", "stream", "what engineering"]),

    # ── Placements ───────────────────────────────────────────────
    ("placements", "by_branch",  ["placement in", "package in", "salary in", "placement for"]),
    ("placements", None,         ["placement", "package", "salary", "recruiter", "company", "job", "lpa", "hiring"]),

    # ── Scholarship ──────────────────────────────────────────────
    ("scholarship", None, ["scholarship", "financial aid", "fee waiver", "ebc", "obc scholarship", "free education"]),

    # ── Hostel ───────────────────────────────────────────────────
    ("hostel", "facilities",  ["hostel facility", "hostel facilities", "hostel amenities", "hostel wifi", "hostel mess"]),
    ("hostel", None,          ["hostel", "accommodation", "boarding", "stay on campus", "room available"]),

    # ── Contact ──────────────────────────────────────────────────
    ("contact", "email",   ["email", "mail id", "email id", "email address"]),
    ("contact", "website", ["website", "web address", "online portal", "url", "official site"]),
    ("contact", None,      ["contact", "phone", "number", "helpline", "reach", "call",
                            "telephone", "mobile number", "contact number", "how to contact",
                            "admission office", "office details", "office contact", "office info",
                            "office number", "contact details", "details for", "info about office",
                            "office of admission", "content details"]),

    # ── Thanks / Farewell ─────────────────────────────────────────
    ("thanks",   None, ["thank you", "thanks", "thank u", "thx", "appreciate", "ty", "thankyou"]),
    ("farewell", None, ["goodbye", "good bye", "see you", "take care", "see ya", "later", "bye", "exit", "quit"]),
]


def _extract_branch(query: str) -> str | None:
    q = query.lower()
    for alias, canonical in _BRANCH_ALIASES.items():
        if alias in q:
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


def detect_intent(query: str) -> tuple[str, str | None, float, str | None]:
    """Returns (intent, sub_intent, confidence, extracted_entity)."""
    q = query.lower().strip()
    entity = _extract_branch(q)

    if _is_greeting(q):
        return "greeting", None, 1.0, None

    for intent, sub_intent, keywords in _INTENT_RULES:
        if any(kw in q for kw in keywords):
            return intent, sub_intent, 1.0, entity

    return "general_chat", None, 0.0, entity
