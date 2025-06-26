import json
import os

DB_FOLDER = "data"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def load(name):
    path = f"{DB_FOLDER}/{name}.json"
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)

def save(name, data):
    path = f"{DB_FOLDER}/{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
