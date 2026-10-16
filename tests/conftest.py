"""
Shared pytest setup for find_the_cup tests.
"""

import sys
import os

# Add parent dir so we can import the game modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


@pytest.fixture(autouse=True)
def isolated_high_score(tmp_path, monkeypatch):
    """Point every test at a throwaway high score file, never the player's real one."""
    import find_the_cup
    path = str(tmp_path / "highscore.json")
    monkeypatch.setattr(find_the_cup, "HIGH_SCORE_FILE", path)
    return path
