# storage.py
# WHY: Loading and saving JSON files is repetitive.
# We keep those 10-line patterns here so every other module just calls
# load_json() or save_json() and does not worry about file paths or errors.

import json
import os


def load_json(file_path, default):
    """
    Read a JSON file and return its contents.

    If the file does not exist yet (first run) or is broken,
    we return `default` instead of crashing.

    Parameters:
        file_path : the path to the .json file (a string)
        default   : what to return when the file is missing or broken
                    (usually an empty dict {} or empty list [])
    """
    if not os.path.exists(file_path):
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        # File exists but is broken — return the safe default
        return default


def save_json(file_path, data):
    """
    Write `data` to a JSON file.

    We create the parent folder automatically so the caller
    does not need to worry about whether data/ exists yet.

    Parameters:
        file_path : where to save (e.g. "data/portfolio.json")
        data      : any Python dict or list
    """
    folder = os.path.dirname(file_path)
    if folder != "" and not os.path.exists(folder):
        os.makedirs(folder)

    try:
        with open(file_path, "w", encoding="utf-8") as file:
            # indent=2 makes the file human-readable (each key on its own line)
            json.dump(data, file, indent=2)
    except OSError as error:
        # Print the error but do not crash the whole app
        print(f"Warning: could not save {file_path}: {error}")
