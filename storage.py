import json
import os


SAVE_FILE = "games.json"


def load_games():

    if not os.path.exists(SAVE_FILE):
        return {}

    with open(SAVE_FILE, "r") as file:
        return json.load(file)


def save_games(data):

    with open(SAVE_FILE, "w") as file:
        json.dump(
            data,
            file,
            indent=4
        )

