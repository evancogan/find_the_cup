"""
sfx.py - build retro sound effects from pure code in pygame (no audio files).

Every sound is a recipe of four ingredients:
  1. waveform  - the raw tone (sine, triangle, square, sawtooth, noise)
  2. pitch     - where the tone starts and ends, sliding or stepping
  3. envelope  - volume shape: instant start, then a fade out
  4. filter    - (noise only) a tone knob that muffles over time

Run this file directly to try it: press keys 1-6 to hear the presets.
Requires: pip install pygame numpy
"""

import numpy as np
import pygame

PRESETS = {
    "coin":    dict(wave="square",   start_hz=988,  end_hz=1319, duration=0.35, step=True),
    "jump":    dict(wave="square",   start_hz=220,  end_hz=660,  duration=0.25),
    "laser":   dict(wave="sawtooth", start_hz=1600, end_hz=120,  duration=0.30),
    "hit":     dict(wave="square",   start_hz=300,  end_hz=60,   duration=0.12),
    "powerup": dict(wave="triangle", start_hz=300,  end_hz=1800, duration=0.90),
    "boom":    dict(wave="noise",    start_hz=1800, end_hz=60,   duration=1.20),
    "whoosh":  dict(wave="noise",    start_hz=1200, end_hz=100,  duration=0.20),
}


def make_sfx(wave="square", start_hz=440, end_hz=440, duration=0.3,
             step=False, volume=0.3):
    """Build a pygame Sound from a recipe. Call AFTER pygame.mixer is initialized."""
    sample_rate, _, channels = pygame.mixer.get_init()
    n = int(sample_rate * duration)
    t = np.linspace(0, 1, n, endpoint=False)   # 0 -> 1 across the sound's lifetime

    # --- Ingredient 2: the pitch curve (how high the tone is at each moment) ---
    if step:
        freq = np.where(t < 0.25, start_hz, end_hz)          # jump between two notes
    else:
        freq = start_hz * (end_hz / start_hz) ** t           # smooth slide

    # --- Ingredient 1 (+4): the raw waveform ---
    if wave == "noise":
        samples = _filtered_noise(n, freq * 4, sample_rate)
    else:
        # "phase" = how many cycles the wave has completed so far. Tracking it
        # like a spinning wheel lets the pitch change smoothly, without clicks.
        phase = np.cumsum(freq / sample_rate)
        frac = phase % 1.0                                   # position within the current cycle
        if wave == "sine":
            samples = np.sin(2 * np.pi * phase)
        elif wave == "triangle":
            samples = 4 * np.abs(frac - 0.5) - 1
        elif wave == "square":
            samples = np.where(frac < 0.5, 1.0, -1.0)
        elif wave == "sawtooth":
            samples = 2 * frac - 1
        else:
            raise ValueError(f"unknown wave: {wave}")

    # --- Ingredient 3: the volume envelope (quick fade in, then decay) ---
    attack = min(0.01 / duration, 0.5)
    envelope = np.where(t < attack, t / attack,
                        np.exp(-4 * (t - attack) / (1 - attack)))
    samples = samples * envelope * volume

    # Convert to 16-bit numbers, the format pygame's mixer plays
    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    if channels == 2:
        pcm = np.column_stack((pcm, pcm))                    # same sound in both ears
    return pygame.sndarray.make_sound(np.ascontiguousarray(pcm))


def _filtered_noise(n, cutoff_hz, sample_rate):
    """Random static passed through a muffling filter whose cutoff sweeps down."""
    noise = np.random.uniform(-1, 1, n)
    amount = 1 - np.exp(-2 * np.pi * np.minimum(cutoff_hz, sample_rate / 2) / sample_rate)
    out = np.empty(n)
    y = 0.0
    for i in range(n):                  # each sample leans toward the noise by `amount`
        y += amount[i] * (noise[i] - y)
        out[i] = y
    return out / (np.max(np.abs(out)) or 1)   # restore loudness lost to filtering


if __name__ == "__main__":
    pygame.mixer.pre_init(44100, -16, 2, 512)   # small buffer = low delay on playback
    pygame.init()
    screen = pygame.display.set_mode((420, 200))
    pygame.display.set_caption("sfx demo - press 1-6")
    font = pygame.font.SysFont(None, 28)

    # Build every sound once at startup, then play instantly whenever needed
    names = list(PRESETS)
    sounds = {name: make_sfx(**PRESETS[name]) for name in names}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_6:
                sounds[names[event.key - pygame.K_1]].play()

        screen.fill((24, 24, 28))
        for i, name in enumerate(names):
            screen.blit(font.render(f"{i + 1}  {name}", True, (220, 220, 220)), (30, 20 + i * 28))
        pygame.display.flip()

    pygame.quit()
