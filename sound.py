"""
sound.py — Synthesized sound effects for DeciWise
All sounds are generated mathematically via pygame — no audio files needed.
"""

import threading
import math
import array

_ENABLED = True   # set to False to mute everything

def _try_import_pygame():
    try:
        import pygame
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=1, buffer=512)
        pygame.mixer.init()
        return pygame
    except Exception:
        return None

_pg = _try_import_pygame()

# ── Waveform generators ───────────────────────────────────────────────────────

def _sine_wave(freq, duration_ms, volume=0.5, sample_rate=44100):
    """Return a pygame Sound of a pure sine wave."""
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = array.array("h", [0] * n_samples)
    peak = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        buf[i] = int(peak * math.sin(2 * math.pi * freq * t))
    sound = _pg.mixer.Sound(buffer=buf)
    return sound


def _multi_tone(freqs_durations, volume=0.5, sample_rate=44100):
    """
    Return a pygame Sound made of sequential tones.
    freqs_durations: list of (freq_hz, duration_ms)
    """
    all_samples = array.array("h")
    peak = int(32767 * volume)
    for freq, dur_ms in freqs_durations:
        n = int(sample_rate * dur_ms / 1000)
        for i in range(n):
            t = i / sample_rate
            if freq == 0:
                all_samples.append(0)
            else:
                # Apply tiny fade-in/out (5 ms) to avoid clicks
                fade = min(1.0, i / (sample_rate * 0.005),
                           (n - i) / (sample_rate * 0.005))
                all_samples.append(int(peak * fade * math.sin(
                    2 * math.pi * freq * t)))
    return _pg.mixer.Sound(buffer=all_samples)


def _noise_burst(duration_ms, volume=0.3, sample_rate=44100):
    """Short white-noise burst (used for 'wrong' answer)."""
    import random
    n = int(sample_rate * duration_ms / 1000)
    peak = int(32767 * volume)
    buf = array.array("h")
    for i in range(n):
        fade = min(1.0, i / (sample_rate * 0.003),
                   (n - i) / (sample_rate * 0.003))
        buf.append(int(peak * fade * (random.random() * 2 - 1)))
    return _pg.mixer.Sound(buffer=buf)


# ── Pre-build all sounds at import time ──────────────────────────────────────
_sounds = {}

def _build_sounds():
    if _pg is None:
        return
    try:
        # Click — single short mid tone (button press)
        _sounds["click"] = _sine_wave(660, 55, volume=0.25)

        # Correct answer — bright ascending two-note ding
        _sounds["correct"] = _multi_tone([
            (523, 80),   # C5
            (659, 80),   # E5
            (784, 130),  # G5
        ], volume=0.45)

        # Wrong answer — descending buzz + noise
        _sounds["wrong"] = _multi_tone([
            (300, 80),
            (220, 120),
            (180, 100),
        ], volume=0.4)

        # Level complete / result screen — triumphant fanfare
        _sounds["complete"] = _multi_tone([
            (523, 100),  # C5
            (659, 100),  # E5
            (784, 100),  # G5
            (0,   40),
            (784, 80),
            (1047, 300), # C6
        ], volume=0.45)

        # Perfect score — extra celebratory run
        _sounds["perfect"] = _multi_tone([
            (523, 80), (587, 80), (659, 80), (698, 80),
            (784, 80), (880, 80), (988, 80), (1047, 300),
        ], volume=0.45)

        # ── WIN sound — bright victory fanfare (lesson passed ≥ 60%) ──
        # Rising chord + triumphant finish
        _sounds["win"] = _multi_tone([
            (392, 80),   # G4
            (523, 80),   # C5
            (659, 80),   # E5
            (784, 80),   # G5
            (0,   30),
            (659, 60),   # E5
            (784, 60),   # G5
            (1047, 120), # C6
            (0,   40),
            (1047, 80),  # C6 echo
            (1319, 400), # E6 — held finish
        ], volume=0.50)

        # ── PERFECT WIN — full celebratory cascade (100%) ──
        _sounds["win_perfect"] = _multi_tone([
            (523, 60), (587, 60), (659, 60), (698, 60),
            (784, 60), (880, 60), (988, 60),
            (0,   25),
            (1047, 80), (1175, 80), (1319, 80),
            (0,   30),
            (1047, 60), (1175, 60),
            (1319, 500),  # E6 long hold
        ], volume=0.50)

        # ── FAIL sound — descending sad tune (lesson failed < 60%) ──
        # Slow descending minor-ish sequence + low thud
        _sounds["fail"] = _multi_tone([
            (494, 150),  # B4
            (440, 150),  # A4
            (392, 150),  # G4
            (349, 150),  # F4
            (0,   40),
            (294, 120),  # D4
            (0,   30),
            (247, 500),  # B3 — long sad hold
        ], volume=0.45)

        # ── GAME OVER — deeper, more dramatic fail ──
        _sounds["gameover"] = _multi_tone([
            (330, 180),  # E4
            (294, 180),  # D4
            (262, 180),  # C4
            (0,   50),
            (220, 140),  # A3
            (0,   40),
            (185, 140),  # F#3
            (0,   40),
            (165, 600),  # E3 — deep long hold
        ], volume=0.48)

        # Start game / begin quiz — upbeat two-note flourish
        _sounds["start"] = _multi_tone([
            (440, 90),
            (660, 150),
        ], volume=0.35)

        # Story typewriter tick — very quiet, short click
        _sounds["tick"] = _sine_wave(1200, 18, volume=0.06)

        # Level unlock — shimmering ascending arpeggio
        _sounds["unlock"] = _multi_tone([
            (392, 70),  # G4
            (523, 70),  # C5
            (659, 70),  # E5
            (784, 140), # G5
        ], volume=0.35)

        # Back / navigate — soft low click
        _sounds["back"] = _multi_tone([
            (440, 60),
            (330, 80),
        ], volume=0.25)

    except Exception as e:
        print(f"[Sound] Build error: {e}")

_build_sounds()


# ── Public API ────────────────────────────────────────────────────────────────

def play(name: str):
    """Play a named sound effect in a background thread (non-blocking)."""
    if not _ENABLED or _pg is None:
        return
    snd = _sounds.get(name)
    if snd is None:
        return
    threading.Thread(target=snd.play, daemon=True).start()


def mute(state: bool = True):
    """Globally mute (True) or unmute (False) all sounds."""
    global _ENABLED
    _ENABLED = not state
