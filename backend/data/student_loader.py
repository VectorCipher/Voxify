import json
import os
import re

DATA_PATH = os.path.join("data", "students.json")

def load_students():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["students"]

def extract_roll_no(text: str):
    match = re.search(r"roll\s*(number|no)?\s*(\d+)", text.lower())
    if match:
        return int(match.group(2))
    return None

def get_student(text: str):
    students = load_students()
    text_lower = text.lower()

    roll_no = extract_roll_no(text_lower)
    if roll_no is not None:
        for student in students:
            if student["roll_no"] == roll_no:
                return student


    for student in students:
        if student["name"].lower() in text_lower:
            return student

    return None
