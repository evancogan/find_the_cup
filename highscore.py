"""
High score storage for Find the Cup.
Keeps the best streak in a small JSON file so it survives closing the game.
"""

import json
import os


def load_high_score(path):
    """Return the saved best streak, or 0 if the file is missing or unreadable."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            score = json.load(f).get("best_streak", 0)
    except (OSError, ValueError, AttributeError):
        return 0
    # Ignore anything that isn't a sensible score (e.g. hand-edited file)
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        return 0
    return score


def save_high_score(score, path):
    """Write *score* as the best streak. Returns False if the file can't be written."""
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump({"best_streak": score}, f)
        # Replace in one step so a crash mid-write can't leave a corrupt file
        os.replace(tmp_path, path)
    except OSError:
        return False
    return True
