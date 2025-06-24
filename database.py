# database.py

import json
import os
import threading

LOCK = threading.Lock()

# Mapping names to filenames
DB_FILES = {
    "users": "users.json",
    "complaints": "complaints.json",
    "referrals": "railway.json"
}

def load(name):
    """Load data from a JSON file."""
    if not os.path.exists(DB_FILES[name]):
        save(name, {})  # create empty file if not exists
    with LOCK, open(DB_FILES[name], "r", encoding="utf-8") as f:
        return json.load(f)

def save(name, data):
    """Save data to a JSON file."""
    with LOCK, open(DB_FILES[name], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
