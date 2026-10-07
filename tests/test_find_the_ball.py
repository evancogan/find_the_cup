"""
Tests for find_the_cup game.
Run with: pytest tests/test_find_the_ball.py -v
"""

import sys
import os


# Add parent dir so we can import the game module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ---- Helpers ----------------------------------------------------------------

def _advance_to(game, target_phase):
    """Advance the game by calling update() until it reaches *target_phase*."""
    max_steps = 500
    for _ in range(max_steps):
        if game.phase == target_phase:
            break
        game.update(100)
    else:
        pytest.fail(
            f"Game did not reach '{target_phase}' after {max_steps} steps. "
            f"Stuck at '{game.phase}'."
        )


def _full_game(game):
    """Run a complete game cycle: start → dancing → choice."""
    import find_the_cup
    game.start_start()
    _advance_to(game, find_the_cup.Phase.START_LOWER)
    _advance_to(game, find_the_cup.Phase.DANCING)
    _advance_to(game, find_the_cup.Phase.CHOOSING)


def _win_on_purpose(game):
    """Play to the choosing phase and click the cup that has the ball."""
    import find_the_cup
    _full_game(game)
    cup = game.cups[game.ball_idx]
    game.handle_click((int(cup["x"]), int(find_the_cup.CUP_Y + cup["lift"])))
    # Advance through RAISING phase to get to RESULT
    _advance_to(game, find_the_cup.Phase.RESULT)
    assert game.result == "win"


def _lose_on_purpose(game):
    """Play to the choosing phase and click a cup that doesn't have the ball."""
    import find_the_cup
    _full_game(game)
    wrong = next(i for i in range(3) if i != game.ball_idx)
    cup = game.cups[wrong]
    game.handle_click((int(cup["x"]), int(find_the_cup.CUP_Y + cup["lift"])))
    # Advance through RAISING phase to get to RESULT
    _advance_to(game, find_the_cup.Phase.RESULT)
    assert game.result == "lose"


def _next_round(game):
    """Do what the RESTART button does: set up a fresh round and start it."""
    game.reset()
    game.start_start()


def _play_rounds(game, outcomes):
    """Play one round per item in *outcomes* ("win" or "lose"), pressing RESTART between them."""
    for round_number, outcome in enumerate(outcomes):
        if round_number > 0:
            game.reset()
        if outcome == "win":
            _win_on_purpose(game)
        elif outcome == "lose":
            _lose_on_purpose(game)
        else:
            pytest.fail(f"Unknown outcome {outcome!r}, expected 'win' or 'lose'")


# ---- New game ---------------------------------------------------------------

def test_game_initializes_with_three_cups():
    """A new game should have exactly 3 cups."""
    import find_the_cup
    game = find_the_cup.Game()
    assert len(game.cups) == 3


def test_cups_not_stacked_at_start():
    """Cups should be in different horizontal positions at reset."""
    import find_the_cup
    game = find_the_cup.Game()
    slots = [cup["slot"] for cup in game.cups]
    assert len(set(slots)) == 3, f"Cups stacked: {slots}"


def test_all_cups_same_color():
    """All cups should have the same color to hide which one has the ball."""
    import find_the_cup
    game = find_the_cup.Game()
    colors = [cup["color"] for cup in game.cups]
    assert len(set(colors)) == 1, f"Cups have different colors: {colors}"


def test_game_waits_for_start_button():
    """The game should not start automatically; it must wait for the start button."""
    import find_the_cup
    game = find_the_cup.Game()
    assert game.phase == find_the_cup.Phase.MENU, f"Expected Phase.MENU, but got {game.phase}"


def test_start_button_disappears_after_click():
    """The START button disappears as soon as the player clicks it.

    The game transitions from MENU → START, and render() no longer draws
    the START button during the START phase (it only appears in MENU).
    """
    import find_the_cup
    game = find_the_cup.Game()
    assert game.phase == find_the_cup.Phase.MENU

    # Click the start button
    cx = find_the_cup.WIDTH // 2
    cy = find_the_cup.HEIGHT // 2 + 30
    game.handle_click((cx, cy))

    # Phase should have advanced from MENU to START (reveal animation)
    assert game.phase == find_the_cup.Phase.START, \
        f"Expected Phase.START after click, got {game.phase}"

    # The START button must NOT be drawn during the START phase.
    # We verify this by checking that render() does not call _draw_button for START.
    import pygame
    screen = pygame.Surface((800, 600))
    game.render(screen)

    # If the button were still drawn, there would be a green rectangle on the surface.
    # Sample pixels at the button location (center-bottom: cx ± 100, cy ± 30)
    btn_center_x = find_the_cup.WIDTH // 2
    btn_center_y = find_the_cup.HEIGHT // 2 + 60
    for dx in range(-80, 80, 20):
        for dy in range(-25, 25, 20):
            px = screen.get_at((btn_center_x + dx, btn_center_y + dy))
            # GREEN is (50, 180, 50). A filled button would have green pixels here.
            msg = f"Green button pixel found at ({btn_center_x + dx}, {btn_center_y + dy}) — the START button should not be drawn in Phase.START"
            assert px[:3] != (50, 180, 50), msg


