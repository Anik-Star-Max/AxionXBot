import json
import os

DATA_PATH = "data"
USERS_DB = os.path.join(DATA_PATH, "users.json")

# Make sure data folder exists
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# Load users
def load_users():
    try:
        with open(USERS_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save users
def save_users(data):
    with open(USERS_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# Global user dict
users = load_users()
