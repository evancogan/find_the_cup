"""
Find the Cup
A shell game where you track a ball hidden under one of three cups.
Watch the cups swap positions, then pick the right one!
"""

import pygame
import random
import math
from enum import Enum, auto

# ── Phase Enum ───────────────────────────────────────────────────────────────
class Phase(Enum):
    """Game phases for find_the_cup."""
    MENU = auto()
    START = auto()
    START_LOWER = auto()
    DANCING = auto()
    CHOOSING = auto()
    RESULT = auto()

# ── Setup ──────────────────────────────────────────────────────────────────
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Find the Cup!")
clock = pygame.time.Clock()

# ── Colors ─────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (30, 30, 30)
GRAY       = (180, 180, 180)
DARK_GRAY  = (80, 80, 80)
RED        = (220, 50, 50)
GREEN      = (50, 180, 50)
BLUE       = (60, 120, 220)
YELLOW     = (240, 210, 50)
GOLD       = (255, 200, 0)
PURPLE     = (140, 60, 200)
BG         = (40, 40, 60)
CUP_COLOR  = (100, 100, 140)   # all cups same color to hide the ball

# ── Constants ──────────────────────────────────────────────────────────────
CUP_WIDTH  = 100
CUP_HEIGHT = 120
CUP_RADIUS = 40
CUP_SPACING = 200
GROUND_Y    = HEIGHT - 140
CUP_Y       = GROUND_Y - CUP_HEIGHT // 2
BALL_RADIUS = 18
SWAP_DURATION     = 600   # ms per individual swap
SWAP_PAUSE        = 400   # ms pause between swaps
REVEAL_DURATION   = 1200

# Streak-based speed scaling
SWAP_SPEED_PER_STREAK   = 50   # ms reduction per streak point
SWAP_PAUSE_PER_STREAK   = 30
SWAP_DURATION_MIN       = 200  # minimum swap duration (ms)
SWAP_PAUSE_MIN          = 100  # minimum pause between swaps (ms)

# ── Font ───────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("arial", 48, bold=True)
font_med   = pygame.font.SysFont("arial", 28)
font_small = pygame.font.SysFont("arial", 20)