def test_cup_click_on_menu_does_not_start_game():
    """Clicking a cup while on the MENU screen must not start the game."""
    import find_the_cup
    game = find_the_cup.Game()
    assert game.phase == find_the_cup.Phase.MENU
    # Click the center of the middle cup (well outside the START button rect)
    cx = find_the_cup.WIDTH // 2
    cy = find_the_cup.CUP_Y
    game.handle_click((cx, cy))
    assert game.phase == find_the_cup.Phase.MENU, \
        f"Phase should still be MENU after clicking a cup on the menu, got {game.phase}"


# ---- Reveal -----------------------------------------------------------------

def test_ball_shown_during_reveal():
    """The ball is visible while the cups lift and while they lower again."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    assert game.ball_visible is True
    _advance_to(game, find_the_cup.Phase.START_LOWER)
    assert game.ball_visible is True


def test_ball_starts_under_its_cup():
    """At the reveal, the ball is horizontally lined up with the cup that has it."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    assert game.ball_x == game.cups[game.ball_idx]["x"]


def test_ball_fully_visible_when_cups_lifted():
    """When the cups reach the top of their lift, the whole ball is below them."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    # The lift peaks right as START hands over to START_LOWER.
    _advance_to(game, find_the_cup.Phase.START_LOWER)
    ball_top = game.ball_y - find_the_cup.BALL_RADIUS
    for cup in game.cups:
        cup_bottom = find_the_cup.CUP_Y + cup["lift"] + find_the_cup.CUP_HEIGHT // 2
        assert ball_top >= cup_bottom, \
            f"Ball top={ball_top} is hidden behind a lifted cup bottom={cup_bottom}"


# ---- Ground -----------------------------------------------------------------

def test_ball_touching_bottom_line():
    """The ball should rest on the ground line when the cups lift."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    assert game.phase == find_the_cup.Phase.START
    assert game.ball_y + find_the_cup.BALL_RADIUS == find_the_cup.GROUND_Y


def test_cup_touching_bottom_line():
    """Every cup should rest on the ground line during the choosing phase."""
    import find_the_cup
    game = find_the_cup.Game()
    _full_game(game)
    assert game.phase == find_the_cup.Phase.CHOOSING
    for cup in game.cups:
        cup_bottom = find_the_cup.CUP_Y + cup["lift"] + find_the_cup.CUP_HEIGHT // 2
        assert cup_bottom == find_the_cup.GROUND_Y


def test_ground_line_is_visible():
    """The ground line should be visible on the screen."""
    import pygame
    import find_the_cup
    game = find_the_cup.Game()
    pygame.init()
    ## I will test the color of the pixels where the ground line should be drawn
    screen = pygame.display.set_mode((find_the_cup.WIDTH, find_the_cup.HEIGHT))
    game.render(screen)
    pygame.display.flip()

    # Test the color of the pixels where the ground line should be
    ground_y = find_the_cup.GROUND_Y
    left_cup_edge = find_the_cup.WIDTH // 2 - find_the_cup.CUP_SPACING - find_the_cup.CUP_WIDTH // 2
    # From where the line starts to just short of the left cup, whose outline overhangs its edge.
    for x in range(100, left_cup_edge - 5):
        pixel_color = screen.get_at((x, ground_y))
        assert pixel_color == find_the_cup.DARK_GRAY, f"Pixel at ({x}, {ground_y}) is {pixel_color}, expected {find_the_cup.DARK_GRAY}"


# ---- Shuffle ----------------------------------------------------------------

