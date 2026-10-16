"""
Tests for the saved high score (best streak).
Run with: pytest tests/test_high_score.py -v

Every test gets a throwaway high score file from the autouse fixture in conftest.py.
"""

import json

import pytest

from test_find_the_ball import _win_on_purpose, _play_rounds


# ---- Saving and loading -----------------------------------------------------

def test_missing_file_means_zero(tmp_path):
    """With no save file yet, the best streak is zero."""
    from highscore import load_high_score
    assert load_high_score(str(tmp_path / "nope.json")) == 0


def test_save_then_load_round_trips(tmp_path):
    """A saved score is read back exactly."""
    from highscore import load_high_score, save_high_score
    path = str(tmp_path / "hs.json")
    assert save_high_score(7, path) is True
    assert load_high_score(path) == 7


@pytest.mark.parametrize("contents", [
    "not json at all",
    "",
    "[1, 2, 3]",
    '{"best_streak": "seven"}',
    '{"best_streak": -3}',
    '{"best_streak": true}',
    '{"something_else": 4}',
])
def test_bad_file_means_zero(tmp_path, contents):
    """A corrupt or hand-edited save file falls back to zero instead of crashing."""
    from highscore import load_high_score
    path = tmp_path / "hs.json"
    path.write_text(contents, encoding="utf-8")
    assert load_high_score(str(path)) == 0


def test_save_failure_returns_false(tmp_path):
    """If the file can't be written, saving reports failure instead of crashing."""
    from highscore import save_high_score
    missing_dir = tmp_path / "does_not_exist" / "hs.json"
    assert save_high_score(3, str(missing_dir)) is False


# ---- In the game ------------------------------------------------------------

def test_new_game_loads_saved_best(isolated_high_score):
    """A new game starts with the best streak from the save file."""
    import find_the_cup
    from highscore import save_high_score
    save_high_score(4, isolated_high_score)
    game = find_the_cup.Game()
    assert game.best_streak == 4


def test_new_best_is_saved_to_file(isolated_high_score):
    """Beating the best streak writes it to the file straight away."""
    import find_the_cup
    from highscore import load_high_score
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.best_streak == 1
    assert load_high_score(isolated_high_score) == 1


def test_best_survives_closing_the_game(isolated_high_score):
    """A best streak set in one game is there when a fresh game starts (like reopening it)."""
    import find_the_cup
    game = find_the_cup.Game()
    _play_rounds(game, ["win", "win"])
    assert game.streak == 2

    reopened = find_the_cup.Game()
    assert reopened.best_streak == 2


def test_lower_streak_does_not_overwrite_best(isolated_high_score):
    """Winning when the streak is below the saved best leaves the file alone."""
    import find_the_cup
    from highscore import load_high_score, save_high_score
    save_high_score(5, isolated_high_score)
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1
    assert game.best_streak == 5
    assert load_high_score(isolated_high_score) == 5


def test_losing_keeps_best(isolated_high_score):
    """Losing resets the streak but not the best streak, in memory or on disk."""
    import find_the_cup
    from highscore import load_high_score
    game = find_the_cup.Game()
    _play_rounds(game, ["win", "lose"])
    assert game.streak == 0
    assert game.best_streak == 1
    assert load_high_score(isolated_high_score) == 1


def test_explicit_path_is_used(tmp_path, isolated_high_score):
    """Game(high_score_path=...) reads and writes that file, not the default one."""
    import find_the_cup
    from highscore import load_high_score
    own_path = str(tmp_path / "custom.json")
    game = find_the_cup.Game(high_score_path=own_path)
    _win_on_purpose(game)
    assert load_high_score(own_path) == 1
    assert load_high_score(isolated_high_score) == 0


# ---- Start screen -----------------------------------------------------------

def test_best_streak_shown_on_start_screen(isolated_high_score):
    """The start screen (MENU) shows the saved best streak."""
    import find_the_cup
    from highscore import save_high_score
    save_high_score(3, isolated_high_score)
    game = find_the_cup.Game()
    assert game.phase == find_the_cup.Phase.MENU
    assert "Best streak: 3" in game.get_display()


def test_best_streak_shown_as_zero_first_time():
    """With no save file, the start screen shows a best streak of 0."""
    import find_the_cup
    game = find_the_cup.Game()
    assert "Best streak: 0" in game.get_display()


def test_best_streak_text_is_rendered():
    """The best streak line is actually drawn on the start screen."""
    import find_the_cup
    import pygame
    game = find_the_cup.Game()
    surf = pygame.Surface((find_the_cup.WIDTH, find_the_cup.HEIGHT))
    game.render(surf)
    # render() puts line i at y = 50 + i * (font_small height + 8); best streak is line 1
    y = 50 + 1 * (find_the_cup.font_small.get_height() + 8)
    found = any(
        surf.get_at((x, yy))[:3] == find_the_cup.GRAY
        for x in range(find_the_cup.WIDTH // 2 - 80, find_the_cup.WIDTH // 2 + 80)
        for yy in range(y - 10, y + 10)
    )
    assert found, f"No GRAY text pixels found where the best streak line should be (y≈{y})"
