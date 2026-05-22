"""
counseling_handler.py — Conversational guidance responses for branch/career counseling.
Handles sub-intents from the counseling intent without touching the LLM.
"""

from typing import Optional


_RESPONSES = {
    "best_branch": (
        "Great question! The best branch really depends on your interests. "
        "If you enjoy coding and software, Computer Engineering or IT are excellent choices — "
        "they have the highest placement rates (90–92%) and average packages of Rs. 5.5–6 LPA. "
        "If you're into electronics and hardware, ENTC is a solid pick. "
        "Mechanical and Civil are great if you prefer core engineering. "
        "What are your interests? That'll help narrow it down."
    ),
    "cs_vs_it": (
        "Both Computer Engineering and IT are very similar in curriculum and career prospects. "
        "CS has a slightly higher cutoff and average package (Rs. 6 LPA vs Rs. 5.5 LPA for IT). "
        "Both branches see top recruiters like TCS, Infosys, Wipro, and Persistent. "
        "If you get CS, great — but IT is equally strong and the difference in outcomes is minimal."
    ),
    "ai_vs_it": (
        "At VIT Pune, AI/ML is part of the Computer Engineering curriculum, not a separate branch. "
        "IT (Information Technology) is a dedicated branch with strong placements — average Rs. 5.5 LPA, "
        "highest Rs. 16 LPA, and a 90% placement rate. "
        "If your goal is AI/ML, Computer Engineering is the closest match. "
        "IT is also a great option with excellent industry exposure."
    ),
    "best_placements": (
        "For placements, Computer Engineering leads with a 92% placement rate and average Rs. 6 LPA. "
        "IT is a close second at 90% and Rs. 5.5 LPA. "
        "ENTC follows at 78%, and Mechanical at 75%. "
        "If placements are your priority, CS or IT are the strongest choices."
    ),
    "is_coding_hard": (
        "Coding can feel challenging at first, but it gets much easier with practice. "
        "VIT Pune has a strong coding culture with clubs, hackathons, and platforms like LeetCode and HackerRank. "
        "Most students who put in consistent effort find it very rewarding. "
        "Don't let the initial learning curve discourage you!"
    ),
    "college_life": (
        "College life at VIT Pune is vibrant! There are technical clubs, cultural fests, sports facilities, "
        "and a strong placement cell. The campus has good infrastructure, Wi-Fi, a library, and a cafeteria. "
        "Students generally find the environment supportive and engaging."
    ),
    "is_hostel_safe": (
        "Yes, the hostel is safe. There's 24x7 security with CCTV at all entry and exit points. "
        "The girls hostel has a separate gate with female security staff round the clock. "
        "There's also a medical room and tie-up with a nearby hospital for emergencies."
    ),
    "attendance_strict": (
        "Yes, attendance is taken seriously — a minimum of 75% is required to be eligible for exams. "
        "It's best to stay regular. If you miss classes due to genuine reasons, "
        "you can apply for medical or other leave through the proper process."
    ),
    "low_marks": (
        "Don't worry — there are options. If your PCM percentage is above 50% (45% for reserved categories), "
        "you're eligible. Branches like Civil and Mechanical have lower cutoffs. "
        "Management quota admissions are also available directly through the college. "
        "Would you like details on the cutoffs or management quota process?"
    ),
    "should_join": (
        "VIT Pune has a solid reputation for placements, infrastructure, and faculty. "
        "With 120+ companies visiting campus and an 85% placement rate, it's a good choice. "
        "The campus has good facilities and an active student community. "
        "It's definitely worth considering, especially for CS, IT, and ENTC branches."
    ),
    "mechanical_future": (
        "Mechanical Engineering has a steady scope in core industries like automotive, manufacturing, "
        "and energy. Companies like Tata Motors, Mahindra, Cummins, and Thermax recruit from VIT Pune. "
        "Average package is Rs. 3.5 LPA. If you're interested in core engineering, it's a solid choice."
    ),
    "civil_future": (
        "Civil Engineering has good scope in construction, infrastructure, and real estate. "
        "Companies like L&T Construction, Shapoorji Pallonji, and Godrej Properties recruit from campus. "
        "Average package is Rs. 3 LPA. Government jobs (PWD, MSRDC) are also a popular path."
    ),
    "entc_future": (
        "ENTC (Electronics and Telecommunication) has strong scope in embedded systems, IoT, telecom, "
        "and semiconductor industries. Recruiters include L&T, Siemens, Bosch, Honeywell, and Qualcomm. "
        "Average package is Rs. 4 LPA with a 78% placement rate."
    ),
    "hostel_vs_day": (
        "It depends on your situation. Hostel life gives you independence, peer learning, and saves commute time. "
        "The fee is Rs. 60,000 per year including mess. "
        "Day scholar is cheaper but requires a reliable commute. "
        "If you live far from campus, hostel is generally the better choice for focus and convenience."
    ),
    "first_year_tips": (
        "For first year: attend all classes to build your foundation, join at least one technical club, "
        "start practicing coding early on platforms like LeetCode, and maintain above 75% attendance. "
        "Don't stress too much — focus on learning and building good habits from day one."
    ),
    "software_career": (
        "To get a software job: build strong DSA skills on LeetCode and HackerRank, "
        "work on projects and put them on GitHub, do internships in 6th or 7th semester, "
        "and participate in the college placement training program. "
        "Companies like TCS, Infosys, Wipro, and Persistent actively recruit from campus."
    ),
    "lateral_entry_guidance": (
        "Lateral entry (direct second year) is a great option for diploma holders. "
        "You need to appear for MHT-CET (diploma) exam and register on the DTE portal. "
        "10% additional seats are reserved for lateral entry students. "
        "It saves one year and you join directly in the second year."
    ),
    "management_quota_guidance": (
        "Management quota is 15% of seats, filled directly by the college. "
        "It's a good option if your CET score isn't high enough for CAP rounds. "
        "Contact the admission office directly for management quota availability and fees. "
        "Phone: 020-12345678."
    ),
}

_DEFAULT = (
    "That's a great question to think about before choosing your branch. "
    "I'd suggest considering your interests, career goals, and the placement statistics for each branch. "
    "Computer Engineering and IT have the strongest placements here. "
    "Would you like details on a specific branch or career path?"
)


def handle_counseling(query: str = "", sub_intent: Optional[str] = None) -> str:
    if sub_intent and sub_intent in _RESPONSES:
        return _RESPONSES[sub_intent]

    # Fallback: try to match query keywords to a sub-intent
    q = query.lower()
    if "ai" in q and "it" in q:
        return _RESPONSES["ai_vs_it"]
    if "cs" in q and "it" in q:
        return _RESPONSES["cs_vs_it"]
    if "best" in q and "placement" in q:
        return _RESPONSES["best_placements"]
    if "best" in q or "which branch" in q or "should i choose" in q:
        return _RESPONSES["best_branch"]
    if "mechanical" in q:
        return _RESPONSES["mechanical_future"]
    if "civil" in q:
        return _RESPONSES["civil_future"]
    if "entc" in q or "electronics" in q:
        return _RESPONSES["entc_future"]
    if "hostel" in q and ("safe" in q or "good" in q):
        return _RESPONSES["is_hostel_safe"]
    if "coding" in q and ("hard" in q or "difficult" in q or "scared" in q):
        return _RESPONSES["is_coding_hard"]
    if "software" in q or "placed" in q or "crack" in q:
        return _RESPONSES["software_career"]

    return _DEFAULT
