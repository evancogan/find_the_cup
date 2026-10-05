# Test cheat sheet

## Every test starts like this

```python
def test_what_should_be_true():
    """One sentence: what the game should do."""
    import find_the_cup
    game = find_the_cup.Game()      # a fresh game, sitting in MENU, nothing played yet
```

## Moving the game forward

| I want to... | Line |
|---|---|
| Press START | `game.start_start()` |
| Let time pass (ms) | `game.update(100)` |
| Skip ahead to a phase | `_advance_to(game, find_the_cup.Phase.DANCING)` |
| Play up to choosing | `_full_game(game)` |
| Win a round | `_win_on_purpose(game)` |
| Lose a round | `_lose_on_purpose(game)` |
| Start the next round (RESTART) | `_next_round(game)` |
| Click somewhere | `game.handle_click((x, y))` |

Phases: `MENU`, `START`, `START_LOWER`, `DANCING`, `CHOOSING`, `RESULT`, all written as `find_the_cup.Phase.NAME`.

## Looking at the game

| What | Line |
|---|---|
| Current phase | `game.phase` |
| The three cups | `game.cups` (a list; each cup is a dict) |
| One cup's position | `cup["x"]`, `cup["slot"]`, `cup["lift"]` |
| Which cup has the ball | `game.ball_idx` → `game.cups[game.ball_idx]` |
| The ball | `game.ball_x`, `game.ball_y`, `game.ball_visible` |
| Win or lose | `game.result` (`"win"` or `"lose"`) |
| Text on screen | `game.get_display()` |
| Position labels | `game.cup_labels()` → `[("Cup 1", x), ...]` |
| The three table positions | `game.slots` (x of left, middle, right) |
| Constants | `find_the_cup.GROUND_Y`, `find_the_cup.CUP_Y`, `find_the_cup.CUP_HEIGHT`, ... |

## Checking things

```python
assert game.streak == 1                                  # exact value
assert game.phase == find_the_cup.Phase.CHOOSING         # guard: am I where I think I am?
assert "Cup 3" in game.get_display()                     # text contains
assert "Cup B" not in game.get_display()                 # text does NOT contain
assert abs(game.ball_x - cup["x"]) < 1                   # close enough (for decimals)
assert a < b                                             # smaller (e.g. faster = shorter duration)
assert game.streak == 1, f"Expected 1, got {game.streak}"  # custom failure message

for cup in game.cups:                                    # check every cup
    assert cup["lift"] == 0
```

## Bottom of a thing = centre + half its height

```python
ball_bottom = game.ball_y + find_the_cup.BALL_RADIUS
cup_bottom = find_the_cup.CUP_Y + cup["lift"] + find_the_cup.CUP_HEIGHT // 2
```

## Checking what's drawn (pixels)

```python
import pygame
screen = pygame.Surface((find_the_cup.WIDTH, find_the_cup.HEIGHT))
game.render(screen)
assert screen.get_at((x, y)) == find_the_cup.DARK_GRAY    # (x, y) = across, then down
```

## A test I haven't written yet

```python
def test_something():
    """What it will check."""
    pytest.skip("not written yet")
```

## Running

```bash
python -m pytest tests -v
```
```bash
python -m pytest tests -k streak -v
```
(`-k streak` runs only tests with "streak" in the name)

## Before trusting a test, ask

- **Would it fail if I broke the feature?** If not, it's decoration.
- **Is the starting value different from the expected result?** (A "reset to 0" test must start above 0.)
- **Does every name I used actually exist?** (Ctrl+click it.)
- **Did it fail for the right reason?** A red from a typo isn't the red you want.
- **Did I save?** (A dot ● on the tab means unsaved.)
