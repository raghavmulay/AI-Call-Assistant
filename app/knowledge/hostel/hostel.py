import json, os

_PATH = os.path.join(os.path.dirname(__file__), "hostel.json")

def load():
    with open(_PATH, encoding="utf-8") as f:
        return json.load(f)