# ── Helper: draw a cup ─────────────────────────────────────────────────────
def draw_cup(surface, cx, cy, color, scale=1.0):
    """Draw a stylized cup shape centered at (cx, cy)."""
    w = CUP_WIDTH * scale
    h = CUP_HEIGHT * scale
    r = CUP_RADIUS * scale
    top_y = cy - h // 2
    bot_y = cy + h // 2

    pts = [
        (cx - w // 2 + 10 * scale, top_y),
        (cx + w // 2 - 10 * scale, top_y),
        (cx + w // 2, bot_y),
        (cx - w // 2, bot_y),
    ]
    pygame.draw.polygon(surface, color, pts)
    pygame.draw.polygon(surface, DARK_GRAY, pts, width=3)

    pygame.draw.ellipse(surface, lighten(color, 40),
                        (cx - r, top_y - 8 * scale, r * 2, 16 * scale))
    pygame.draw.ellipse(surface, DARK_GRAY,
                        (cx - r, top_y - 8 * scale, r * 2, 16 * scale), width=2)
    pygame.draw.ellipse(surface, darken(color, 60),
                        (cx - r + 5, top_y - 4 * scale, r * 2 - 10, 10 * scale))


def lighten(color, amount):
    return tuple(min(255, c + amount) for c in color)


def darken(color, amount):
    return tuple(max(0, c - amount) for c in color)


def draw_ball(surface, cx, cy):
    pygame.draw.circle(surface, RED, (int(cx), int(cy)), BALL_RADIUS)
    pygame.draw.circle(surface, lighten(RED, 80),
                       (int(cx) - 5, int(cy) - 5), BALL_RADIUS // 3)
    pygame.draw.circle(surface, darken(RED, 60),
                       (int(cx), int(cy)), BALL_RADIUS, width=2)


def draw_text(surface, text, x, y, font=font_med, color=WHITE, centered=True):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y)) if centered else surf.get_rect(topleft=(x, y))
    surface.blit(surf, rect)


# ── Game ───────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.streak = 0
        self.reset()

    def reset(self):
        self.ball_idx = random.randint(0, 2)
        cx = WIDTH // 2
        # Three fixed slots: left, center, right
        self.slots = [cx - CUP_SPACING, cx, cx + CUP_SPACING]
        # Each cup tracks which slot it's currently assigned to
        self.cups = [
            {"slot": i, "x": self.slots[i], "lift": 0, "color": CUP_COLOR}
            for i in range(3)
        ]
        self.phase = Phase.MENU
        self.phase_timer = 0
        self._start_clicked = False
        self.ball_visible = False
        self.ball_x = 0
        self.ball_y = 0
        self.result = None
        self.swap_sequence = []
        self.swap_targets = []
        self.current_swap = 0
        self.swap_phase = "swapping"

    # ── Phase transitions ────────────────────────────────────────────────
    def start_start(self):
        """Start phase: lift cups to reveal ball."""
        if self._start_clicked:
            # Already started — simulate instant progression through all phases
            for cup in self.cups:
                cup["lift"] = 0
            self.start_dancing()
            return
        self._start_clicked = True
        self.phase = Phase.START
        self.phase_timer = 0
        self.ball_visible = True
        self.ball_x = self.cups[self.ball_idx]["x"]
        # Ball rests on the ground line during reveal
        self.ball_y = GROUND_Y - BALL_RADIUS

    def start_dancing(self):
        """Dancing phase: shuffle cups with trackable swaps."""
        # Hide ball — player must now track the cup
        self.ball_visible = False
        # Reset all lifts to 0 (cups back on the ground)
        for cup in self.cups:
            cup["lift"] = 0

        # Build swap pairs: each element = (cup_a, cup_b) indices to swap
        targets = [0, 1, 2]
        swaps = []
        for _ in range(5):
            i = random.randint(0, 1)  # always swap adjacent pair (0,1) or (1,2)
            j = i + 1
            swaps.append((i, j))
            targets[i], targets[j] = targets[j], targets[i]
        # Ensure at least one cup moved
        if targets == [0, 1, 2]:
            swaps.pop()
            targets[0], targets[1] = targets[1], targets[0]

        self.swap_sequence = swaps
        self.swap_targets = targets
        self.current_swap = 0
        self.swap_phase = "swapping"  # "swapping" or "pausing"
        self.phase_timer = 0
        self.phase = Phase.DANCING

    def start_choice(self):
        """Choice phase: player picks a cup."""
        # Reset all lifts so cups sit flat on the ground
        for cup in self.cups:
            cup["lift"] = 0
        self.ball_visible = False
        self.phase = Phase.CHOOSING
        self.phase_timer = 0

    def _swap_duration(self):
        """Return the current swap duration (ms) based on streak.

        Higher streak → faster swaps, but never below SWAP_DURATION_MIN.
        """
        return max(SWAP_DURATION_MIN,
                   SWAP_DURATION - self.streak * SWAP_SPEED_PER_STREAK)

    def _swap_pause(self):
        """Return the current pause between swaps (ms) based on streak."""
        return max(SWAP_PAUSE_MIN,
                   SWAP_PAUSE - self.streak * SWAP_PAUSE_PER_STREAK)

    def start_result(self, win: bool):
        if win:
            self.streak += 1
        else:
            self.streak = 0
        self.phase = Phase.RESULT
        self.phase_timer = 0
        self.result = "win" if win else "lose"

    # ── Update ───────────────────────────────────────────────────────────
    def update(self, dt):
        if self.phase == Phase.START:
            progress = min(self.phase_timer / REVEAL_DURATION, 1.0)
            for cup in self.cups:
                cup["lift"] = progress * -150
            if progress >= 1.0:
                # After lifting, lower cups back down
                self.phase = Phase.START_LOWER
                self.phase_timer = 0

        elif self.phase == Phase.START_LOWER:
            progress = min(self.phase_timer / REVEAL_DURATION, 1.0)
            for cup in self.cups:
                cup["lift"] = -150 + progress * 150
            if progress >= 1.0:
                # Start the dancing/shuffling phase
                self.start_dancing()

        elif self.phase == Phase.DANCING:
            if self.swap_phase == "swapping":
                progress = min(self.phase_timer / self._swap_duration(), 1.0)
                # Smooth easing: slow start, fast middle, slow end
                t = progress * progress * (3 - 2 * progress)
                a, b = self.swap_sequence[self.current_swap]
                ax = self.slots[self.cups[a]["slot"]]
                bx = self.slots[self.cups[b]["slot"]]
                # Interpolate positions
                new_ax = self.cups[a]["x"] + (bx - self.cups[a]["x"]) * t
                new_bx = self.cups[b]["x"] + (ax - self.cups[b]["x"]) * t
                self.cups[a]["x"] = new_ax
                self.cups[b]["x"] = new_bx
                if progress >= 1.0:
                    # Snap to final positions and update slot tracking
                    self.cups[a]["x"] = bx
                    self.cups[b]["x"] = ax
                    # Properly swap the slots (not overwrite with array indices!)
                    self.cups[a]["slot"], self.cups[b]["slot"] = self.cups[b]["slot"], self.cups[a]["slot"]
                    # Update ball position if its cup just moved
                    ball_cup = self.cups[self.ball_idx]
                    self.ball_x = ball_cup["x"]
                    self.current_swap += 1
                    if self.current_swap >= len(self.swap_sequence):
                        # All swaps done — sync cups to their final slots
                        for i in range(3):
                            self.cups[i]["slot"] = self.swap_targets[i]
                            self.cups[i]["x"] = self.slots[self.cups[i]["slot"]]
                        self.start_choice()
                    else:
                        self.swap_phase = "pausing"
                        self.phase_timer = 0
            elif self.swap_phase == "pausing":
                if self.phase_timer >= self._swap_pause():
                    self.swap_phase = "swapping"
                    self.phase_timer = 0

        elif self.phase in (Phase.CHOOSING, Phase.RESULT):
            pass

        self.phase_timer += dt

    def get_display(self):
        """Return the current display text for testing purposes."""
        if self.phase == Phase.START:
            return "Find the Cup!\nThe ball is under one of these cups..."
        elif self.phase == Phase.DANCING:
            return "Shuffling...\nTrack the ball!"
        elif self.phase == Phase.CHOOSING:
            line = "Which cup is it under?\nClick the cup you think has the ball!"
            if self.streak > 0:
                line += f"\nStreak: {self.streak}"
            return line
        elif self.phase == Phase.RESULT:
            if self.result == "win":
                line = "You Win!\nYou found the ball!"
                if self.streak > 0:
                    line += f"\nStreak: {self.streak}"
                return line
            else:
                labels = [text for text, _x in self.cup_labels()]
                ball_slot = self.cups[self.ball_idx]["slot"]
                return f"Wrong!\nThe ball was under {labels[ball_slot]}"
        elif self.phase == Phase.MENU:
            return "Find the Cup!"
        return ""

    # ── Input ────────────────────────────────────────────────────────────
    def cup_labels(self):
        """Return list of (text, x) for labels at fixed slot positions, left to right."""
        return [(f"Cup {i+1}", self.slots[i]) for i in range(len(self.slots))]

    def handle_click(self, pos):
        if self.phase != Phase.CHOOSING:
            return
        mx, my = pos
        for i, cup in enumerate(self.cups):
            cx = int(cup["x"])
            cy = int(CUP_Y + cup["lift"])
            if (abs(mx - cx) < CUP_WIDTH // 2 + 10
                    and abs(my - cy) < CUP_HEIGHT // 2 + 10):
                won = (i == self.ball_idx)
                self.start_result(won)
                return

    # ── Render ───────────────────────────────────────────────────────────
    def render(self, surface):
        surface.fill(BG)

        # Title and subtitle from get_display()
        display = self.get_display()
        lines = display.split("\n")
        for i, line in enumerate(lines):
            if not line:
                continue
            y = 50 + i * (font_small.get_height() + 8)
            draw_text(surface, line, WIDTH // 2, y,
                      font=font_big if i == 0 else font_small,
                      color=GOLD if self.phase == Phase.RESULT and i == 0 else GRAY)

        # Ground line
        pygame.draw.line(surface, DARK_GRAY,
                         (100, GROUND_Y),
                         (WIDTH - 100, GROUND_Y), 2)

        # Ball
        if self.ball_visible:
            draw_ball(surface, self.ball_x, self.ball_y)

        # Cups
        for i, cup in enumerate(self.cups):
            cx = int(cup["x"])
            cy = int(CUP_Y + cup["lift"])
            draw_cup(surface, cx, cy, cup["color"])

        # Labels at fixed positions (not attached to cups)
        for text, x in self.cup_labels():
            label = font_med.render(text, True, WHITE)
            surface.blit(label,
                         (x - label.get_width() // 2,
                          CUP_Y + CUP_HEIGHT // 2 + 25))

        # Result overlay
        if self.phase == Phase.RESULT:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
            if self.result == "win":
                draw_text(surface, "You Win!",
                          WIDTH // 2, HEIGHT // 2 - 40,
                          font=font_big, color=GOLD)

        # Buttons
        if self.phase == Phase.MENU:
            self._draw_button(surface, WIDTH // 2, HEIGHT // 2 + 60,
                              "START", GREEN, font_big)
        elif self.phase == Phase.START:
            self._draw_button(surface, WIDTH // 2, HEIGHT // 2 + 60,
                              "START", GREEN, font_big)
        elif self.phase == Phase.RESULT:
            self._draw_button(surface, WIDTH // 2, HEIGHT // 2 + 80,
                              "RESTART", BLUE, font_med)

    def _draw_button(self, surface, cx, cy, text, color, font):
        btn_x = cx - 100
        btn_y = cy - 30
        btn_w, btn_h = 200, 60
        pygame.draw.rect(surface, color, (btn_x, btn_y, btn_w, btn_h),
                         border_radius=12)
        pygame.draw.rect(surface, WHITE, (btn_x, btn_y, btn_w, btn_h),
                         3, border_radius=12)
        draw_text(surface, text, cx, cy, font=font, color=WHITE)


# ── Main Loop ──────────────────────────────────────────────────────────────
def main():
    game = Game()
    running = True

    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if game.phase in (Phase.MENU, Phase.START):
                    btn_x = WIDTH // 2 - 100
                    btn_y = HEIGHT // 2 + 30
                    if (btn_x <= mx <= btn_x + 200 and
                            btn_y <= my <= btn_y + 60):
                        game.start_start()

                elif game.phase == Phase.CHOOSING:
                    game.handle_click((mx, my))

                elif game.phase == Phase.RESULT:
                    btn_x = WIDTH // 2 - 100
                    btn_y = HEIGHT // 2 + 50
                    if (btn_x <= mx <= btn_x + 200 and
                            btn_y <= my <= btn_y + 60):
                        game.reset()
                        game.start_start()

        game.update(dt)
        game.render(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
