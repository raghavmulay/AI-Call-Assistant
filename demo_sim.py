import sys, json
sys.path.insert(0, '.')
from backend.app.ai.intent.intent_detector import detect_intent
from backend.app.ai.prompts.serializer import serializer

def load(p):
    return json.load(open(p, encoding='utf-8'))

fees    = load('backend/app/ai/knowledge/fees.json')
hostel  = load('backend/app/ai/knowledge/hostel/hostel.json')
pl      = load('backend/app/ai/knowledge/placements/placements.json')
campus  = load('backend/app/ai/knowledge/campus_life.json')
counsel = load('backend/app/ai/knowledge/counseling.json')
docs    = load('backend/app/ai/knowledge/documents.json')
office  = load('backend/app/ai/knowledge/office/office.json')
adm     = load('backend/app/ai/knowledge/admission/dates.json')

data_map = {
    'fees':             fees,
    'hostel':           hostel,
    'hostel_rules':     hostel,
    'placements':       pl,
    'scholarship':      pl['scholarship'],
    'campus_life':      campus,
    'counseling':       counsel,
    'documents':        docs,
    'contact':          office,
    'office_timing':    office,
    'office_location':  office,
    'branches':         adm['branches'],
    'cutoff':           adm['cutoff'],
    'eligibility':      adm['eligibility'],
    'admission_process':adm['process'],
    'admission_dates':  adm['schedule'],
}

QUICK = {
    'greeting': 'Hello! I am Aria, your AI admission counselor at VIT Pune. How can I help you today?',
    'thanks':   'You are welcome! Feel free to ask if you have more questions.',
    'farewell': 'Goodbye! Best of luck with your admission. Feel free to call back anytime.',
}

demo_queries = [
    # Hostel
    'What are the hostel fees?',
    'Does the hostel fee include mess?',
    'Tell me about boys hostel',
    'Is the hostel safe for girls?',
    'What are the hostel facilities?',
    'What time is breakfast in the mess?',
    # Placements
    'What is the placement record?',
    'How are placements in computer engineering?',
    'Which companies come for recruitment?',
    'What is the average package?',
    'Are internships available?',
    'Does the college provide placement training?',
    # Admissions
    'What is the admission process?',
    'When is the last date to apply?',
    'What is the cutoff for computer engineering?',
    'Am I eligible if I have 60 percent?',
    'What documents do I need for admission?',
    'When do classes begin?',
    # Counseling
    'AI vs IT which is better?',
    'Which branch has the best placements?',
    'Is coding difficult for beginners?',
    'Should I join this college?',
    'What is the scope of mechanical engineering?',
    'Hostel or day scholar which is better?',
    # Fees
    'What are the tuition fees?',
    'What is the total annual cost?',
    'Is there a fee installment option?',
    'Tell me about scholarships',
    'Is there a fee refund policy?',
    # Campus Life
    'What clubs are there in college?',
    'Tell me about the annual fest',
    'What sports facilities are available?',
    'How is the coding culture?',
    'What are the library timings?',
    'Is there a college bus?',
    # Office / Contact
    'What are the office timings?',
    'Where is the admission office?',
    'What is the college phone number?',
    'What is the college website?',
    # Branches / Academics
    'How many branches are offered?',
    'What is the grading system?',
    'What is the attendance requirement?',
    # Greetings
    'Hello',
    'Thank you',
    'Goodbye',
]

print('DEMO SIMULATION — %d queries' % len(demo_queries))
print('=' * 70)

ok_count = 0
issues = []

for q in demo_queries:
    intent, sub, conf, entity = detect_intent(q)

    if intent in QUICK:
        response = QUICK[intent]
    else:
        data = data_map.get(intent)
        if data:
            response = serializer.serialize(intent, data, sub_intent=sub, entity=entity)
        else:
            response = '[LLM fallback — general conversation]'

    is_ok = bool(response) and len(response.strip()) > 10
    status = 'OK' if is_ok else 'EMPTY'
    if is_ok:
        ok_count += 1
    else:
        issues.append(q)

    short = (response[:90] + '...') if len(response) > 90 else response
    print('[%s] Q: %s' % (status, q))
    print('     intent=%-20s sub=%-20s entity=%s' % (intent, str(sub), str(entity)))
    print('     -> %s' % short)
    print()

print('=' * 70)
print('RESULT: %d/%d responses OK' % (ok_count, len(demo_queries)))
if issues:
    print('ISSUES:')
    for i in issues:
        print('  - ' + i)
else:
    print('All responses generated successfully.')
