import json
import os

# Load data from a JSON file
def load(filename):
    file_path = f"{filename}.json"

    # If file doesn't exist, create default content
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            default_data = [] if filename == "reports" else {}
            json.dump(default_data, f, indent=4)

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Save data to a JSON file
def save(filename, data):
    file_path = f"{filename}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
