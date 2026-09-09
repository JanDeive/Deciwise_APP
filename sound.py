"""
sound.py — 8-bit chiptune sound effects for DeciWise (Retro Edition)
All sounds are generated mathematically via pygame — no audio files needed.
Waveforms use square waves and arpeggio patterns to mimic classic NES/Game Boy audio.
"""

import threading
import math
import array
import random as _random

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

# ── Chiptune waveform generators ──────────────────────────────────────────────

def _square_wave(freq, duration_ms, volume=0.4, duty=0.5, sample_rate=44100):
    """
    8-bit style square wave — the backbone of NES/Game Boy audio.
    duty: pulse width 0.0–1.0 (0.5 = perfect square, 0.25 = NES pulse)
    """
    n = int(sample_rate * duration_ms / 1000)
    peak = int(32767 * volume)
    buf = array.array("h")
    period = sample_rate / freq if freq > 0 else 0
    for i in range(n):
        # Hard clip fade at start/end to reduce pops
        fade = min(1.0, i / max(1, sample_rate * 0.003),
                   (n - i) / max(1, sample_rate * 0.003))
        if freq == 0:
            buf.append(0)
        else:
            phase = (i % period) / period
            val = peak if phase < duty else -peak
            buf.append(int(val * fade))
    return _pg.mixer.Sound(buffer=buf)


def _chip_seq(notes, volume=0.4, duty=0.5, sample_rate=44100):
    """
    Sequence of (freq_hz, duration_ms) square-wave notes.
    freq=0 means silence (rest).
    """
    all_samples = array.array("h")
    peak = int(32767 * volume)
    for freq, dur_ms in notes:
        n = int(sample_rate * dur_ms / 1000)
        period = (sample_rate / freq) if freq > 0 else 0
        for i in range(n):
            fade = min(1.0, i / max(1, sample_rate * 0.003),
                       (n - i) / max(1, sample_rate * 0.003))
            if freq == 0:
                all_samples.append(0)
            else:
                phase = (i % period) / period
                val = peak if phase < duty else -peak
                all_samples.append(int(val * fade))
    return _pg.mixer.Sound(buffer=all_samples)


def _noise_burst(duration_ms, volume=0.25, sample_rate=44100):
    """
    Pseudo-random noise burst — classic NES noise channel.
    Used for wrong-answer buzz and game-over effects.
    """
    n = int(sample_rate * duration_ms / 1000)
    peak = int(32767 * volume)
    buf = array.array("h")
    lfsr = 0x7FFF   # 15-bit LFSR seed (NES noise register style)
    for i in range(n):
        fade = min(1.0, i / max(1, sample_rate * 0.003),
                   (n - i) / max(1, sample_rate * 0.003))
        # Shift LFSR
        bit = ((lfsr >> 0) ^ (lfsr >> 1)) & 1
        lfsr = (lfsr >> 1) | (bit << 14)
        val = peak if (lfsr & 1) else -peak
        buf.append(int(val * fade))
    return _pg.mixer.Sound(buffer=buf)


# ── Pre-build all sounds at import time ──────────────────────────────────────
_sounds = {}

def _build_sounds():
    if _pg is None:
        return
    try:
        # ── CLICK — short NES-style blip (25% duty pulse, high pitch) ──
        _sounds["click"] = _square_wave(880, 40, volume=0.20, duty=0.25)

        # ── CORRECT — classic 3-note ascending arpeggio (NES coin/pickup) ──
        _sounds["correct"] = _chip_seq([
            (523, 60),   # C5
            (659, 60),   # E5
            (784, 100),  # G5
            (1047, 140), # C6 — held finish
        ], volume=0.38, duty=0.5)

        # ── WRONG — descending buzzy sequence + noise hit ──
        _sounds["wrong"] = _chip_seq([
            (220, 70),
            (185, 70),
            (147, 100),
            (0,   20),
            (110, 140),  # low thud
        ], volume=0.38, duty=0.25)

        # ── COMPLETE — short triumphant fanfare ──
        _sounds["complete"] = _chip_seq([
            (523, 80), (659, 80), (784, 80),
            (0,   30),
            (784, 60), (1047, 250),
        ], volume=0.38, duty=0.5)

        # ── PERFECT — full ascending scale run ──
        _sounds["perfect"] = _chip_seq([
            (523, 55), (587, 55), (659, 55), (698, 55),
            (784, 55), (880, 55), (988, 55), (1047, 250),
        ], volume=0.38, duty=0.5)

        # ── WIN — victory fanfare (lesson passed ≥ 60%) ──
        # Classic 8-bit win jingle feel
        _sounds["win"] = _chip_seq([
            (392, 70),   # G4
            (523, 70),   # C5
            (659, 70),   # E5
            (784, 70),   # G5
            (0,   25),
            (659, 55),
            (784, 55),
            (1047, 100), # C6
            (0,   35),
            (1047, 70),
            (1319, 380), # E6 — held
        ], volume=0.42, duty=0.5)

        # ── PERFECT WIN — full celebratory cascade (100%) ──
        _sounds["win_perfect"] = _chip_seq([
            (523, 50), (587, 50), (659, 50), (698, 50),
            (784, 50), (880, 50), (988, 50),
            (0,   20),
            (1047, 65), (1175, 65), (1319, 65),
            (0,   25),
            (1047, 50), (1175, 50),
            (1319, 420),  # long held finish
        ], volume=0.42, duty=0.5)

        # ── FAIL — descending minor melody (lesson failed < 60%) ──
        _sounds["fail"] = _chip_seq([
            (494, 130),  # B4
            (440, 130),  # A4
            (392, 130),  # G4
            (349, 130),  # F4
            (0,   35),
            (294, 110),  # D4
            (0,   25),
            (247, 460),  # B3 — sad low hold
        ], volume=0.40, duty=0.25)

        # ── GAME OVER — dramatic NES-style descending + noise hits ──
        _sounds["gameover"] = _chip_seq([
            (330, 160),  # E4
            (294, 160),  # D4
            (262, 160),  # C4
            (0,   40),
            (220, 120),  # A3
            (0,   30),
            (185, 120),  # F#3
            (0,   30),
            (165, 500),  # E3 — deep long hold
        ], volume=0.42, duty=0.25)

        # ── START — upbeat two-note power-up blip ──
        _sounds["start"] = _chip_seq([
            (440, 70),
            (0,   15),
            (660, 55),
            (0,   15),
            (880, 130),
        ], volume=0.32, duty=0.5)

        # ── TICK — tiny typewriter click (very quiet high blip) ──
        _sounds["tick"] = _square_wave(1400, 14, volume=0.05, duty=0.25)

        # ── UNLOCK — shimmering ascending arpeggio (level unlock jingle) ──
        _sounds["unlock"] = _chip_seq([
            (392, 60),   # G4
            (523, 60),   # C5
            (659, 60),   # E5
            (784, 60),   # G5
            (1047, 160), # C6
        ], volume=0.32, duty=0.5)

        # ── BACK — short two-note step-down ──
        _sounds["back"] = _chip_seq([
            (440, 50),
            (330, 70),
        ], volume=0.22, duty=0.25)

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
