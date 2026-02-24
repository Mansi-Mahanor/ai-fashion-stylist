
import json
import os

DB_FILE = "designs.json"

def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_design(username, gender,style_vibe, occasion, outfit,image_base64):

    data = load_data()

    if username not in data:
        data[username] = []

    data[username].append({
        "gender": gender,
        "style": style_vibe,
        "occasion": occasion,
        "outfit": outfit,
        "image": image_base64
    })

    save_data(data)

def get_user_designs(username):
    data = load_data()
    return data.get(username, [])