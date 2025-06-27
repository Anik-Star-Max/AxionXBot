import json
import os

def load(file):
    """Load data from a JSON file. Returns an empty dict if file not found or invalid."""
    try:
        with open(f"{file}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save(file, data):
    """Save data to a JSON file."""
    with open(f"{file}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def report_user(reporter_id: str, reported_id: str, reason: str = "No reason provided"):
    """Add a user report to reports.json"""
    reports = load("reports")
    if reported_id not in reports:
        reports[reported_id] = []

    reports[reported_id].append({
        "reporter": reporter_id,
        "reason": reason
    })

    save("reports", reports)
