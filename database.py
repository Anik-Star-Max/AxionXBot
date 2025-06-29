import json
import os

USERS_DB = "users.json"

def load_json(filename):
    """Load data from JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename, data):
    """Save data to JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# 🔄 Load users at start
users = load_json(USERS_DB)

def save_users(updated_data=None):
    """Update users.json safely."""
    if updated_data is None:
        updated_data = users
    save_json(USERS_DB, updated_data)