def test_ball_obscured_during_dancing():
    """The ball should NOT be visible while cups are dancing/shuffling."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    _advance_to(game, find_the_cup.Phase.DANCING)
    assert game.ball_visible is False, \
        "Ball should be hidden during dancing so player must track the cup"


def test_cups_switch_positions():
    """After dancing, at least one cup should be in a different slot."""
    import find_the_cup
    game = find_the_cup.Game()
    initial_slots = [cup["slot"] for cup in game.cups]
    _full_game(game)
    final_slots = [cup["slot"] for cup in game.cups]
    assert final_slots != initial_slots, \
        f"Cups didn't move: initial_slots={initial_slots}, final_slots={final_slots}"


def test_ball_follows_its_cup_after_shuffle():
    """After the shuffle, the ball's position matches where its cup ended up."""
    import find_the_cup
    game = find_the_cup.Game()
    _full_game(game)
    ball_cup = game.cups[game.ball_idx]
    assert abs(game.ball_x - ball_cup["x"]) < 1, \
        f"Ball at x={game.ball_x} not under its cup at x={ball_cup['x']}"


# ---- Choosing ---------------------------------------------------------------

def test_all_cups_lowered_at_choice():
    """During the choice phase, all cups should be back on the ground (lift=0)."""
    import find_the_cup
    game = find_the_cup.Game()
    _full_game(game)
    assert game.phase == find_the_cup.Phase.CHOOSING
    for i, cup in enumerate(game.cups):
        assert abs(cup["lift"]) < 1, \
            f"Cup {i} lift={cup['lift']} not lowered during choice phase"


def test_cups_not_overlapping_at_choice():
    """During choice phase, no two cups should overlap."""
    import find_the_cup
    game = find_the_cup.Game()
    _full_game(game)
    assert game.phase == find_the_cup.Phase.CHOOSING
    xs = [cup["x"] for cup in game.cups]
    # Cups are drawn centred on x, so centres closer than one cup width overlap.
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            assert abs(xs[i] - xs[j]) >= find_the_cup.CUP_WIDTH, \
                f"Cups {i} and {j} overlap: x={xs[i]}, x={xs[j]}"


def test_clicking_wrong_cup():
    """Clicking the wrong cup should result in 'lose'."""
    import find_the_cup
    game = find_the_cup.Game()
    game.ball_idx = 0
    _full_game(game)
    assert game.phase == find_the_cup.Phase.CHOOSING
    cup_x = int(game.cups[1]["x"])
    cup_y = int(find_the_cup.CUP_Y + game.cups[1]["lift"])
    game.handle_click((cup_x, cup_y))
    # After clicking, cups raise before showing result
    _advance_to(game, find_the_cup.Phase.RESULT)
    assert game.phase == find_the_cup.Phase.RESULT
    assert game.result == "lose"


def test_clicking_right_cup():
    """Clicking the correct cup should result in 'win'."""
    import find_the_cup
    game = find_the_cup.Game()
    game.ball_idx = 2
    _full_game(game)
    assert game.phase == find_the_cup.Phase.CHOOSING
    cup_x = int(game.cups[2]["x"])
    cup_y = int(find_the_cup.CUP_Y + game.cups[2]["lift"])
    game.handle_click((cup_x, cup_y))
    # After clicking, cups raise before showing result
    _advance_to(game, find_the_cup.Phase.RESULT)
    assert game.phase == find_the_cup.Phase.RESULT
    assert game.result == "win"


# ---- Labels and messages ----------------------------------------------------

