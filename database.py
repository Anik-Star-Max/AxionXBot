# database.py

import json
import os

def load(filename):
    if not os.path.exists(f"{filename}.json"):
        return {}
    try:
        with open(f"{filename}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save(filename, data):
    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Auto-create blank files if missing
for fname in ["users", "complaints", "railway"]:
    if not os.path.exists(f"{fname}.json"):
        save(fname, {})
