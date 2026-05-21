import random

_GREETINGS = [
    "Hi! Ask me about admissions, fees, or courses.",
    "Hello! How can I help you today?",
    "Hey! What would you like to know?",
]

_THANKS = [
    "You're welcome! Anything else?",
    "Happy to help!",
    "Glad I could assist!",
]

_FAREWELLS = [
    "Goodbye! Best of luck!",
    "Take care! Call again anytime.",
    "Bye! All the best.",
]


def handle_greeting(_: str = "") -> str:
    return random.choice(_GREETINGS)


def handle_thanks(_: str = "") -> str:
    return random.choice(_THANKS)


def handle_farewell(_: str = "") -> str:
    return random.choice(_FAREWELLS)