def test_labels_stay_with_positions_not_cups():
    """Labels mark table positions, like game-show doors: "Cup 1", "Cup 2", "Cup 3"
    from left to right. They stay put while the cups move, so they never reveal
    which cup has the ball. game.cup_labels() returns [(text, x), ...] left to right,
    and render() should draw exactly those."""
    import find_the_cup
    game = find_the_cup.Game()
    game.start_start()
    _advance_to(game, find_the_cup.Phase.DANCING)
    game.update(find_the_cup.SWAP_DURATION // 2)
    # Mid-swap is the only moment where "labels at the slots" and "labels on the cups" differ.
    assert any(cup["x"] not in game.slots for cup in game.cups), "cups should be mid-swap"
    assert game.cup_labels() == [
        ("Cup 1", game.slots[0]),
        ("Cup 2", game.slots[1]),
        ("Cup 3", game.slots[2]),
    ]


def test_lose_message_uses_position_label():
    """After a wrong pick, the message names where the ball was using the label the
    player can see under that position ("Cup 1"/"Cup 2"/"Cup 3"), and no other label."""
    import find_the_cup
    game = find_the_cup.Game()
    _lose_on_purpose(game)
    labels = [text for text, _x in game.cup_labels()]
    ball_slot = game.cups[game.ball_idx]["slot"]
    message = game.get_display()
    assert labels[ball_slot] in message, f"Expected {labels[ball_slot]!r} in {message!r}"
    # Naming every label would pass the check above without saying where the ball was.
    for i, label in enumerate(labels):
        if i != ball_slot:
            assert label not in message, f"{label!r} wrongly appears in {message!r}"


def test_old_cup_names_never_shown():
    """The old identity names ("Cup A/B/C") must not appear in any text the game shows,
    in any phase. render() should take its on-screen text from get_display(), so this
    covers what the player sees."""
    import find_the_cup
    game = find_the_cup.Game()
    texts = [game.get_display()]
    game.start_start()
    texts.append(game.get_display())
    _advance_to(game, find_the_cup.Phase.DANCING)
    texts.append(game.get_display())
    _advance_to(game, find_the_cup.Phase.CHOOSING)
    texts.append(game.get_display())

    loser = find_the_cup.Game()
    _lose_on_purpose(loser)
    texts.append(loser.get_display())

    for text in texts:
        for old_name in ("Cup A", "Cup B", "Cup C"):
            assert old_name not in text, f"Old name {old_name!r} shown in {text!r}"


# ---- Streak and difficulty --------------------------------------------------

def test_new_game_streak_is_zero():
    """The streak is zero at the start of a new game."""
    import find_the_cup
    game = find_the_cup.Game()
    assert game.streak == 0


def test_win_increases_streak():
    """Winning a round increases the streak by one."""
    import find_the_cup
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1



def test_loss_resets_streak():
    """Losing a round resets the streak to zero. Win first, so there's a streak to lose."""
    import find_the_cup
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1
    # Now lose a round
    loser = find_the_cup.Game()
    _lose_on_purpose(loser)
    assert loser.streak == 0


def test_streak_survives_next_round():
    """After a win, the streak is still there once the next round starts."""
    import find_the_cup
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1
    # Start a new round (like pressing RESTART)
    _next_round(game)
    assert game.streak == 1


def test_swaps_get_faster_with_streak():
    """A swap takes less time at a higher streak."""
    import find_the_cup
    # Compare swap duration at streak=0 vs streak=5
    fast_game = find_the_cup.Game()
    fast_game.streak = 5
    fast_swap_dur = fast_game._swap_duration()
    slow_game = find_the_cup.Game()
    slow_game.streak = 0
    slow_swap_dur = slow_game._swap_duration()
    assert fast_swap_dur < slow_swap_dur, \
        f"Swap at streak=5 ({fast_swap_dur}ms) should be faster than streak=0 ({slow_swap_dur}ms)"


def test_swap_speed_has_a_limit():
    """However long the streak, a swap never takes less than the minimum duration."""
    import find_the_cup
    game = find_the_cup.Game()
    game.streak = 100  # absurdly high streak
    min_duration = 200  # assumed minimum from game constants
    assert game._swap_duration() >= min_duration, \
        f"Swap duration {game._swap_duration()}ms is below minimum {min_duration}ms"


def test_streak_shown_to_player():
    """The streak is shown to the player during the game."""
    import find_the_cup
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1
    display = game.get_display()
    assert "Streak: 1" in display, f"Streak '1' not shown in {display!r}"


def test_streak_text_is_actually_rendered():
    """The streak text is drawn on the screen surface, not just present in get_display()."""
    import find_the_cup
    import pygame
    game = find_the_cup.Game()
    _win_on_purpose(game)
    assert game.streak == 1
    # Render to a blank surface
    surf = pygame.Surface((find_the_cup.WIDTH, find_the_cup.HEIGHT))
    game.render(surf)
    # Compute where render() places each line: y_i = 50 + i * (font_small.get_height() + 8)
    font_h = find_the_cup.font_small.get_height()
    spacing = font_h + 8
    streak_line_idx = 2  # line index for "Streak: N"
    streak_y = 50 + streak_line_idx * spacing
    # Look for GRAY-colored pixels (with anti-aliasing tolerance) around the expected position
    # GRAY is (180, 180, 180); allow some tolerance for darkening (e.g., from RESULT overlay)
    found_gray = False
    search_rect = pygame.Rect(find_the_cup.WIDTH // 2 - 60, streak_y - 15, 120, 30)
    for x in range(search_rect.left, search_rect.right):
        for y in range(search_rect.top, search_rect.bottom):
            if 0 <= x < find_the_cup.WIDTH and 0 <= y < find_the_cup.HEIGHT:
                r, g, b = surf.get_at((x, y))[:3]
                # Check if pixel is close to GRAY (allowing for darkening)
                if abs(r - 180) <= 100 and abs(g - 180) <= 100 and abs(b - 180) <= 100:
                    found_gray = True
                    break
        if found_gray:
            break
    assert found_gray, f"No GRAY-colored pixels found at expected streak position (y≈{streak_y})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
