"""
DeciWise — Family Planning Quiz Game  (Capstone Edition)
Built with Python Tkinter. No external dependencies beyond pygame for sound.
"""

import tkinter as tk
from tkinter import font as tkfont
import json, os, time
import sound as SFX

# ── Window ────────────────────────────────────────────────────────────────────
WINDOW_W, WINDOW_H = 430, 800

# ── Retro font helper ─────────────────────────────────────────────────────────
# Falls back gracefully: Courier New → Lucida Console → TkFixedFont
def _retro(size, weight="normal"):
    for fam in ("Courier New", "Lucida Console", "Courier"):
        try:
            f = tkfont.Font(family=fam, size=size, weight=weight)
            if f.actual()["family"].lower().startswith(fam.split()[0].lower()):
                return f
        except Exception:
            pass
    return tkfont.Font(family="TkFixedFont", size=size, weight=weight)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
QUESTIONS_DB = os.path.join(DATA_DIR, "questions.json")
PROGRESS_DB  = os.path.join(DATA_DIR, "progress.json")

# ── Palette  (Retro CRT / Arcade theme) ──────────────────────────────────────
C = {
    "bg":        "#1a1f1a",   # soft dark green-grey (not pitch black)
    "card":      "#242e24",   # medium dark card surface
    "card2":     "#1e2a36",   # soft blue-tinted card
    "accent":    "#39ff7a",   # softer neon green (easier on eyes)
    "accent2":   "#2ecc55",   # mid green
    "accent3":   "#1a4d2e",   # muted dark green border
    "easy":      "#39ff7a",   # easy green
    "medium":    "#ffbb33",   # warm amber
    "hard":      "#ff6b6b",   # soft neon red
    "expert":    "#d966ff",   # soft neon purple
    "white":     "#e8f5e8",   # soft off-white (easy to read)
    "grey":      "#7a9e7a",   # readable muted green
    "correct":   "#39ff7a",
    "wrong":     "#ff6b6b",
    "gold":      "#ffd700",   # bright gold
    "silver":    "#b8ccb8",
    "bronze":    "#cd8c3a",
    "locked":    "#2a3a2a",   # soft locked state
    "dark":      "#1a1f1a",
    "timer_ok":  "#39ff7a",
    "timer_warn":"#ffbb33",
    "timer_bad": "#ff6b6b",
    "xp":        "#33ddff",   # soft cyan
    "lives":     "#ff6b6b",
    "banner":    "#111811",   # dark but not void banner
    "glow":      "#1a4d2e",   # card glow tint
}

# ── Light mode palette ────────────────────────────────────────────────────────
_DARK_PALETTE = {k: v for k, v in C.items()}   # snapshot of dark values

_LIGHT_PALETTE = {
    "bg":        "#dce8dc",   # soft grey-green background
    "card":      "#c8d8c8",   # muted grey-green card
    "card2":     "#c4d0de",   # soft grey-blue card
    "accent":    "#1a6b35",   # deep forest green
    "accent2":   "#2a9a50",   # mid green
    "accent3":   "#8ab89a",   # muted green border
    "easy":      "#1a6b35",
    "medium":    "#b87700",   # muted amber
    "hard":      "#a83228",   # muted red
    "expert":    "#6a2e8a",   # muted purple
    "white":     "#1a2a1a",   # near-black text
    "grey":      "#3a5a3a",   # readable dark green text
    "correct":   "#1a6b35",
    "wrong":     "#a83228",
    "gold":      "#8a6800",   # muted gold
    "silver":    "#4a604a",
    "bronze":    "#6a3810",
    "locked":    "#b8ccb8",   # muted locked
    "dark":      "#dce8dc",
    "timer_ok":  "#1a6b35",
    "timer_warn":"#b87700",
    "timer_bad": "#a83228",
    "xp":        "#1a4a8a",   # muted blue XP
    "lives":     "#a83228",
    "banner":    "#b8ccb8",   # grey-green banner
    "glow":      "#8ab89a",
}

# ── Theme toggle ──────────────────────────────────────────────────────────────
_IS_LIGHT = False

def _apply_theme(light: bool):
    """Swap all C values in-place so every widget rebuild picks up new colors."""
    global _IS_LIGHT
    _IS_LIGHT = light
    src = _LIGHT_PALETTE if light else _DARK_PALETTE
    for k, v in src.items():
        C[k] = v

# Quiz mode is always standard questions
QUIZ_MODE_KEY = "questions"

# Timer seconds per difficulty
TIMER = {"Easy": 30, "Medium": 22, "Hard": 16,
         "Beginner": 30, "Intermediate": 22, "Difficult": 16,
         "Kahoot": 20}
XP_CORRECT   = 10
XP_BONUS_FAST = 5   # answered in first half of timer
XP_PERFECT   = 20   # bonus for 100% level

# Lives
MAX_LIVES = 3

STORY_ICONS = {
    "couple":       "💑",
    "health_center":"🏥",
    "seminar":      "📋",
    "classroom":    "🏫",
    "midwife":      "👩‍⚕️",
    "counselor":    "🧑‍💼",
    "condom":       "🛡️",
}

BADGES = {
    "first_step":   {"icon": "🌱", "name": "First Step",     "desc": "Complete Chapter 1 Beginner"},
    "beginner":     {"icon": "📗", "name": "Beginner",        "desc": "Complete Chapter 1 (all 3 tiers)"},
    "intermediate": {"icon": "📘", "name": "Intermediate",    "desc": "Complete Chapters 1–2"},
    "expert":       {"icon": "📕", "name": "Expert",          "desc": "Complete Chapter 3"},
    "perfect_run":  {"icon": "🏆", "name": "Perfect Run",     "desc": "Score 100% on any level"},
    "speedster":    {"icon": "⚡", "name": "Speedster",       "desc": "Answer 5 questions quickly"},
    "deciwise":     {"icon": "🎓", "name": "DeciWise Master", "desc": "Complete all chapters"},
}

ACT_MAP = {
    1: ("Chapter 1", "Family Planning",       "#2ecc71", [1, 2]),
    2: ("Chapter 2", "Contraceptives",         "#3498db", [3, 4]),
    3: ("Chapter 3", "Fertility Awareness",    "#9b59b6", [5, 6]),
}

# ── JSON helpers ──────────────────────────────────────────────────────────────
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ── Colour math ───────────────────────────────────────────────────────────────
def _darken(h, f=0.75):
    h = h.lstrip("#")
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(int(r*f),int(g*f),int(b*f))

def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    # Expand 3-digit hex shorthand to 6-digit
    for c in (a, b):
        pass
    def _expand(h):
        h = h.lstrip("#")
        if len(h) == 3:
            h = h[0]*2 + h[1]*2 + h[2]*2
        return h
    a, b = _expand(a), _expand(b)
    ar,ag,ab_ = int(a[0:2],16),int(a[2:4],16),int(a[4:6],16)
    br,bg_,bb = int(b[0:2],16),int(b[2:4],16),int(b[4:6],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(ar+(br-ar)*t), int(ag+(bg_-ag)*t), int(ab_+(bb-ab_)*t))

# ── Canvas helpers ────────────────────────────────────────────────────────────
def rr(cv, x1,y1,x2,y2, r=16, **kw):
    """Draw rounded rectangle on canvas."""
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
           x1,y2, x1,y2-r, x1,y1+r, x1,y1, x1+r,y1]
    return cv.create_polygon(pts, smooth=True, **kw)

def _grad(cv, x1, y1, x2, y2, col_top, col_bot, steps=20, **kw):
    """
    Fill a rectangle with a vertical gradient by drawing `steps` thin slices.
    Extra kwargs (e.g. tags=) are forwarded to each create_rectangle call.
    """
    h = y2 - y1
    for i in range(steps):
        t1 = i / steps
        t2 = (i + 1) / steps
        c  = _lerp(col_top, col_bot, (t1 + t2) / 2)
        ry1 = y1 + int(h * t1)
        ry2 = y1 + int(h * t2) + 1
        cv.create_rectangle(x1, ry1, x2, ry2, fill=c, outline="", **kw)

def _grad_rr(cv, x1, y1, x2, y2, col_top, col_bot, r=12, steps=24, **kw):
    """
    Gradient-filled rounded rectangle: draws a clipping poly mask then
    sliced gradient strips. Two-pass: first fill with bottom color (for
    corners), then draw gradient strips inside.
    tags= kwarg is supported.
    """
    tags = kw.pop("tags", "")
    # Base rounded rect (bottom color — fills corners)
    rr(cv, x1, y1, x2, y2, r=r, fill=col_bot, outline="",
       **({"tags": tags} if tags else {}))
    # Gradient strips
    h = y2 - y1
    w = x2 - x1
    for i in range(steps):
        t   = i / steps
        t2  = (i + 1) / steps
        col = _lerp(col_top, col_bot, (t + t2) / 2)
        sy1 = y1 + int(h * t)
        sy2 = y1 + int(h * t2) + 1
        # Clip horizontally to approximate the rounded corners
        corner_clip = 0
        mid_y = (sy1 + sy2) / 2
        dist_top = mid_y - y1
        dist_bot = y2 - mid_y
        edge_dist = min(dist_top, dist_bot)
        if edge_dist < r:
            import math
            corner_clip = int(r - math.sqrt(max(0, r*r - (r - edge_dist)**2)))
        cv.create_rectangle(
            x1 + corner_clip, sy1,
            x2 - corner_clip, sy2,
            fill=col, outline="",
            **({"tags": tags} if tags else {}))

# ── Scrollable frame ──────────────────────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=None, **kw):
        bg = bg or C["bg"]
        super().__init__(parent, bg=bg, **kw)
        self._cv  = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb  = tk.Scrollbar(self, orient="vertical", command=self._cv.yview)
        self.inner= tk.Frame(self._cv, bg=bg)
        self.inner.bind("<Configure>",
            lambda e: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._win = self._cv.create_window((0,0), window=self.inner, anchor="nw")
        self._cv.configure(yscrollcommand=self._sb.set)
        self._cv.pack(side="left", fill="both", expand=True)
        self._sb.pack(side="right", fill="y")
        self._cv.bind("<Configure>",
            lambda e: self._cv.itemconfig(self._win, width=e.width))
        self._cv.bind("<MouseWheel>",
            lambda e: self._cv.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.inner.bind("<MouseWheel>",
            lambda e: self._cv.yview_scroll(int(-1*(e.delta/120)), "units"))
    def top(self): self._cv.yview_moveto(0)

# ── Retro pixel button factory ────────────────────────────────────────────────
# Flat square corners, pixel font, neon border + drop-shadow for arcade feel
def Btn(parent, text, cmd, bg=None, fg=None, w=None, h=None,
        fs=12, r=14, pad_bg=None):
    bg     = bg  or C["accent"]
    fg     = fg  or C["dark"]
    pad_bg = pad_bg or C["bg"]
    f      = tk.Frame(parent, bg=pad_bg)
    fnt    = _retro(fs, "bold")
    bw     = w or (fnt.measure(text) + 64)
    bh     = h or (fs * 2 + 22)

    cv = tk.Canvas(f, width=bw, height=bh, bg=pad_bg, highlightthickness=0)
    cv.pack()

    def draw(color=bg, glowing=False):
        cv.delete("all")
        # Outer glow ring (neon border)
        glow_col = _lerp(color, "#ffffff", 0.18)
        cv.create_rectangle(0, 0, bw-1, bh-1,
                             outline=glow_col, fill="", width=1)
        # Drop shadow
        shadow = _darken(color, 0.30)
        cv.create_rectangle(3, 3, bw-2, bh-2, fill=shadow, outline="")
        # Gradient body — light top, darker bottom
        col_top = _lerp(color, "#ffffff", 0.22)
        col_bot = _darken(color, 0.72)
        _grad(cv, 1, 1, bw-4, bh-4, col_top, col_bot, steps=18)
        # Top-left highlight edge
        bright = _lerp(color, "#ffffff", 0.40)
        cv.create_line(1, bh-4, 1, 1, fill=bright, width=2)
        cv.create_line(1, 1, bw-4, 1, fill=bright, width=2)
        # Bottom-right shadow edge
        cv.create_line(bw-4, 1, bw-4, bh-4, fill=shadow, width=1)
        cv.create_line(1, bh-4, bw-4, bh-4, fill=shadow, width=1)
        # Label shadow + label
        cv.create_text(bw//2 + 1, bh//2 + 1,
                       text=text, fill=_darken(fg, 0.4) if fg != C["dark"] else "#000000",
                       font=fnt)
        cv.create_text(bw//2, bh//2,
                       text=text, fill=fg, font=fnt)

    draw()
    cv.bind("<Enter>",    lambda e: draw(_lerp(bg, "#ffffff", 0.14), True))
    cv.bind("<Leave>",    lambda e: draw(bg))
    cv.bind("<Button-1>", lambda e: [draw(_darken(bg, 0.50)),
                                      f.after(90, lambda: draw(bg)), cmd()])
    f._cv   = cv
    f._draw = draw
    f._bg   = bg
    f._fg   = fg
    f._fnt  = fnt
    f._bw   = bw
    f._bh   = bh
    f._text = text
    return f

# ══════════════════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DeciWise — Family Planning Quiz")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - WINDOW_W) // 2
        y = (self.winfo_screenheight() - WINDOW_H) // 2
        self.geometry(f"{WINDOW_W}x{WINDOW_H}+{x}+{y}")

        # ── Shared quiz state ──────────────────────────────────────────────
        self.player_name      = ""
        self.current_level    = None
        self.chosen_difficulty= "Beginner"   # set by difficulty picker in StoryScreen
        self.quiz_index       = 0
        self.quiz_score       = 0
        self.quiz_answers     = []
        self.lives            = MAX_LIVES
        self.total_xp_session = 0
        self.fast_answers     = 0
        self.congrats_level   = None   # set to level dict when player just passed

        self._frame = None
        self.show("splash")

    # ── Navigate ──────────────────────────────────────────────────────────────
    def show(self, name, **kw):
        if self._frame:
            self._frame.destroy()
        screens = {
            "splash":       SplashScreen,
            "level_select": LevelSelectScreen,
            "story":        StoryScreen,
            "quiz":         QuizScreen,
            "kahoot":       KahootScreen,
            "myth_fact":    MythFactScreen,
            "hangman":      HangmanScreen,
            "jigsaw":       JigsawScreen,
            "crossword":    CrosswordScreen,
            "image_hint":   ImageHintScreen,
            "result":       ResultScreen,
            "gameover":     GameOverScreen,
            "leaderboard":  LeaderboardScreen,
            "badges":       BadgesScreen,
        }
        self._frame = screens[name](self, self, **kw)
        self._frame.pack(fill="both", expand=True)

    def start_level(self):
        """Reset per-level quiz state and route to correct quiz type."""
        self.quiz_index   = 0
        self.quiz_score   = 0
        self.quiz_answers = []
        self.lives        = MAX_LIVES
        self.fast_answers = 0
        qt = self.current_level.get("quiz_type", "standard")
        if qt == "kahoot":
            self.show("kahoot")
        elif qt == "myth_fact":
            self.show("myth_fact")
        elif qt == "hangman":
            self.show("hangman")
        elif qt == "jigsaw":
            self.show("jigsaw")
        elif qt == "crossword":
            self.show("crossword")
        elif qt == "image_hint":
            self.show("image_hint")
        else:
            self.show("quiz")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Splash / Name Entry
# ══════════════════════════════════════════════════════════════════════════════
class SplashScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        # Animated title canvas
        self._cv = tk.Canvas(self, width=WINDOW_W, height=220,
                              bg=C["bg"], highlightthickness=0)
        self._cv.pack()
        self._draw_header()

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=36)

        tk.Label(body, text="─── FAMILY PLANNING QUIZ SYSTEM ───",
                 font=_retro(8), bg=C["bg"],
                 fg=C["grey"]).pack(pady=(4,2))

        # Neon divider
        sep = tk.Canvas(body, width=320, height=4,
                        bg=C["bg"], highlightthickness=0)
        sep.pack(pady=(0,16))
        sep.create_rectangle(0, 1, 320, 2, fill=C["accent3"], outline="")
        sep.create_rectangle(20, 0, 300, 3, fill=C["accent2"], outline="")

        # Name entry
        tk.Label(body, text="▶  ENTER PLAYER NAME",
                 font=_retro(10, "bold"),
                 bg=C["bg"], fg=C["accent"]).pack(anchor="w")
        self._name_var = tk.StringVar()
        # Load saved name
        try:
            p = load_json(PROGRESS_DB)
            self._name_var.set(p.get("player_name",""))
        except Exception:
            pass

        entry = tk.Entry(body, textvariable=self._name_var,
                         font=_retro(13),
                         bg=C["card"], fg=C["accent"],
                         insertbackground=C["accent"],
                         relief="flat", bd=0,
                         highlightbackground=C["accent"],
                         highlightthickness=1,
                         justify="center")
        entry.pack(fill="x", ipady=8, pady=(6,24))
        entry.focus()
        entry.bind("<Return>", lambda e: self._go())

        btn = Btn(body, "[ PRESS START ]", self._go,
                  bg=C["accent"], fg=C["dark"], w=240, fs=13, pad_bg=C["bg"])
        btn.pack(pady=(0,12))

        # Nav row
        nav = tk.Frame(body, bg=C["bg"])
        nav.pack(pady=(0,8))
        Btn(nav, "🏆  LEADERBOARD",
            lambda: self.app.show("leaderboard"),
            bg=C["card2"], fg=C["xp"], w=166, fs=9,
            pad_bg=C["bg"]).pack(side="left", padx=5)
        Btn(nav, "🎖  BADGES",
            lambda: self.app.show("badges"),
            bg=C["card2"], fg=C["gold"], w=166, fs=9,
            pad_bg=C["bg"]).pack(side="left", padx=5)

        # Theme toggle button
        theme_row = tk.Frame(body, bg=C["bg"])
        theme_row.pack(pady=(4, 0))
        self._theme_btn_frame = theme_row
        self._build_theme_btn(theme_row)

        tk.Label(self, text="v2.0  ·  DeciWise  ·  INSERT COIN ▶",
                 font=_retro(7), bg=C["bg"],
                 fg=C["grey"]).pack(side="bottom", pady=6)
        self._blink_insert(self.winfo_children()[-1])

    def _build_theme_btn(self, parent):
        """Draw the light/dark toggle switch canvas."""
        for w in parent.winfo_children():
            w.destroy()
        is_light = _IS_LIGHT
        sw_bg  = C["card2"]
        label  = "☀  LIGHT MODE" if not is_light else "🌙  DARK MODE"
        lbl_fg = C["medium"] if not is_light else C["xp"]
        Btn(parent, label, self._toggle_theme,
            bg=sw_bg, fg=lbl_fg, w=340, fs=10,
            pad_bg=C["bg"]).pack()

    def _toggle_theme(self):
        SFX.play("click")
        _apply_theme(not _IS_LIGHT)
        # Rebuild splash from scratch with new colors
        self.app.show("splash")

    def _draw_header(self):
        cv = self._cv
        cv.delete("all")
        # Gradient background — dark top, slightly lighter bottom
        _grad(cv, 0, 0, WINDOW_W, 220,
              _lerp(C["bg"], "#000000", 0.3), _lerp(C["bg"], C["accent3"], 0.5),
              steps=40)
        # Scanlines
        for y in range(0, 220, 3):
            cv.create_line(0, y, WINDOW_W, y, fill="#171d17", width=1)
        # Outer border — double neon line
        cv.create_rectangle(6, 6, WINDOW_W-6, 214,
                             outline=C["accent3"], width=1)
        cv.create_rectangle(4, 4, WINDOW_W-4, 216,
                             outline=C["accent"], width=2)
        # Chunky corner squares
        corner = 12
        for cx2, cy2 in [(4,4),(WINDOW_W-4-corner,4),
                          (4,216-corner),(WINDOW_W-4-corner,216-corner)]:
            cv.create_rectangle(cx2, cy2, cx2+corner, cy2+corner,
                                 fill=C["accent"], outline="")
        # Neon glow under title (3-layer blur simulation)
        # Neon glow layers under title (bloom effect)
        for off, alpha in [(8,"#0d1f0d"),(6,"#1a3a22"),(4,"#204d2e"),(2,"#2e6640")]:
            cv.create_text(WINDOW_W//2, 78+off//2,
                            text="DECIWISE",
                            font=_retro(38, "bold"),
                            fill=alpha)
        # 3D extrusion — stacked offset layers (bottom-right shadow)
        for step in range(5, 0, -1):
            shade = _lerp("#000000", _darken(C["accent"], 0.5), step / 5)
            cv.create_text(WINDOW_W//2 + step, 75 + step,
                            text="DECIWISE",
                            font=_retro(38, "bold"),
                            fill=shade)
        # Main face
        cv.create_text(WINDOW_W//2, 75,
                        text="DECIWISE",
                        font=_retro(38, "bold"),
                        fill=C["accent"])
        # Top-left specular highlight (bright edge)
        cv.create_text(WINDOW_W//2 - 1, 74,
                        text="DECIWISE",
                        font=_retro(38, "bold"),
                        fill=_lerp(C["accent"], "#ffffff", 0.35))
        # Horizontal neon divider under title
        cv.create_line(40, 100, WINDOW_W-40, 100,
                        fill=C["accent3"], width=1)
        cv.create_line(60, 102, WINDOW_W-60, 102,
                        fill=C["accent2"], width=1)
        # Subtitle
        cv.create_text(WINDOW_W//2, 120, text="★  QUIZ EDITION  ★",
                        font=_retro(12, "bold"), fill=C["medium"])
        # Tagline
        cv.create_text(WINDOW_W//2, 148, text="LEARN  //  DECIDE  //  GROW",
                        font=_retro(9), fill=C["grey"])
        self._after(cv)

    def _after(self, cv, on=True):
        """Blink a cursor on the header canvas."""
        try:
            cv.delete("cursor_line")
            if on:
                cv.create_line(WINDOW_W//2 - 60, 170,
                                WINDOW_W//2 + 60, 170,
                                fill=C["accent"], width=2,
                                tags="cursor_line")
            self._cv.after(500, lambda: self._after(cv, not on))
        except Exception:
            pass

    def _blink_insert(self, lbl, on=True):
        """Blink the INSERT COIN label."""
        try:
            lbl.configure(fg=C["accent"] if on else C["accent3"])
            lbl.after(600, lambda: self._blink_insert(lbl, not on))
        except Exception:
            pass

    def _go(self):
        name = self._name_var.get().strip() or "PLAYER_1"
        self.app.player_name = name
        try:
            p = load_json(PROGRESS_DB)
            p["player_name"] = name
            save_json(PROGRESS_DB, p)
        except Exception:
            pass
        SFX.play("start")
        self.app.show("level_select")

# ══════════════════════════════════════════════════════════════════════════════
# WIDGET — Congratulations Popup + Confetti  (Toplevel-based)
# ══════════════════════════════════════════════════════════════════════════════
import random as _random

class CongratsPopup:
    """
    Retro CRT congratulations overlay with pixel-art card and scanline particles.
    Auto-dismisses after 4.5 s or on any click.
    """
    _PARTICLE_COUNT = 60
    # Neon arcade pixel-confetti palette
    _COLORS = ["#00ff41","#ffaa00","#ff3333","#00ccff",
               "#cc44ff","#ffcc00","#ff6600","#00ff99",
               "#ff0099","#33ffcc","#ffff00","#ff44aa"]
    _FPS_MS = 28
    _BG     = "#141c14"   # near-black CRT green tint

    def __init__(self, parent, info):
        self._root    = parent.winfo_toplevel()
        self._info    = info
        self._aids    = []
        self._running = True

        # ── Toplevel window ───────────────────────────────────────────────
        self._win = tk.Toplevel(self._root)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)

        self._root.update_idletasks()
        rx = self._root.winfo_x()
        ry = self._root.winfo_y()
        self._win.geometry(f"{WINDOW_W}x{WINDOW_H}+{rx}+{ry}")
        self._win.configure(bg=self._BG)

        # ── Full-window canvas ────────────────────────────────────────────
        self._cv = tk.Canvas(
            self._win, width=WINDOW_W, height=WINDOW_H,
            bg=self._BG, highlightthickness=0)
        self._cv.pack(fill="both", expand=True)

        # Draw CRT scanlines as permanent dark stripes on the background
        for y in range(0, WINDOW_H, 4):
            self._cv.create_line(0, y, WINDOW_W, y,
                                 fill="#001200", width=1, tags="scanline")

        # ── Spawn pixel confetti ──────────────────────────────────────────
        self._particles = []
        for _ in range(self._PARTICLE_COUNT):
            self._spawn_particle(start_above=True)

        # ── Draw the congratulations card ─────────────────────────────────
        self._draw_card()

        # ── Dismiss on click anywhere ─────────────────────────────────────
        self._cv.bind("<Button-1>",   lambda e: self._dismiss())
        self._win.bind("<Button-1>",  lambda e: self._dismiss())

        # ── Start animation + auto-dismiss timer ──────────────────────────
        self._aids.append(self._win.after(self._FPS_MS, self._tick))
        self._aids.append(self._win.after(4500, self._dismiss))

    # ── Particle factory ──────────────────────────────────────────────────────
    def _spawn_particle(self, start_above=False):
        x  = _random.uniform(0, WINDOW_W)
        y  = _random.uniform(-WINDOW_H, 0) if start_above else _random.uniform(-80, -8)
        vx = _random.uniform(-1.5, 1.5)
        vy = _random.uniform(2.5, 6.0)
        # Chunky square pixels — retro feel
        pw = _random.choice([4, 6, 8, 10])
        ph = pw   # square
        color = _random.choice(self._COLORS)
        oid = self._cv.create_rectangle(
            x, y, x+pw, y+ph, fill=color, outline="")
        self._particles.append({
            "id": oid, "x": x, "y": y,
            "vx": vx, "vy": vy, "w": pw, "h": ph
        })

    # ── Draw card ─────────────────────────────────────────────────────────────
    def _draw_card(self):
        lvl   = self._info["lvl"]
        score = self._info["score"]
        total = self._info["total"]
        stars = self._info["stars"]
        pct   = self._info["pct"]
        dc    = lvl["difficulty_color"]

        cw, ch = 320, 280
        cx = (WINDOW_W - cw) // 2
        cy = (WINDOW_H - ch) // 2

        # ── Outer neon glow border with 3D bevel ──────────────────────────
        for i in range(4):
            self._cv.create_rectangle(
                cx - i, cy - i, cx + cw + i, cy + ch + i,
                outline=dc, fill="", tags="card_top")
        # 3D bevel — bright top-left, dark bottom-right
        self._cv.create_line(cx-4, cy-4, cx+cw+4, cy-4,
                             fill=_lerp(dc,"#ffffff",0.5), width=2, tags="card_top")
        self._cv.create_line(cx-4, cy-4, cx-4, cy+ch+4,
                             fill=_lerp(dc,"#ffffff",0.35), width=2, tags="card_top")
        self._cv.create_line(cx+cw+4, cy-4, cx+cw+4, cy+ch+4,
                             fill=_darken(dc, 0.4), width=2, tags="card_top")
        self._cv.create_line(cx-4, cy+ch+4, cx+cw+4, cy+ch+4,
                             fill=_darken(dc, 0.4), width=2, tags="card_top")

        # ── Card body — gradient dark CRT background ──────────────────────
        _grad_rr(self._cv, cx, cy, cx + cw, cy + ch,
                 _lerp(C["bg"], "#2a3a2a", 0.8), C["bg"],
                 r=8, steps=30, tags="card_top")

        # ── Chunky pixel corners ───────────────────────────────────────────
        corner_size = 10
        for ox, oy in [(cx, cy), (cx+cw-corner_size, cy),
                       (cx, cy+ch-corner_size), (cx+cw-corner_size, cy+ch-corner_size)]:
            self._cv.create_rectangle(
                ox, oy, ox+corner_size, oy+corner_size,
                fill=dc, outline="", tags="card_top")

        # ── Top header strip — gradient with 3D bevel ─────────────────────
        _grad(self._cv, cx, cy, cx+cw, cy+38,
              _lerp(dc, "#ffffff", 0.25), _darken(dc, 0.7),
              steps=20, tags="card_top")
        # Top highlight edge (bevel)
        self._cv.create_line(cx, cy, cx+cw, cy,
                             fill=_lerp(dc, "#ffffff", 0.6),
                             width=2, tags="card_top")
        # Left highlight edge (bevel)
        self._cv.create_line(cx, cy, cx, cy+38,
                             fill=_lerp(dc, "#ffffff", 0.4),
                             width=1, tags="card_top")
        # Bottom shadow edge (bevel)
        self._cv.create_line(cx, cy+37, cx+cw, cy+37,
                             fill=_darken(dc, 0.4),
                             width=2, tags="card_top")
        # Scanlines over the header strip
        for y in range(cy, cy+38, 4):
            self._cv.create_line(cx, y, cx+cw, y,
                                 fill="#1a3a1a", width=1, tags="card_top")
        self._cv.create_text(
            WINDOW_W//2, cy + 19,
            text=f"[ LVL {lvl['id']} : {lvl['difficulty'].upper()} ]",
            font=_retro(10, "bold"),
            fill="#000000", tags="card_top")

        # ── Arcade result label ────────────────────────────────────────────
        icon = "** PERFECT **" if pct == 1.0 else "* CLEARED *"
        self._cv.create_text(
            WINDOW_W//2, cy + 68,
            text=icon,
            font=_retro(13, "bold"),
            fill="#ffcc00", tags="card_top")

        # ── Main message with pixel shadow ─────────────────────────────────
        msg = "PERFECT SCORE!" if pct == 1.0 else "LESSON PASSED!"
        self._cv.create_text(
            WINDOW_W//2 + 2, cy + 103,
            text=msg, font=_retro(16, "bold"),
            fill="#1a4a1a", tags="card_top")
        self._cv.create_text(
            WINDOW_W//2, cy + 101,
            text=msg, font=_retro(16, "bold"),
            fill="#00ff41", tags="card_top")

        # ── Level title ────────────────────────────────────────────────────
        self._cv.create_text(
            WINDOW_W//2, cy + 128,
            text=lvl["title"],
            font=_retro(9),
            fill="#aaffaa", tags="card_top")

        # ── Score ──────────────────────────────────────────────────────────
        self._cv.create_text(
            WINDOW_W//2, cy + 155,
            text=f"SCORE:  {score} / {total}",
            font=_retro(12, "bold"),
            fill=dc, tags="card_top")

        # ── Pixel star rating (ASCII block style) ──────────────────────────
        star_str = ("[ * ]" * stars) + ("[ . ]" * (3 - stars))
        self._cv.create_text(
            WINDOW_W//2, cy + 182,
            text=star_str,
            font=_retro(11, "bold"),
            fill="#ffcc00", tags="card_top")

        # ── Horizontal pixel divider ───────────────────────────────────────
        self._cv.create_rectangle(
            cx + 20, cy + 202, cx + cw - 20, cy + 204,
            fill="#00cc33", outline="", tags="card_top")        # ── Dismiss hint ───────────────────────────────────────────────────
        self._cv.create_text(
            WINDOW_W//2, cy + 258,
            text="[ PRESS ANYWHERE TO CONTINUE ]",
            font=_retro(8),
            fill="#aaffaa", tags="card_top")

    # ── Animation tick ────────────────────────────────────────────────────────
    def _tick(self):
        if not self._running:
            return
        for p in self._particles:
            p["vy"] = min(p["vy"] + 0.07, 9)
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            # Wrap horizontal
            if p["x"] > WINDOW_W + 12:  p["x"] = -12
            elif p["x"] < -12:           p["x"] = WINDOW_W + 12
            # Reset fallen particles
            if p["y"] > WINDOW_H + 12:
                p["y"] = _random.uniform(-60, -8)
                p["x"] = _random.uniform(0, WINDOW_W)
                p["vy"] = _random.uniform(2.0, 5.5)
            self._cv.coords(
                p["id"],
                p["x"], p["y"],
                p["x"] + p["w"], p["y"] + p["h"])

        # Redraw card on top so confetti doesn't cover it
        self._cv.tag_raise("card_top")
        self._aids.append(self._win.after(self._FPS_MS, self._tick))

    # ── Dismiss ───────────────────────────────────────────────────────────────
    def _dismiss(self):
        if not self._running:
            return
        self._running = False
        for a in self._aids:
            try: self._win.after_cancel(a)
            except Exception: pass
        try:
            self._win.destroy()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Level Select  (Act-based journey map)
# ══════════════════════════════════════════════════════════════════════════════
class LevelSelectScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()
        # Show congratulations popup if coming from a passed level
        if app.congrats_level:
            self.after(400, self._show_congrats)

    def _show_congrats(self):
        info = self.app.congrats_level
        self.app.congrats_level = None
        CongratsPopup(self, info)

    def _build(self):
        p         = load_json(PROGRESS_DB)
        levels    = load_json(QUESTIONS_DB)["levels"]
        unlocked  = p.get("unlocked_levels", [1])
        completed = p.get("completed_levels", [])
        scores    = p.get("high_scores", {})
        total_xp  = p.get("total_xp", 0)
        lvl_map   = {l["id"]: l for l in levels}

        # ── Top bar ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["banner"], pady=0)
        hdr.pack(fill="x")
        # Neon top edge
        tk.Frame(hdr, bg=C["accent"], height=2).pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=C["banner"], pady=8)
        inner_hdr.pack(fill="x")
        tk.Label(inner_hdr, text="  ▶ DeciWise",
                 font=_retro(14, "bold"),
                 bg=C["banner"], fg=C["accent"]).pack(side="left", padx=10)
        name = self.app.player_name or p.get("player_name","Player")
        # Player + XP pill on right
        right_f = tk.Frame(inner_hdr, bg=C["banner"])
        right_f.pack(side="right", padx=10)
        tk.Label(right_f, text=f"⚡ {total_xp} XP",
                 font=_retro(10, "bold"),
                 bg=C["banner"], fg=C["xp"]).pack(side="right", padx=(4,0))
        tk.Label(right_f, text=f"👤 {name}",
                 font=_retro(9),
                 bg=C["banner"], fg=C["grey"]).pack(side="right", padx=4)
        # Neon bottom edge
        tk.Frame(hdr, bg=C["accent3"], height=1).pack(fill="x")

        # ── Scrollable body ───────────────────────────────────────────────
        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        tk.Label(inner, text="── YOUR LEARNING JOURNEY ──",
                 font=_retro(11, "bold"),
                 bg=C["bg"], fg=C["accent2"]).pack(pady=(16,2))

        total_stars = sum(scores.get(str(i),{}).get("stars",0)
                          for i in range(1,7))
        tk.Label(inner, text=f"⭐  {total_stars} / 18  stars collected",
                 font=_retro(9),
                 bg=C["bg"], fg=C["gold"]).pack(pady=(0,10))

        # ── Act sections ─────────────────────────────────────────────────
        for act_id, (act_label, act_title, act_color, lids) in ACT_MAP.items():
            act_done = all(lid in completed for lid in lids)
            act_open = any(lid in unlocked  for lid in lids)

            # Act header
            ah = tk.Frame(inner, bg=_darken(act_color, 0.25), pady=8)
            ah.pack(fill="x", padx=10, pady=(8,0))
            tk.Label(ah, text=f"{act_label}  ·  {act_title}",
                     font=_retro(12, "bold"),
                     bg=_darken(act_color, 0.25),
                     fg=act_color).pack(side="left", padx=12)
            if act_done:
                tk.Label(ah, text="✔ COMPLETE",
                         font=_retro(10, "bold"),
                         bg=_darken(act_color, 0.25),
                         fg=C["correct"]).pack(side="right", padx=12)

            for lid in lids:
                lvl     = lvl_map[lid]
                is_open = lid in unlocked
                is_done = lid in completed
                s       = scores.get(str(lid), {})
                self._card(inner, lvl, is_open, is_done, s, act_color)

        # ── Bottom buttons ────────────────────────────────────────────────
        brow = tk.Frame(inner, bg=C["bg"])
        brow.pack(pady=18)
        Btn(brow, "🏠 Home",
            lambda: self.app.show("splash"),
            bg=C["card2"], fg=C["white"], w=130, fs=10,
            pad_bg=C["bg"]).pack(side="left", padx=6)
        Btn(brow, "🏆 Leaderboard",
            lambda: self.app.show("leaderboard"),
            bg=C["card2"], fg=C["white"], w=160, fs=10,
            pad_bg=C["bg"]).pack(side="left", padx=6)
        tk.Label(inner, text="", bg=C["bg"], height=1).pack()

    def _card(self, parent, lvl, is_open, is_done, sd, act_color):
        lid        = lvl["id"]
        diff_color = lvl["difficulty_color"]
        stars_n    = sd.get("stars", 0)
        hs_score   = sd.get("score", 0)
        hs_total   = sd.get("total", 5)
        bg = C["card"] if is_open else C["locked"]

        outer = tk.Frame(parent, bg=C["bg"], pady=3, padx=12)
        outer.pack(fill="x")

        # Neon left-border strip
        wrap = tk.Frame(outer, bg=act_color if is_open else C["locked"])
        wrap.pack(fill="x")
        strip = tk.Frame(wrap, bg=act_color if is_open else C["locked"], width=4)
        strip.pack(side="left", fill="y")
        card = tk.Frame(wrap, bg=bg, padx=12, pady=10,
                        highlightbackground=_darken(act_color,0.5) if is_open else bg,
                        highlightthickness=1 if is_open else 0)
        card.pack(side="left", fill="x", expand=True)

        row1 = tk.Frame(card, bg=bg)
        row1.pack(fill="x")

        # Level number pill badge — 3D extruded look
        num_cv = tk.Canvas(row1, width=40, height=40,
                            bg=bg, highlightthickness=0)
        num_cv.pack(side="left", padx=(0,10))
        if is_open:
            ac = act_color
            # Bottom-right drop shadow (depth layer)
            num_cv.create_oval(5, 5, 37, 37,
                               fill=_darken(ac, 0.25), outline="")
            # Mid layer (side face of extrusion)
            num_cv.create_oval(3, 3, 35, 35,
                               fill=_darken(ac, 0.45), outline="")
            # Main face gradient (top-left bright, bottom-right dark)
            num_cv.create_oval(1, 1, 33, 33,
                               fill=ac, outline="")
            # Specular highlight (top-left inner gleam)
            num_cv.create_oval(4, 4, 18, 16,
                               fill=_lerp(ac, "#ffffff", 0.45), outline="")
            # Inner subtle ring
            num_cv.create_oval(2, 2, 32, 32,
                               outline=_lerp(ac, "#ffffff", 0.25), fill="", width=1)
        else:
            num_cv.create_oval(3, 3, 37, 37,
                               fill=_darken(C["locked"], 0.6), outline="")
            num_cv.create_oval(1, 1, 35, 35,
                               fill=C["locked"], outline="")
        num_cv.create_text(17, 17, text=str(lid),
                            fill=C["bg"] if is_open else C["grey"],
                            font=_retro(11, "bold"))

        info = tk.Frame(row1, bg=bg)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=lvl["title"],
                 font=_retro(11, "bold"),
                 bg=bg, fg=C["white"] if is_open else C["grey"]).pack(anchor="w")
        tk.Label(info, text=f"{lvl['difficulty']}  ·  10 Qs  ·  Pick difficulty",
                 font=_retro(8),
                 bg=bg, fg=diff_color if is_open else C["locked"]).pack(anchor="w")

        if is_open:
            status = tk.Frame(row1, bg=bg)
            status.pack(side="right")
            if is_done:
                tk.Label(status, text="⭐"*stars_n+"☆"*(3-stars_n),
                         font=_retro(13), bg=bg, fg=C["gold"]).pack()
                tk.Label(status, text=f"{hs_score}/{hs_total}",
                         font=_retro(8), bg=bg, fg=C["grey"]).pack()
            else:
                tk.Label(status, text="PLAY ▶",
                         font=_retro(10, "bold"),
                         bg=bg, fg=C["accent"],
                         cursor="hand2").pack()
        else:
            tk.Label(row1, text="🔒",
                     font=_retro(14), bg=bg,
                     fg=C["grey"]).pack(side="right")

        if is_open:
            for w in card.winfo_children() + [card]:
                w.bind("<Button-1>", lambda e, l=lvl: self._open(l))
            for w in row1.winfo_children() + [row1] + info.winfo_children():
                w.bind("<Button-1>", lambda e, l=lvl: self._open(l))

    def _open(self, lvl):
        SFX.play("click")
        self.app.current_level = lvl
        self.app.show("story")

# ── Video Player ──────────────────────────────────────────────────────────────
class _VideoPlayer:
    """
    Plays a video file (any format OpenCV can decode, including .mov) inside
    a Tkinter Canvas. No audio — video frames only.
    Controls: Play/Pause button + progress bar.
    Call .frame to get the tk widget to pack/grid.
    Call .stop() before destroying the parent.
    """
    _FPS_DEFAULT = 30

    def __init__(self, parent, path, width=430, height=260):
        self._path    = path
        self._w       = width
        self._h       = height
        self._playing = False
        self._after_id= None
        self._cap     = None
        self._photo   = None
        self._total   = 0
        self._fps     = self._FPS_DEFAULT

        # Root frame — pack this
        self.frame = tk.Frame(parent, bg="#000000")

        try:
            import cv2 as _cv2
            from PIL import Image as _Image, ImageTk as _ImageTk
            self._cv2      = _cv2
            self._Image    = _Image
            self._ImageTk  = _ImageTk
        except ImportError as e:
            self._cv2 = None
            tk.Label(self.frame,
                     text=f"⚠ Video unavailable ({e})",
                     bg="#000000", fg="#ff6b6b",
                     font=_retro(10)).pack(pady=20)
            return

        # Canvas for frames
        self._canvas = tk.Canvas(self.frame, width=width, height=height,
                                  bg="#000000", highlightthickness=0)
        self._canvas.pack()

        # Controls bar
        ctrl = tk.Frame(self.frame, bg=C["banner"])
        ctrl.pack(fill="x")

        self._play_btn = tk.Label(ctrl, text="⏸  Pause",
                                   font=_retro(10, "bold"),
                                   bg=C["banner"], fg=C["accent"],
                                   cursor="hand2", padx=10, pady=4)
        self._play_btn.pack(side="left")
        self._play_btn.bind("<Button-1>", lambda e: self._toggle())

        self._time_lbl = tk.Label(ctrl, text="0:00 / 0:00",
                                   font=_retro(8),
                                   bg=C["banner"], fg=C["grey"], padx=8)
        self._time_lbl.pack(side="right")

        # Progress bar (clickable)
        self._prog_bg = tk.Canvas(ctrl, height=6, bg=C["locked"],
                                   highlightthickness=0)
        self._prog_bg.pack(side="left", fill="x", expand=True, padx=6, pady=8)
        self._prog_fill = self._prog_bg.create_rectangle(
            0, 0, 0, 6, fill=C["accent"], outline="")
        self._prog_bg.bind("<Button-1>", self._seek)

        self._open()

    def pack(self, **kw):
        self.frame.pack(**kw)

    def _open(self):
        if self._cv2 is None:
            return
        # Normalize path separators for Windows
        path = str(self._path).replace("/", "\\")
        self._cap = self._cv2.VideoCapture(path)
        if not self._cap.isOpened():
            self._cap = None
            self._show_error("Cannot open video file.\nCheck the file path and format.")
            return
        # Test-read one frame to confirm it actually works
        ret, _ = self._cap.read()
        if not ret:
            self._cap.release()
            self._cap = None
            self._show_error("Video file opened but no frames found.\n(.mov may need codec support)")
            return
        # Rewind to start
        self._cap.set(self._cv2.CAP_PROP_POS_FRAMES, 0)
        self._fps   = self._cap.get(self._cv2.CAP_PROP_FPS) or self._FPS_DEFAULT
        self._total = int(self._cap.get(self._cv2.CAP_PROP_FRAME_COUNT))
        self._show_frame()
        self._play()   # auto-play

    def _show_error(self, msg):
        tk.Label(self.frame, text=f"⚠ {msg}",
                 bg="#000000", fg="#ff6b6b",
                 font=_retro(9), wraplength=WINDOW_W-20,
                 justify="center").pack(pady=20)

    def _show_frame(self):
        if self._cap is None or self._cv2 is None:
            return False
        ret, frame = self._cap.read()
        if not ret:
            return False
        frame = self._cv2.resize(frame, (self._w, self._h))
        frame = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        img = self._Image.fromarray(frame)
        self._photo = self._ImageTk.PhotoImage(img)
        self._canvas.create_image(0, 0, anchor="nw", image=self._photo)
        # Progress bar
        pos = int(self._cap.get(self._cv2.CAP_PROP_POS_FRAMES))
        if self._total > 0:
            ratio = pos / self._total
            bw = self._prog_bg.winfo_width() or (self._w - 120)
            self._prog_bg.coords(self._prog_fill, 0, 0, int(bw * ratio), 6)
        # Time label
        fps = self._fps or self._FPS_DEFAULT
        cur_s = int(pos / fps)
        tot_s = int(self._total / fps)
        self._time_lbl.configure(
            text=f"{cur_s//60}:{cur_s%60:02d} / {tot_s//60}:{tot_s%60:02d}")
        return True

    def _tick(self):
        if not self._playing or self._cap is None:
            return
        ok = self._show_frame()
        if ok:
            delay = max(1, int(1000 / (self._fps or self._FPS_DEFAULT)))
            self._after_id = self.frame.after(delay, self._tick)
        else:
            # Ended — reset to start, stop
            self._cap.set(self._cv2.CAP_PROP_POS_FRAMES, 0)
            self._show_frame()   # show first frame as poster
            self._playing = False
            self._play_btn.configure(text="▶  Play")

    def _play(self):
        self._playing = True
        self._play_btn.configure(text="⏸  Pause")
        self._tick()

    def _pause(self):
        self._playing = False
        self._play_btn.configure(text="▶  Play")
        if self._after_id:
            try: self.frame.after_cancel(self._after_id)
            except Exception: pass

    def _toggle(self):
        SFX.play("click")
        if self._cap is None:
            return
        if self._playing:
            self._pause()
        else:
            self._play()

    def _seek(self, event):
        if self._cap is None or self._total == 0:
            return
        bw = self._prog_bg.winfo_width()
        if bw <= 0:
            return
        ratio = max(0.0, min(1.0, event.x / bw))
        self._cap.set(self._cv2.CAP_PROP_POS_FRAMES, int(ratio * self._total))
        self._show_frame()

    def stop(self):
        self._playing = False
        if self._after_id:
            try: self.frame.after_cancel(self._after_id)
            except Exception: pass
        if self._cap:
            try: self._cap.release()
            except Exception: pass
            self._cap = None


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Story (animated typewriter)
# ══════════════════════════════════════════════════════════════════════════════
class StoryScreen(tk.Frame):
    _TW_DELAY   = 20
    _BOUNCE     = [22,36,52,66,60,64,62,62]
    _FADE_STEPS = 14

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app        = app
        self._aids      = []
        self._done      = False
        self._video     = None   # VideoPlayer instance
        self._build()

    def _build(self):
        lvl = self.app.current_level
        self._lvl       = lvl
        self._icon_char = STORY_ICONS.get(lvl.get("story_image",""), "📖")
        diff_c  = lvl["difficulty_color"]
        timer_s = "30 / 22 / 16"   # depends on chosen difficulty

        # Banner
        self._banner = tk.Frame(self, bg=C["bg"], pady=10)
        self._banner.pack(fill="x")
        self._t1 = tk.Label(self._banner,
                             text=f"Level {lvl['id']}: {lvl['title']}",
                             font=_retro(15, "bold"),
                             bg=C["bg"], fg=C["bg"])
        self._t1.pack()
        self._t2 = tk.Label(self._banner,
                             text=f"{lvl['difficulty']}  ·  {timer_s}s per question  ·  ❤ {MAX_LIVES} lives",
                             font=_retro(10),
                             bg=C["bg"], fg=C["bg"])
        self._t2.pack()

        # Skip
        sk = tk.Frame(self, bg=C["bg"])
        sk.pack(anchor="e", padx=12, pady=(0,4))
        skcv = tk.Canvas(sk, width=90, height=26,
                          bg=C["bg"], highlightthickness=0)
        skcv.pack()
        skcv.create_rectangle(0,0,90,26, fill=C["locked"], outline="", tags="bg")
        skcv.create_text(45,13, text="Skip ▶▶",
                          fill=C["grey"],
                          font=_retro(9, "bold"), tags="t")
        skcv.bind("<Button-1>", lambda e: self._skip())
        skcv.bind("<Enter>",  lambda e: skcv.itemconfig("bg",fill=C["accent3"]))
        skcv.bind("<Leave>",  lambda e: skcv.itemconfig("bg",fill=C["locked"]))

        # ── Video player (if chapter has a video file) ────────────────────
        video_rel = lvl.get("video_file", "")
        if video_rel:
            video_abs = os.path.join(os.path.dirname(__file__), video_rel)
            if os.path.exists(video_abs):
                self._video = _VideoPlayer(self, video_abs,
                                           width=WINDOW_W, height=260)
                self._video.pack(fill="x")

        # Scroll body
        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        self._sf = sf
        inn = sf.inner
        inn.configure(padx=18)

        self._icon_lbl = tk.Label(inn, text="",
                                   font=("Segoe UI Emoji",62), bg=C["bg"])
        self._icon_lbl.pack(pady=(16,4))

        self._hdr_lbl = tk.Label(inn, text="📖  Story",
                                  font=_retro(12, "bold"),
                                  bg=C["bg"], fg=C["bg"], anchor="w")
        self._hdr_lbl.pack(fill="x", pady=(0,6))

        sc = tk.Frame(inn, bg=C["card"], padx=16, pady=14,
                      highlightbackground=C["accent2"], highlightthickness=1)
        sc.pack(fill="x")
        self._st = tk.Label(sc, text="",
                             font=_retro(11),
                             bg=C["card"], fg=C["white"],
                             wraplength=368, justify="left", anchor="nw")
        self._st.pack(anchor="w")

        # Info strip (shown after story reveals)
        self._info = tk.Label(inn,
                               text=f"❓ 10 Questions  |  ❤ {MAX_LIVES} lives",
                               font=_retro(10),
                               bg=C["bg"], fg=C["bg"])
        self._info.pack(pady=(12,4))

        # XP info
        xp_est = 10 * XP_CORRECT
        self._xp_lbl = tk.Label(inn,
                                  text=f"⚡ Earn up to {xp_est + XP_PERFECT} XP",
                                  font=_retro(9),
                                  bg=C["bg"], fg=C["bg"])
        self._xp_lbl.pack(pady=(0,8))

        # ── Difficulty picker or Begin button (revealed after story) ────────
        self._diff_frame = tk.Frame(inn, bg=C["bg"])
        self._diff_frame.pack(pady=(0,6))

        quiz_type = lvl.get("quiz_type", "standard")

        if quiz_type == "kahoot":
            diff_label = tk.Label(self._diff_frame,
                                  text="🎮  KAHOOT STYLE  —  20s per question",
                                  font=_retro(10, "bold"),
                                  bg=C["bg"], fg=C["bg"])
            diff_label.pack(pady=(0,8))
            self._diff_label = diff_label
            Btn(self._diff_frame, "  START KAHOOT  ▶  ",
                lambda: self._pick_difficulty("Kahoot"),
                bg="#e74c3c", fg=C["white"], w=260, fs=13,
                pad_bg=C["bg"]).pack(pady=(0,4))

        elif quiz_type == "myth_fact":
            diff_label = tk.Label(self._diff_frame,
                                  text="🧠  MYTH OR FACT  —  Choose wisely!",
                                  font=_retro(10, "bold"),
                                  bg=C["bg"], fg=C["bg"])
            diff_label.pack(pady=(0,8))
            self._diff_label = diff_label
            Btn(self._diff_frame, "  START QUIZ  ▶  ",
                lambda: self._pick_difficulty("Beginner"),
                bg="#8e44ad", fg=C["white"], w=260, fs=13,
                pad_bg=C["bg"]).pack(pady=(0,4))

        elif quiz_type in ("hangman", "jigsaw", "crossword", "image_hint"):
            icons = {"hangman": "🎯", "jigsaw": "🧩",
                     "crossword": "📝", "image_hint": "🖼️"}
            names = {"hangman": "HANGMAN", "jigsaw": "JIGSAW PUZZLE",
                     "crossword": "CROSSWORD", "image_hint": "IMAGE HINT"}
            icon = icons.get(quiz_type, "▶")
            name = names.get(quiz_type, quiz_type.upper())
            diff_label = tk.Label(self._diff_frame,
                                  text=f"{icon}  {name}",
                                  font=_retro(12, "bold"),
                                  bg=C["bg"], fg=C["bg"])
            diff_label.pack(pady=(0,8))
            self._diff_label = diff_label
            Btn(self._diff_frame, f"  START {name}  ▶  ",
                lambda: self._pick_difficulty("Beginner"),
                bg="#3498db", fg=C["white"], w=280, fs=13,
                pad_bg=C["bg"]).pack(pady=(0,4))

        else:
            diff_label = tk.Label(self._diff_frame,
                                  text="── CHOOSE DIFFICULTY ──",
                                  font=_retro(10, "bold"),
                                  bg=C["bg"], fg=C["bg"])
            diff_label.pack(pady=(0,8))
            self._diff_label = diff_label
            diff_btns = tk.Frame(self._diff_frame, bg=C["bg"])
            diff_btns.pack()
            DIFFS = [
                ("Beginner",     C["easy"],   "30s each"),
                ("Intermediate", C["medium"], "22s each"),
                ("Difficult",    C["hard"],   "16s each"),
            ]
            for dname, dcol, dtimer in DIFFS:
                Btn(diff_btns, dname,
                    lambda d=dname: self._pick_difficulty(d),
                    bg=dcol, fg=C["bg"], w=120, fs=10,
                    pad_bg=C["bg"]).pack(side="left", padx=4)

        # Back button (always visible)
        self._back_f = Btn(inn, "← Back", self._back,
                           bg=C["card2"], fg=C["white"], w=120, fs=11,
                           pad_bg=C["bg"])
        self._back_f.pack(pady=(8, 24))
        tk.Label(inn, text="", bg=C["bg"], height=2).pack()

        self._aids.append(self.after(100, self._anim_banner))

    # Animations ──────────────────────────────────────────────────────────────
    def _anim_banner(self, step=0):
        n = self._FADE_STEPS
        t = min(step/n, 1.0)
        self._banner.configure(bg=_lerp(C["bg"], C["banner"], t))
        self._t1.configure(bg=_lerp(C["bg"],C["banner"],t),
                            fg=_lerp(C["bg"],C["white"],t))
        self._t2.configure(bg=_lerp(C["bg"],C["banner"],t),
                            fg=_lerp(C["bg"],self._lvl["difficulty_color"],t))
        if step < n:
            self._aids.append(self.after(28, lambda: self._anim_banner(step+1)))
        else:
            self._hdr_lbl.configure(fg=C["accent"])
            self._aids.append(self.after(60, self._anim_icon))

    def _anim_icon(self, step=0):
        sizes = self._BOUNCE
        size  = sizes[min(step, len(sizes)-1)]
        self._icon_lbl.configure(text=self._icon_char,
                                  font=("Segoe UI Emoji", size))
        if step < len(sizes)-1:
            self._aids.append(self.after(52, lambda: self._anim_icon(step+1)))
        else:
            self._aids.append(self.after(100, self._anim_type))

    def _anim_type(self, i=0):
        txt = self._lvl["story"]
        if i <= len(txt):
            self._st.configure(text=txt[:i]+"▌")
            self._sf.top()
            if i < len(txt):
                d = self._TW_DELAY * (5 if i>0 and txt[i-1] in ".!?," else 1)
                if i % 4 == 0: SFX.play("tick")
                self._aids.append(self.after(d, lambda: self._anim_type(i+1)))
            else:
                self._done = True
                self._st.configure(text=txt)
                self._aids.append(self.after(200, lambda: self._blink(txt,0)))
        else:
            self._reveal(0)

    def _blink(self, txt, n):
        if n >= 6:
            self._st.configure(text=txt)
            self._reveal(0)
            return
        self._st.configure(text=txt + ("▌" if n%2==0 else " "))
        self._aids.append(self.after(350, lambda: self._blink(txt, n+1)))

    def _reveal(self, step=0):
        n = self._FADE_STEPS
        t = min(step/n, 1.0)
        self._info.configure(fg=_lerp(C["bg"], C["grey"], t))
        self._xp_lbl.configure(fg=_lerp(C["bg"], C["xp"], t))
        self._diff_label.configure(
            fg=_lerp(C["bg"], C["accent"], t),
            bg=_lerp(C["bg"], C["bg"], t))
        if step < n:
            self._aids.append(self.after(32, lambda: self._reveal(step+1)))

    def _pick_difficulty(self, difficulty):
        """Called when user picks a difficulty — store it and start quiz."""
        [self.after_cancel(a) for a in self._aids]
        if self._video:
            self._video.stop()
        SFX.play("start")
        self.app.chosen_difficulty = difficulty
        self.app.start_level()

    def _skip(self):
        [self.after_cancel(a) for a in self._aids]
        self._aids.clear()
        if self._video:
            self._video.stop()
        lvl = self._lvl
        self._banner.configure(bg=C["banner"])
        self._t1.configure(bg=C["banner"], fg=C["white"])
        self._t2.configure(bg=C["banner"], fg=lvl["difficulty_color"])
        self._icon_lbl.configure(text=self._icon_char,
                                  font=("Segoe UI Emoji",62))
        self._hdr_lbl.configure(fg=C["accent"])
        self._st.configure(text=lvl["story"])
        self._info.configure(fg=C["grey"])
        self._xp_lbl.configure(fg=C["xp"])
        self._diff_label.configure(fg=C["accent"])
        if not self._back_f.winfo_ismapped():
            self._back_f.pack(pady=(8, 24))
        self._back_f._draw()
        self._done = True

    def _back(self):
        [self.after_cancel(a) for a in self._aids]
        if self._video:
            self._video.stop()
        SFX.play("back")
        self.app.show("level_select")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Quiz  (timer + lives + XP + pause)
# ══════════════════════════════════════════════════════════════════════════════
class QuizScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app     = app
        self._locked = False
        self._paused = False
        self._t_left = TIMER.get(app.chosen_difficulty,
                                  TIMER[app.current_level["difficulty"]])
        self._t_total= self._t_left
        self._t_aid  = None
        self._q_start= time.time()
        self._build()
        self._tick()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        app   = self.app
        lvl   = app.current_level
        idx   = app.quiz_index
        diff  = app.chosen_difficulty.lower()   # "beginner"/"intermediate"/"difficult"
        qs    = lvl.get(diff, lvl.get("questions", []))
        q     = qs[idx]
        total = len(qs)

        # ── HUD bar ──────────────────────────────────────────────────────
        hud_wrap = tk.Frame(self, bg=C["banner"])
        hud_wrap.pack(fill="x")
        tk.Frame(hud_wrap, bg=C["accent"], height=2).pack(fill="x")
        hud = tk.Frame(hud_wrap, bg=C["banner"], pady=7)
        hud.pack(fill="x")
        tk.Frame(hud_wrap, bg=C["accent3"], height=1).pack(fill="x")

        # Lives
        lives_f = tk.Frame(hud, bg=C["banner"])
        lives_f.pack(side="left", padx=8)
        for i in range(MAX_LIVES):
            tk.Label(lives_f,
                     text="❤" if i < app.lives else "🖤",
                     font=("Segoe UI Emoji",13),
                     bg=C["banner"],
                     fg=C["lives"] if i < app.lives else C["locked"]).pack(side="left")

        # Question counter
        mode_badge = tk.Label(
            hud,
            text=f"Q {idx+1}/{total}",
            font=_retro(10, "bold"),
            bg=C["banner"], fg=C["accent"])
        mode_badge.pack(side="left", padx=4)

        # XP
        tk.Label(hud, text=f"⚡ {app.total_xp_session}",
                 font=_retro(9, "bold"),
                 bg=C["banner"], fg=C["xp"]).pack(side="left", padx=4)

        # Timer
        self._timer_lbl = tk.Label(hud,
                                    text=f"⏱ {self._t_left}s",
                                    font=_retro(12, "bold"),
                                    bg=C["banner"], fg=C["timer_ok"])
        self._timer_lbl.pack(side="right", padx=8)

        # Pause
        pk = tk.Label(hud, text="⏸",
                       font=_retro(12),
                       bg=C["banner"], fg=C["grey"],
                       cursor="hand2")
        pk.pack(side="right", padx=4)
        pk.bind("<Button-1>", lambda e: self._toggle_pause())

        # ── Progress strip ────────────────────────────────────────────────
        pb_bg = tk.Frame(self, bg=C["locked"], height=5)
        pb_bg.pack(fill="x")
        self._pb = tk.Frame(pb_bg, bg=C["accent"], height=5,
                             width=int(WINDOW_W*(idx+1)/total))
        self._pb.place(x=0,y=0)

        # ── Scrollable body ───────────────────────────────────────────────
        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        self._sf  = sf
        inn       = sf.inner
        inn.configure(padx=16)

        diff_c = lvl["difficulty_color"]
        # Difficulty pill
        pill_row = tk.Frame(inn, bg=C["bg"])
        pill_row.pack(fill="x", pady=(10,6))
        pill = tk.Frame(pill_row, bg=diff_c, padx=8, pady=2)
        pill.pack(side="left")
        tk.Label(pill, text=f"  {lvl['difficulty'].upper()}  ",
                 font=_retro(8, "bold"),
                 bg=diff_c, fg=C["bg"]).pack()

        # Question card with neon left accent
        qwrap = tk.Frame(inn, bg=diff_c)
        qwrap.pack(fill="x")
        tk.Frame(qwrap, bg=diff_c, width=3).pack(side="left", fill="y")
        qc = tk.Frame(qwrap, bg=C["card"], padx=14, pady=12,
                      highlightbackground=_darken(diff_c, 0.5),
                      highlightthickness=1)
        qc.pack(side="left", fill="x", expand=True)
        tk.Label(qc, text=q["question"],
                 font=_retro(11, "bold"),
                 bg=C["card"], fg=C["white"],
                 wraplength=356, justify="left").pack(anchor="w")

        tk.Label(inn, text="", bg=C["bg"], height=1).pack()

        # Options — shuffled each time so the correct answer isn't always
        # in the same position
        import random as _r
        shuffled_options = list(q["options"])
        _r.shuffle(shuffled_options)

        self._opts = {}
        _letters = ["A", "B", "C", "D"]
        for _li, opt in enumerate(shuffled_options):
            _letter = _letters[_li] if _li < len(_letters) else "?"
            bf = tk.Frame(inn, bg=C["bg"], pady=2)
            bf.pack(fill="x")
            cv = tk.Canvas(bf, height=52, bg=C["bg"], highlightthickness=0)
            cv.pack(fill="x")
            fnt    = _retro(10)
            fnt_lbl= _retro(11, "bold")
            _col_base = C["card"]

            def draw(cv=cv, text=opt, col=_col_base, letter=_letter):
                cv.delete("all")
                w = cv.winfo_width() or WINDOW_W-32
                # Gradient card body
                col_top = _lerp(col, "#ffffff", 0.18)
                col_bot = _darken(col, 0.75)
                _grad(cv, 2, 2, w-2, 50, col_top, col_bot, steps=16)
                # Left neon accent strip (letter box) — 3D extruded
                acc     = C["accent2"] if col == _col_base else _lerp(col, "#ffffff", 0.3)
                acc_bot = _darken(acc, 0.55)
                # Right-side extrusion shadow (depth)
                cv.create_rectangle(36, 4, 40, 50,
                                     fill=_darken(acc, 0.35), outline="")
                # Bottom extrusion shadow
                cv.create_rectangle(2, 48, 40, 52,
                                     fill=_darken(acc, 0.35), outline="")
                # Main face gradient
                _grad(cv, 2, 2, 36, 50,
                      _lerp(acc, "#ffffff", 0.30), acc_bot, steps=16)
                # Top highlight line
                cv.create_line(3, 3, 35, 3,
                                fill=_lerp(acc, "#ffffff", 0.55), width=1)
                # Left highlight line
                cv.create_line(3, 3, 3, 49,
                                fill=_lerp(acc, "#ffffff", 0.35), width=1)
                # Letter label
                cv.create_text(19, 26, text=letter,
                                fill=C["bg"], font=fnt_lbl)
                # Divider line
                cv.create_line(36, 2, 36, 50, fill=_darken(acc, 0.5), width=1)
                # Answer text
                cv.create_text(w//2 + 18, 26, text=text,
                                fill=C["white"], font=fnt, width=w-56,
                                anchor="center")

            cv.bind("<Configure>", lambda e,c=cv,t=opt,l=_letter,b=_col_base: draw(c,t,b,l))
            cv.bind("<Button-1>",  lambda e,o=opt: self._pick(o))
            cv.bind("<Enter>",  lambda e,c=cv,t=opt,l=_letter: draw(c,t,C["accent3"],l))
            cv.bind("<Leave>",  lambda e,c=cv,t=opt,l=_letter,b=_col_base: draw(c,t,b,l))
            self._opts[opt] = (cv, draw)

        # Timer bar
        self._tbar_bg = tk.Frame(inn, bg=C["locked"], height=6)
        self._tbar_bg.pack(fill="x", pady=(10,4))
        self._tbar = tk.Frame(self._tbar_bg, bg=C["timer_ok"], height=6,
                               width=WINDOW_W-32)
        self._tbar.place(x=0,y=0)

        # Explanation (hidden)
        self._expl_f = tk.Frame(inn, bg=C["card"], padx=14, pady=10)
        self._expl_l = tk.Label(self._expl_f, text="",
                                 font=_retro(10),
                                 bg=C["card"], fg=C["white"],
                                 wraplength=360, justify="left")
        self._expl_l.pack(anchor="w")

        # XP flash (hidden)
        self._xp_f = tk.Frame(inn, bg=C["bg"])
        self._xp_l = tk.Label(self._xp_f, text="",
                               font=_retro(12, "bold"),
                               bg=C["bg"], fg=C["xp"])
        self._xp_l.pack()

        # Next button (hidden)
        self._next_f = tk.Frame(inn, bg=C["bg"], pady=6)
        lbl = "NEXT  ➜" if idx+1 < total else "SEE RESULTS  ✔"
        self._next_btn = Btn(self._next_f, lbl, self._next,
                              bg=C["accent"], fg=C["dark"], w=230, fs=13,
                              pad_bg=C["bg"])
        self._next_btn.pack()

        tk.Label(inn, text="", bg=C["bg"], height=2).pack()
        self._current_q = q

        # Pause overlay (hidden)
        self._pause_overlay = tk.Frame(self, bg=C["dark"])

    # ── Timer tick ────────────────────────────────────────────────────────────
    def _tick(self):
        if self._locked or self._paused:
            self._t_aid = self.after(200, self._tick)
            return
        if self._t_left <= 0:
            self._time_up()
            return
        self._t_left -= 1
        ratio = self._t_left / self._t_total
        # Colour the timer
        tc = (C["timer_ok"] if ratio > 0.5
              else C["timer_warn"] if ratio > 0.25
              else C["timer_bad"])
        self._timer_lbl.configure(text=f"⏱ {self._t_left}s", fg=tc)
        # Timer bar
        try:
            bw = self._tbar_bg.winfo_width() or WINDOW_W-32
            self._tbar.configure(bg=tc, width=int(bw * ratio))
        except Exception:
            pass
        if self._t_left <= 5:
            SFX.play("tick")
        self._t_aid = self.after(1000, self._tick)

    def _time_up(self):
        if self._locked: return
        self._locked = True
        SFX.play("wrong")
        self.app.lives -= 1
        self._show_answer_colors(None)
        self._expl_l.configure(
            text=f"⏱ Time's up!  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(8,4))
        self._xp_l.configure(text="No XP — Time's up!", fg=C["wrong"])
        self._xp_f.pack(pady=(2,4))
        if self.app.lives <= 0:
            self.after(1400, self._go_gameover)
        else:
            self._next_f.pack(pady=(4,16))

    # ── Pause / resume ────────────────────────────────────────────────────────
    def _toggle_pause(self):
        self._paused = not self._paused
        if self._paused:
            self._show_pause()
        else:
            self._hide_pause()

    def _show_pause(self):
        o = self._pause_overlay
        o.place(x=0,y=0, relwidth=1, relheight=1)
        for w in o.winfo_children(): w.destroy()
        tk.Label(o, text="⏸\nPAUSED",
                 font=_retro(28, "bold"),
                 bg=C["dark"], fg=C["accent"],
                 justify="center").pack(expand=True)
        Btn(o, "▶  Resume", self._toggle_pause,
            bg=C["accent"], fg=C["dark"], w=200, fs=14,
            pad_bg=C["dark"]).pack(pady=10)
        Btn(o, "🏠  Quit Level",
            lambda: [self.after_cancel(self._t_aid or 0),
                     self.app.show("level_select")],
            bg=C["card2"], fg=C["white"], w=200, fs=12,
            pad_bg=C["dark"]).pack()

    def _hide_pause(self):
        self._pause_overlay.place_forget()

    # ── Answer pick ───────────────────────────────────────────────────────────
    def _pick(self, option):
        if self._locked or self._paused: return
        self._locked  = True
        elapsed       = time.time() - self._q_start
        half_time     = self._t_total / 2
        is_fast       = elapsed < half_time
        correct       = self._current_q["answer"]
        is_right      = (option == correct)

        # XP calculation
        xp_gained = 0
        if is_right:
            xp_gained += XP_CORRECT
            if is_fast:
                xp_gained += XP_BONUS_FAST
                self.app.fast_answers += 1
            self.app.quiz_score += 1
        else:
            self.app.lives -= 1

        self.app.total_xp_session += xp_gained
        SFX.play("correct" if is_right else "wrong")

        self.app.quiz_answers.append({
            "question":    self._current_q["question"],
            "chosen":      option,
            "correct":     correct,
            "is_right":    is_right,
            "xp":          xp_gained,
            "explanation": self._current_q.get("explanation","")
        })

        self._show_answer_colors(option)

        icon = "✅" if is_right else "❌"
        self._expl_l.configure(
            text=f"{icon}  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(8,4))

        # XP flash
        if xp_gained > 0:
            bonus = f"  +{XP_BONUS_FAST} speed bonus!" if is_fast and is_right else ""
            self._xp_l.configure(text=f"⚡ +{xp_gained} XP{bonus}", fg=C["xp"])
        else:
            self._xp_l.configure(text=f"❤ {self.app.lives}/{MAX_LIVES} lives remaining",
                                   fg=C["lives"])
        self._xp_f.pack(pady=(2,4))

        if not is_right and self.app.lives <= 0:
            self.after(1500, self._go_gameover)
        else:
            self._next_f.pack(pady=(4,16))

    def _show_answer_colors(self, chosen):
        correct = self._current_q["answer"]
        _letters = ["A", "B", "C", "D"]
        for _li, (opt, (cv, draw_fn)) in enumerate(self._opts.items()):
            letter = _letters[_li] if _li < len(_letters) else "?"
            if opt == correct:       col = C["correct"]
            elif opt == chosen:      col = C["wrong"]
            else:                    col = C["locked"]
            draw_fn(cv, opt, col, letter)
            cv.unbind("<Button-1>")
            cv.unbind("<Enter>")
            cv.unbind("<Leave>")

    def _next(self):
        if self._t_aid: self.after_cancel(self._t_aid)
        SFX.play("click")
        self.app.quiz_index += 1
        diff = self.app.chosen_difficulty.lower()
        total = len(self.app.current_level.get(diff, self.app.current_level.get("questions", [])))
        if self.app.quiz_index >= total:
            self.app.show("result")
        else:
            self.app.show("quiz")

    def _go_gameover(self):
        if self._t_aid: self.after_cancel(self._t_aid)
        self.app.show("gameover")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Kahoot Quiz  (colorful 4-tile layout, 20s timer, no difficulty pick)
# ══════════════════════════════════════════════════════════════════════════════
class KahootScreen(tk.Frame):
    """Kahoot-style quiz: 4 big colored tiles, fast 20s timer, speed bonus."""

    # Kahoot-ish colors: red, blue, yellow, green
    _TILE_COLORS = ["#e74c3c", "#3498db", "#f1c416", "#2ecc71"]
    _TILE_ICONS  = ["▲", "■", "●", "◆"]

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app     = app
        self._locked = False
        self._paused = False
        self._t_left = TIMER.get("Kahoot", 20)
        self._t_total= self._t_left
        self._t_aid  = None
        self._q_start= time.time()
        self._build()
        self._tick()

    def _build(self):
        app  = self.app
        lvl  = app.current_level
        idx  = app.quiz_index
        qs   = lvl.get("kahoot", lvl.get("questions", []))
        q    = qs[idx]
        total= len(qs)
        self._current_q = q

        # ── Top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg="#1a1a2e")
        top.pack(fill="x")
        tk.Frame(top, bg="#e74c3c", height=3).pack(fill="x")
        bar = tk.Frame(top, bg="#1a1a2e", pady=8)
        bar.pack(fill="x")

        # Lives
        lf = tk.Frame(bar, bg="#1a1a2e")
        lf.pack(side="left", padx=10)
        for i in range(MAX_LIVES):
            tk.Label(lf, text="❤" if i < app.lives else "🖤",
                     font=("Segoe UI Emoji", 13), bg="#1a1a2e",
                     fg="#e74c3c" if i < app.lives else "#444").pack(side="left")

        tk.Label(bar, text=f"Q {idx+1} / {total}",
                 font=_retro(11, "bold"),
                 bg="#1a1a2e", fg="#ffffff").pack(side="left", padx=8)

        tk.Label(bar, text=f"⚡ {app.total_xp_session}",
                 font=_retro(9, "bold"),
                 bg="#1a1a2e", fg="#f1c416").pack(side="left", padx=4)

        self._timer_lbl = tk.Label(bar, text=f"⏱ {self._t_left}",
                                    font=_retro(14, "bold"),
                                    bg="#1a1a2e", fg="#2ecc71")
        self._timer_lbl.pack(side="right", padx=12)

        # Progress bar
        pb_bg = tk.Frame(self, bg="#2c2c3e", height=6)
        pb_bg.pack(fill="x")
        self._pb = tk.Frame(pb_bg, bg="#e74c3c", height=6,
                             width=int(WINDOW_W*(idx+1)/total))
        self._pb.place(x=0, y=0)

        # ── Question card ─────────────────────────────────────────────────
        qcard = tk.Frame(self, bg="#16213e", pady=20, padx=20)
        qcard.pack(fill="x", pady=0)
        tk.Label(qcard, text=q["question"],
                 font=_retro(13, "bold"),
                 bg="#16213e", fg="#ffffff",
                 wraplength=380, justify="center").pack()

        # Timer ring canvas (circular progress)
        self._timer_cv = tk.Canvas(self, width=60, height=60,
                                    bg=C["bg"], highlightthickness=0)
        self._timer_cv.pack(pady=6)
        self._draw_timer_ring()

        # ── 4 Tile grid ───────────────────────────────────────────────────
        import random as _r
        opts = list(q["options"])
        _r.shuffle(opts)

        self._opts = {}
        grid = tk.Frame(self, bg=C["bg"])
        grid.pack(fill="both", expand=True, padx=10, pady=(0,10))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, opt in enumerate(opts):
            col_i  = self._TILE_COLORS[i % 4]
            icon_i = self._TILE_ICONS[i % 4]
            row_i, col_grid = divmod(i, 2)

            tile_cv = tk.Canvas(grid, height=90, bg=C["bg"],
                                 highlightthickness=0)
            tile_cv.grid(row=row_i, column=col_grid,
                         padx=5, pady=5, sticky="nsew")

            fnt_icon = _retro(16, "bold")
            fnt_text = _retro(10, "bold")

            def draw_tile(cv=tile_cv, text=opt, col=col_i, icon=icon_i):
                cv.delete("all")
                w = cv.winfo_width() or (WINDOW_W//2 - 20)
                # Gradient tile
                col_top = _lerp(col, "#ffffff", 0.20)
                col_bot = _darken(col, 0.65)
                _grad(cv, 2, 2, w-2, 88, col_top, col_bot, steps=20)
                # Highlight edges
                cv.create_line(2, 2, w-2, 2, fill=_lerp(col,"#ffffff",0.4), width=2)
                cv.create_line(2, 2, 2, 88,  fill=_lerp(col,"#ffffff",0.3), width=2)
                # Drop shadow
                cv.create_line(w-2, 2, w-2, 88, fill=_darken(col,0.4), width=2)
                cv.create_line(2, 88, w-2, 88,  fill=_darken(col,0.4), width=2)
                # Icon top-left
                cv.create_text(20, 20, text=icon, font=fnt_icon,
                                fill="#ffffff")
                # Answer text centered
                cv.create_text(w//2, 55, text=text, font=fnt_text,
                                fill="#ffffff", width=w-16, anchor="center")

            draw_tile()
            tile_cv.bind("<Configure>", lambda e, c=tile_cv, t=opt, cl=col_i, ic=icon_i:
                         draw_tile(c, t, cl, ic))
            tile_cv.bind("<Button-1>",  lambda e, o=opt: self._pick(o))
            tile_cv.bind("<Enter>",     lambda e, c=tile_cv, t=opt, cl=col_i, ic=icon_i:
                         self._hover_tile(c, t, cl, ic, True))
            tile_cv.bind("<Leave>",     lambda e, c=tile_cv, t=opt, cl=col_i, ic=icon_i:
                         self._hover_tile(c, t, cl, ic, False))
            self._opts[opt] = (tile_cv, draw_tile)

        # Explanation label (hidden)
        self._expl_f = tk.Frame(self, bg="#16213e", padx=16, pady=10)
        self._expl_l = tk.Label(self._expl_f, text="",
                                 font=_retro(10),
                                 bg="#16213e", fg="#ffffff",
                                 wraplength=370, justify="center")
        self._expl_l.pack()

        # XP label (hidden)
        self._xp_f = tk.Frame(self, bg=C["bg"])
        self._xp_l = tk.Label(self._xp_f, text="",
                               font=_retro(12, "bold"),
                               bg=C["bg"], fg="#f1c416")
        self._xp_l.pack()

        # Next button (hidden)
        self._next_f = tk.Frame(self, bg=C["bg"], pady=6)
        lbl = "NEXT  ➜" if idx+1 < total else "SEE RESULTS  ✔"
        Btn(self._next_f, lbl, self._next,
            bg="#e74c3c", fg="#ffffff", w=240, fs=13,
            pad_bg=C["bg"]).pack()

    def _draw_timer_ring(self):
        cv = self._timer_cv
        cv.delete("all")
        ratio = self._t_left / (self._t_total or 1)
        col = C["timer_ok"] if ratio > 0.5 else C["timer_warn"] if ratio > 0.25 else C["timer_bad"]
        # Background ring
        cv.create_oval(5, 5, 55, 55, outline="#333", width=5, fill=C["bg"])
        # Progress arc
        extent = int(-360 * ratio)
        cv.create_arc(5, 5, 55, 55, start=90, extent=extent,
                       outline=col, width=5, style="arc")
        # Number
        cv.create_text(30, 30, text=str(self._t_left),
                        font=_retro(12, "bold"), fill=col)

    def _hover_tile(self, cv, text, col, icon, hovering):
        cv.delete("all")
        w = cv.winfo_width() or (WINDOW_W//2 - 20)
        c = _lerp(col, "#ffffff", 0.30) if hovering else col
        col_top = _lerp(c, "#ffffff", 0.20)
        col_bot = _darken(c, 0.65)
        _grad(cv, 2, 2, w-2, 88, col_top, col_bot, steps=20)
        cv.create_line(2, 2, w-2, 2, fill=_lerp(c,"#ffffff",0.4), width=2)
        cv.create_line(2, 2, 2, 88,  fill=_lerp(c,"#ffffff",0.3), width=2)
        cv.create_line(w-2, 2, w-2, 88, fill=_darken(c,0.4), width=2)
        cv.create_line(2, 88, w-2, 88,  fill=_darken(c,0.4), width=2)
        cv.create_text(20, 20, text=icon, font=_retro(16,"bold"), fill="#ffffff")
        cv.create_text(w//2, 55, text=text, font=_retro(10,"bold"),
                        fill="#ffffff", width=w-16, anchor="center")

    def _tick(self):
        if self._locked or self._paused:
            self._t_aid = self.after(200, self._tick)
            return
        if self._t_left <= 0:
            self._time_up()
            return
        self._t_left -= 1
        tc = C["timer_ok"] if self._t_left/self._t_total > 0.5 else \
             C["timer_warn"] if self._t_left/self._t_total > 0.25 else C["timer_bad"]
        self._timer_lbl.configure(text=f"⏱ {self._t_left}", fg=tc)
        self._draw_timer_ring()
        if self._t_left <= 5:
            SFX.play("tick")
        self._t_aid = self.after(1000, self._tick)

    def _time_up(self):
        if self._locked: return
        self._locked = True
        SFX.play("wrong")
        self.app.lives -= 1
        self._reveal_answer(None)
        self._expl_l.configure(text=f"⏱ Time's up!  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(4,4))
        self._xp_l.configure(text="No XP — Time's up!", fg=C["wrong"])
        self._xp_f.pack(pady=(2,4))
        if self.app.lives <= 0:
            self.after(1400, lambda: self.app.show("gameover"))
        else:
            self._next_f.pack(pady=(2,8))

    def _pick(self, option):
        if self._locked or self._paused: return
        self._locked = True
        elapsed  = time.time() - self._q_start
        is_fast  = elapsed < (self._t_total / 2)
        correct  = self._current_q["answer"]
        is_right = (option == correct)

        xp_gained = 0
        if is_right:
            xp_gained += XP_CORRECT
            if is_fast:
                xp_gained += XP_BONUS_FAST
                self.app.fast_answers += 1
            self.app.quiz_score += 1
        else:
            self.app.lives -= 1

        self.app.total_xp_session += xp_gained
        SFX.play("correct" if is_right else "wrong")
        self.app.quiz_answers.append({
            "question": self._current_q["question"],
            "chosen": option, "correct": correct,
            "is_right": is_right, "xp": xp_gained,
            "explanation": self._current_q.get("explanation","")
        })

        self._reveal_answer(option)
        icon = "✅" if is_right else "❌"
        self._expl_l.configure(text=f"{icon}  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(4,4))
        bonus = f"  +{XP_BONUS_FAST} speed!" if is_fast and is_right else ""
        self._xp_l.configure(
            text=f"⚡ +{xp_gained} XP{bonus}" if xp_gained > 0
            else f"❤ {self.app.lives}/{MAX_LIVES} lives",
            fg="#f1c416" if xp_gained > 0 else C["lives"])
        self._xp_f.pack(pady=(2,4))
        if not is_right and self.app.lives <= 0:
            self.after(1500, lambda: self.app.show("gameover"))
        else:
            self._next_f.pack(pady=(2,8))

    def _reveal_answer(self, chosen):
        correct = self._current_q["answer"]
        for opt, (cv, draw_fn) in self._opts.items():
            if opt == correct:    col = C["correct"]
            elif opt == chosen:   col = C["wrong"]
            else:                 col = "#444444"
            w = cv.winfo_width() or (WINDOW_W//2 - 20)
            icon = self._TILE_ICONS[list(self._opts.keys()).index(opt) % 4]
            cv.delete("all")
            _grad(cv, 2, 2, w-2, 88,
                  _lerp(col,"#ffffff",0.18), _darken(col,0.65), steps=20)
            cv.create_text(20, 20, text=icon, font=_retro(16,"bold"), fill="#ffffff")
            cv.create_text(w//2, 55, text=opt, font=_retro(10,"bold"),
                            fill="#ffffff", width=w-16, anchor="center")
            if opt == correct:
                cv.create_text(w-14, 14, text="✓", font=_retro(14,"bold"), fill="#ffffff")
            cv.unbind("<Button-1>")
            cv.unbind("<Enter>")
            cv.unbind("<Leave>")

    def _next(self):
        if self._t_aid: self.after_cancel(self._t_aid)
        SFX.play("click")
        self.app.quiz_index += 1
        total = len(self.app.current_level.get("kahoot",
                    self.app.current_level.get("questions", [])))
        if self.app.quiz_index >= total:
            self.app.show("result")
        else:
            self.app.show("kahoot")

    def _toggle_pause(self): pass   # no pause in Kahoot mode


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Myth or Fact Quiz  (2 big buttons: MYTH / FACT)
# ══════════════════════════════════════════════════════════════════════════════
class MythFactScreen(tk.Frame):
    """Myth-or-Fact quiz: each question shows only MYTH and FACT buttons."""

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app     = app
        self._locked = False
        self._t_left = 25
        self._t_total= 25
        self._t_aid  = None
        self._q_start= time.time()
        self._build()
        self._tick()

    def _build(self):
        app  = self.app
        lvl  = app.current_level
        idx  = app.quiz_index
        qs   = lvl.get("myth_fact", lvl.get("questions", []))
        q    = qs[idx]
        total= len(qs)
        self._current_q = q

        # ── Top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg="#1a0a2e")
        top.pack(fill="x")
        tk.Frame(top, bg="#8e44ad", height=3).pack(fill="x")
        bar = tk.Frame(top, bg="#1a0a2e", pady=8)
        bar.pack(fill="x")

        lf = tk.Frame(bar, bg="#1a0a2e")
        lf.pack(side="left", padx=10)
        for i in range(MAX_LIVES):
            tk.Label(lf, text="❤" if i < app.lives else "🖤",
                     font=("Segoe UI Emoji", 13), bg="#1a0a2e",
                     fg="#e74c3c" if i < app.lives else "#444").pack(side="left")

        tk.Label(bar, text=f"🧠  {idx+1} / {total}",
                 font=_retro(11, "bold"),
                 bg="#1a0a2e", fg="#ffffff").pack(side="left", padx=8)

        tk.Label(bar, text=f"⚡ {app.total_xp_session}",
                 font=_retro(9, "bold"),
                 bg="#1a0a2e", fg="#d966ff").pack(side="left", padx=4)

        self._timer_lbl = tk.Label(bar, text=f"⏱ {self._t_left}",
                                    font=_retro(14, "bold"),
                                    bg="#1a0a2e", fg="#d966ff")
        self._timer_lbl.pack(side="right", padx=12)

        # Progress bar
        pb_bg = tk.Frame(self, bg="#2c1a3e", height=6)
        pb_bg.pack(fill="x")
        self._pb = tk.Frame(pb_bg, bg="#8e44ad", height=6,
                             width=int(WINDOW_W*(idx+1)/total))
        self._pb.place(x=0, y=0)

        # ── Statement card ────────────────────────────────────────────────
        qcard = tk.Frame(self, bg="#0d0d1a", pady=24, padx=20)
        qcard.pack(fill="x")
        tk.Label(qcard, text="📋  Is this a MYTH or a FACT?",
                 font=_retro(10, "bold"),
                 bg="#0d0d1a", fg="#8e44ad").pack(pady=(0,8))
        tk.Label(qcard, text=q["question"],
                 font=_retro(12, "bold"),
                 bg="#0d0d1a", fg="#ffffff",
                 wraplength=380, justify="center").pack()

        # ── MYTH / FACT buttons ────────────────────────────────────────────
        btn_row = tk.Frame(self, bg=C["bg"])
        btn_row.pack(expand=True, fill="both", padx=16, pady=20)
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        btn_row.rowconfigure(0, weight=1)

        for col_i, (label, color) in enumerate([("MYTH", "#e74c3c"),
                                                  ("FACT", "#2ecc71")]):
            cv = tk.Canvas(btn_row, bg=C["bg"], highlightthickness=0)
            cv.grid(row=0, column=col_i, padx=8, pady=8, sticky="nsew")
            fnt_big  = _retro(22, "bold")
            fnt_sub  = _retro(9)

            def draw_btn(cv=cv, lbl=label, col=color):
                cv.delete("all")
                w = cv.winfo_width() or 180
                h = cv.winfo_height() or 160
                col_top = _lerp(col, "#ffffff", 0.22)
                col_bot = _darken(col, 0.60)
                _grad(cv, 3, 3, w-3, h-3, col_top, col_bot, steps=24)
                # Bright edges
                cv.create_line(3, 3, w-3, 3, fill=_lerp(col,"#ffffff",0.5), width=2)
                cv.create_line(3, 3, 3, h-3, fill=_lerp(col,"#ffffff",0.4), width=2)
                cv.create_line(w-3, 3, w-3, h-3, fill=_darken(col,0.4), width=2)
                cv.create_line(3, h-3, w-3, h-3, fill=_darken(col,0.4), width=2)
                # Emoji + label
                emoji = "❌" if lbl == "MYTH" else "✅"
                cv.create_text(w//2, h//2 - 20, text=emoji,
                                font=("Segoe UI Emoji", 28))
                cv.create_text(w//2, h//2 + 22, text=lbl,
                                font=fnt_big, fill="#ffffff")

            draw_btn()
            cv.bind("<Configure>", lambda e, c=cv, l=label, col=color: draw_btn(c, l, col))
            cv.bind("<Button-1>",  lambda e, ans=label: self._pick(ans))
            cv.bind("<Enter>",     lambda e, c=cv, l=label, col=color:
                    self._draw_hover(c, l, col, True))
            cv.bind("<Leave>",     lambda e, c=cv, l=label, col=color: draw_btn(c, l, col))
            setattr(self, f"_btn_{label.lower()}", (cv, draw_btn))

        # Explanation & next (hidden)
        self._expl_f = tk.Frame(self, bg="#0d0d1a", padx=16, pady=10)
        self._expl_l = tk.Label(self._expl_f, text="",
                                 font=_retro(10),
                                 bg="#0d0d1a", fg="#ffffff",
                                 wraplength=370, justify="center")
        self._expl_l.pack()

        self._xp_f = tk.Frame(self, bg=C["bg"])
        self._xp_l = tk.Label(self._xp_f, text="",
                               font=_retro(12, "bold"),
                               bg=C["bg"], fg="#d966ff")
        self._xp_l.pack()

        self._next_f = tk.Frame(self, bg=C["bg"], pady=6)
        lbl_n = "NEXT  ➜" if idx+1 < total else "SEE RESULTS  ✔"
        Btn(self._next_f, lbl_n, self._next,
            bg="#8e44ad", fg="#ffffff", w=240, fs=13,
            pad_bg=C["bg"]).pack()

    def _draw_hover(self, cv, label, col, hover):
        cv.delete("all")
        col2 = _lerp(col, "#ffffff", 0.30) if hover else col
        w = cv.winfo_width() or 180
        h = cv.winfo_height() or 160
        _grad(cv, 3, 3, w-3, h-3,
              _lerp(col2,"#ffffff",0.22), _darken(col2,0.60), steps=24)
        cv.create_line(3, 3, w-3, 3, fill=_lerp(col2,"#ffffff",0.5), width=2)
        cv.create_line(3, 3, 3, h-3, fill=_lerp(col2,"#ffffff",0.4), width=2)
        cv.create_line(w-3, 3, w-3, h-3, fill=_darken(col2,0.4), width=2)
        cv.create_line(3, h-3, w-3, h-3, fill=_darken(col2,0.4), width=2)
        emoji = "❌" if label == "MYTH" else "✅"
        cv.create_text(w//2, h//2 - 20, text=emoji,
                        font=("Segoe UI Emoji", 28))
        cv.create_text(w//2, h//2 + 22, text=label,
                        font=_retro(22,"bold"), fill="#ffffff")

    def _tick(self):
        if self._locked:
            self._t_aid = self.after(200, self._tick)
            return
        if self._t_left <= 0:
            self._time_up(); return
        self._t_left -= 1
        tc = C["timer_ok"] if self._t_left/self._t_total > 0.5 else \
             C["timer_warn"] if self._t_left/self._t_total > 0.25 else C["timer_bad"]
        self._timer_lbl.configure(text=f"⏱ {self._t_left}", fg=tc)
        if self._t_left <= 5: SFX.play("tick")
        self._t_aid = self.after(1000, self._tick)

    def _time_up(self):
        if self._locked: return
        self._locked = True
        SFX.play("wrong")
        self.app.lives -= 1
        self._expl_l.configure(
            text=f"⏱ Time's up!  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(4,4))
        self._xp_l.configure(text="No XP — Time's up!", fg=C["wrong"])
        self._xp_f.pack(pady=(2,4))
        if self.app.lives <= 0:
            self.after(1400, lambda: self.app.show("gameover"))
        else:
            self._next_f.pack(pady=(2,8))

    def _pick(self, answer):
        if self._locked: return
        self._locked = True
        elapsed  = time.time() - self._q_start
        is_fast  = elapsed < (self._t_total / 2)
        correct  = self._current_q["answer"]   # "MYTH" or "FACT"
        is_right = (answer == correct)

        xp_gained = 0
        if is_right:
            xp_gained += XP_CORRECT
            if is_fast:
                xp_gained += XP_BONUS_FAST
                self.app.fast_answers += 1
            self.app.quiz_score += 1
        else:
            self.app.lives -= 1

        self.app.total_xp_session += xp_gained
        SFX.play("correct" if is_right else "wrong")
        self.app.quiz_answers.append({
            "question": self._current_q["question"],
            "chosen": answer, "correct": correct,
            "is_right": is_right, "xp": xp_gained,
            "explanation": self._current_q.get("explanation","")
        })

        # Flash the buttons
        for lbl, col in [("MYTH","#e74c3c"), ("FACT","#2ecc71")]:
            cv, _ = getattr(self, f"_btn_{lbl.lower()}")
            final_col = C["correct"] if lbl == correct else \
                        (C["wrong"] if lbl == answer else "#444444")
            w = cv.winfo_width() or 180
            h = cv.winfo_height() or 160
            cv.delete("all")
            _grad(cv, 3, 3, w-3, h-3,
                  _lerp(final_col,"#ffffff",0.18), _darken(final_col,0.65), steps=20)
            cv.create_line(3, 3, w-3, 3, fill=_lerp(final_col,"#ffffff",0.4), width=2)
            cv.create_line(3, 3, 3, h-3, fill=_lerp(final_col,"#ffffff",0.3), width=2)
            emoji = "❌" if lbl == "MYTH" else "✅"
            cv.create_text(w//2, h//2 - 20, text=emoji,
                            font=("Segoe UI Emoji", 28))
            cv.create_text(w//2, h//2 + 22, text=lbl,
                            font=_retro(22,"bold"), fill="#ffffff")
            if lbl == correct:
                cv.create_text(w//2, h-18, text="◀ CORRECT",
                                font=_retro(8,"bold"), fill="#ffffff")
            cv.unbind("<Button-1>")
            cv.unbind("<Enter>")
            cv.unbind("<Leave>")

        icon = "✅" if is_right else "❌"
        self._expl_l.configure(
            text=f"{icon}  {self._current_q.get('explanation','')}")
        self._expl_f.pack(fill="x", pady=(4,4))
        self._xp_l.configure(
            text=f"⚡ +{xp_gained} XP" if xp_gained > 0
            else f"❤ {self.app.lives}/{MAX_LIVES} lives",
            fg="#d966ff" if xp_gained > 0 else C["lives"])
        self._xp_f.pack(pady=(2,4))
        if not is_right and self.app.lives <= 0:
            self.after(1500, lambda: self.app.show("gameover"))
        else:
            self._next_f.pack(pady=(2,8))

    def _next(self):
        if self._t_aid: self.after_cancel(self._t_aid)
        SFX.play("click")
        self.app.quiz_index += 1
        total = len(self.app.current_level.get("myth_fact",
                    self.app.current_level.get("questions", [])))
        if self.app.quiz_index >= total:
            self.app.show("result")
        else:
            self.app.show("myth_fact")


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Hangman  (Coming Soon placeholder)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Hangman
# ══════════════════════════════════════════════════════════════════════════════
class HangmanScreen(tk.Frame):
    _MAX_WRONG = 6   # stages 0-6 (6 = fully hanged)
    _ALPHABET  = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app

        # Load word list
        self._words   = app.current_level.get("hangman", [])
        self._total   = len(self._words)
        self._widx    = app.quiz_index   # current word index
        self._wrong   = 0
        self._guessed = set()
        self._won     = False

        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        entry = self._words[self._widx]
        self._word  = entry["word"].upper()
        self._hint  = entry["hint"]
        self._wrong = 0
        self._guessed = set()
        self._won   = False

        # Clear any previous widgets
        for w in self.winfo_children():
            w.destroy()

        # ── Top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg="#0a1628")
        top.pack(fill="x")
        tk.Frame(top, bg="#3498db", height=3).pack(fill="x")
        bar = tk.Frame(top, bg="#0a1628", pady=7)
        bar.pack(fill="x")
        tk.Frame(top, bg="#1a3a5c", height=1).pack(fill="x")

        tk.Label(bar, text="🎯  HANGMAN",
                 font=_retro(13, "bold"),
                 bg="#0a1628", fg="#3498db").pack(side="left", padx=10)
        tk.Label(bar, text=f"Word {self._widx+1} / {self._total}",
                 font=_retro(10),
                 bg="#0a1628", fg="#aaaaaa").pack(side="left", padx=6)
        tk.Label(bar, text=f"⚡ {self.app.total_xp_session}",
                 font=_retro(10, "bold"),
                 bg="#0a1628", fg=C["xp"]).pack(side="left", padx=4)
        Btn(bar, "🏠",
            lambda: self.app.show("level_select"),
            bg="#1a3a5c", fg="#ffffff", w=46, fs=10,
            pad_bg="#0a1628").pack(side="right", padx=8)

        # Progress bar
        pb_bg = tk.Frame(self, bg="#1a2a3a", height=5)
        pb_bg.pack(fill="x")
        tk.Frame(pb_bg, bg="#3498db", height=5,
                 width=int(WINDOW_W * (self._widx + 1) / self._total)
                 ).place(x=0, y=0)

        # ── Gallows canvas ────────────────────────────────────────────────
        self._gal_cv = tk.Canvas(self, width=WINDOW_W, height=200,
                                  bg="#0d1b2a", highlightthickness=0)
        self._gal_cv.pack(fill="x")
        self._draw_gallows()

        # ── Hint card ─────────────────────────────────────────────────────
        hint_f = tk.Frame(self, bg="#0f2035", padx=16, pady=8)
        hint_f.pack(fill="x")
        tk.Label(hint_f, text="💡  Hint:",
                 font=_retro(9, "bold"),
                 bg="#0f2035", fg="#3498db").pack(anchor="w")
        tk.Label(hint_f, text=self._hint,
                 font=_retro(10),
                 bg="#0f2035", fg="#ccddee",
                 wraplength=380, justify="left").pack(anchor="w")

        # ── Word blanks ───────────────────────────────────────────────────
        blanks_f = tk.Frame(self, bg=C["bg"], pady=12)
        blanks_f.pack()
        self._letter_labels = {}
        for ch in self._word:
            col_f = tk.Frame(blanks_f, bg=C["bg"])
            col_f.pack(side="left", padx=3)
            lbl = tk.Label(col_f, text=" ",
                            font=_retro(18, "bold"),
                            bg=C["bg"], fg="#3498db",
                            width=2, anchor="center")
            lbl.pack()
            tk.Frame(col_f, bg="#3498db", height=2, width=22).pack()
            self._letter_labels[id(lbl)] = (lbl, ch)

        # ── Wrong guesses display ─────────────────────────────────────────
        wrong_f = tk.Frame(self, bg=C["bg"])
        wrong_f.pack()
        self._wrong_lbl = tk.Label(wrong_f,
                                    text=f"Wrong guesses: 0 / {self._MAX_WRONG}",
                                    font=_retro(9),
                                    bg=C["bg"], fg=C["grey"])
        self._wrong_lbl.pack()
        self._wrong_letters_lbl = tk.Label(wrong_f, text="",
                                            font=_retro(9, "bold"),
                                            bg=C["bg"], fg=C["wrong"])
        self._wrong_letters_lbl.pack()

        # ── Keyboard ──────────────────────────────────────────────────────
        kb_f = tk.Frame(self, bg=C["bg"])
        kb_f.pack(pady=(8, 4))
        self._key_btns = {}
        rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_str in rows:
            row_f = tk.Frame(kb_f, bg=C["bg"])
            row_f.pack(pady=2)
            for letter in row_str:
                cv = tk.Canvas(row_f, width=34, height=34,
                                bg=C["bg"], highlightthickness=0)
                cv.pack(side="left", padx=1)
                self._draw_key(cv, letter, active=True)
                cv.bind("<Button-1>", lambda e, l=letter, c=cv: self._guess(l, c))
                self._key_btns[letter] = cv

        # ── Status label (hidden until end) ───────────────────────────────
        self._status_f = tk.Frame(self, bg=C["bg"])
        self._status_f.pack()

    # ── Draw gallows ──────────────────────────────────────────────────────────
    def _draw_gallows(self):
        cv  = self._gal_cv
        cv.delete("all")
        w, h = WINDOW_W, 200
        col = "#4a8abf"   # steel blue structure

        # Base
        cv.create_line(w//2-80, h-10, w//2+80, h-10, fill=col, width=4)
        # Pole
        cv.create_line(w//2-40, h-10, w//2-40, 10,  fill=col, width=4)
        # Top bar
        cv.create_line(w//2-40, 10,   w//2+40, 10,  fill=col, width=4)
        # Rope
        cv.create_line(w//2+40, 10,   w//2+40, 36,  fill="#8899aa", width=2)

        n = self._wrong
        cx = w//2+40

        # Stage 1 — head
        if n >= 1:
            cv.create_oval(cx-16, 36, cx+16, 68, outline="#e0e0e0", width=2)
        # Stage 2 — body
        if n >= 2:
            cv.create_line(cx, 68, cx, 128, fill="#e0e0e0", width=2)
        # Stage 3 — left arm
        if n >= 3:
            cv.create_line(cx, 82, cx-28, 108, fill="#e0e0e0", width=2)
        # Stage 4 — right arm
        if n >= 4:
            cv.create_line(cx, 82, cx+28, 108, fill="#e0e0e0", width=2)
        # Stage 5 — left leg
        if n >= 5:
            cv.create_line(cx, 128, cx-28, 165, fill="#e0e0e0", width=2)
        # Stage 6 — right leg
        if n >= 6:
            cv.create_line(cx, 128, cx+28, 165, fill="#e0e0e0", width=2)

        # Wrong count indicator dots
        for i in range(self._MAX_WRONG):
            fill = C["wrong"] if i < n else "#1a2a3a"
            cv.create_oval(w//2-80 + i*18, h-30,
                            w//2-62 + i*18, h-12,
                            fill=fill, outline="")

    # ── Draw keyboard key ─────────────────────────────────────────────────────
    def _draw_key(self, cv, letter, active=True, correct=False, wrong=False):
        cv.delete("all")
        if correct:
            bg_col, fg_col = C["correct"], C["bg"]
        elif wrong:
            bg_col, fg_col = "#333333", "#555555"
        elif active:
            bg_col, fg_col = "#1a3a5c", "#ffffff"
        else:
            bg_col, fg_col = "#0d1b2a", "#334455"

        col_top = _lerp(bg_col, "#ffffff", 0.18)
        col_bot = _darken(bg_col, 0.70)
        _grad(cv, 2, 2, 32, 32, col_top, col_bot, steps=12)
        cv.create_rectangle(2, 2, 32, 32, outline=_lerp(bg_col,"#ffffff",0.2), fill="")
        cv.create_text(17, 17, text=letter,
                        font=_retro(10, "bold"), fill=fg_col)

    # ── Guess a letter ────────────────────────────────────────────────────────
    def _guess(self, letter, cv):
        if letter in self._guessed or self._won:
            return
        self._guessed.add(letter)
        SFX.play("click")

        if letter in self._word:
            # Correct — reveal letter on blanks
            SFX.play("correct")
            self._draw_key(cv, letter, correct=True)
            for lbl_id, (lbl, ch) in self._letter_labels.items():
                if ch == letter:
                    lbl.configure(text=letter, fg="#3498db")
            # Check win
            if all(ch in self._guessed for ch in self._word):
                self._on_win()
        else:
            # Wrong
            SFX.play("wrong")
            self._wrong += 1
            self._draw_key(cv, letter, wrong=True)
            self._draw_gallows()
            self._wrong_lbl.configure(
                text=f"Wrong guesses: {self._wrong} / {self._MAX_WRONG}")
            wrong_so_far = " ".join(sorted(
                l for l in self._guessed if l not in self._word))
            self._wrong_letters_lbl.configure(text=wrong_so_far)
            if self._wrong >= self._MAX_WRONG:
                self._on_lose()

    # ── Win ───────────────────────────────────────────────────────────────────
    def _on_win(self):
        self._won = True
        xp = 15 - self._wrong * 2   # more XP for fewer wrong guesses
        xp = max(xp, 2)
        self.app.total_xp_session += xp
        self.app.quiz_score += 1
        self.app.quiz_answers.append({
            "question": f"Hangman: {self._word}",
            "chosen": self._word, "correct": self._word,
            "is_right": True, "xp": xp,
            "explanation": self._hint
        })

        for w in self._status_f.winfo_children():
            w.destroy()
        tk.Label(self._status_f, text="✅  CORRECT!",
                 font=_retro(16, "bold"),
                 bg=C["bg"], fg=C["correct"]).pack(pady=(6, 2))
        tk.Label(self._status_f, text=f"⚡ +{xp} XP",
                 font=_retro(11, "bold"),
                 bg=C["bg"], fg=C["xp"]).pack()

        lbl = "NEXT WORD  ➜" if self._widx + 1 < self._total else "SEE RESULTS  ✔"
        Btn(self._status_f, lbl, self._next,
            bg="#3498db", fg="#ffffff", w=240, fs=13,
            pad_bg=C["bg"]).pack(pady=(10, 4))

    # ── Lose ──────────────────────────────────────────────────────────────────
    def _on_lose(self):
        self._won = False
        self.app.lives -= 1
        self.app.quiz_answers.append({
            "question": f"Hangman: {self._word}",
            "chosen": "", "correct": self._word,
            "is_right": False, "xp": 0,
            "explanation": self._hint
        })

        # Reveal full word
        for lbl_id, (lbl, ch) in self._letter_labels.items():
            if ch not in self._guessed:
                lbl.configure(text=ch, fg=C["wrong"])

        for w in self._status_f.winfo_children():
            w.destroy()
        tk.Label(self._status_f, text=f"❌  The word was: {self._word}",
                 font=_retro(13, "bold"),
                 bg=C["bg"], fg=C["wrong"]).pack(pady=(6, 2))
        tk.Label(self._status_f, text=f"❤ {self.app.lives}/{MAX_LIVES} lives left",
                 font=_retro(10),
                 bg=C["bg"], fg=C["lives"]).pack()

        if self.app.lives <= 0:
            self.after(1500, lambda: self.app.show("gameover"))
        else:
            lbl = "NEXT WORD  ➜" if self._widx + 1 < self._total else "SEE RESULTS  ✔"
            Btn(self._status_f, lbl, self._next,
                bg=C["card2"], fg=C["white"], w=240, fs=13,
                pad_bg=C["bg"]).pack(pady=(10, 4))

    # ── Next word ─────────────────────────────────────────────────────────────
    def _next(self):
        SFX.play("click")
        self.app.quiz_index += 1
        if self.app.quiz_index >= self._total:
            self.app.show("result")
        else:
            self._widx += 1
            self._build()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Jigsaw  (Coming Soon placeholder)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Jigsaw Puzzle  (birthpill.webp image, 4×3 grid, click-to-place)
# ══════════════════════════════════════════════════════════════════════════════
class JigsawScreen(tk.Frame):
    _COLS   = 4
    _ROWS   = 3
    _IMG_W  = 400   # display width of the puzzle area
    _IMG_H  = 225   # display height (keeps ~16:9 ratio)
    _PAD    = 2     # gap between pieces

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._selected = None      # index of currently selected piece
        self._placed   = {}        # slot_idx -> piece_idx (correct when piece_idx == slot_idx)
        self._solved   = False
        self._photos   = []        # keep refs to avoid GC
        self._piece_btns = {}      # piece_idx -> canvas widget (tray)
        self._slot_cvs   = {}      # slot_idx  -> canvas widget (board)
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        import random as _r
        from PIL import Image, ImageTk, ImageDraw

        lvl = self.app.current_level

        # ── Top bar ───────────────────────────────────────────────────────
        top = tk.Frame(self, bg="#1a0f00")
        top.pack(fill="x")
        tk.Frame(top, bg="#e67e22", height=3).pack(fill="x")
        bar = tk.Frame(top, bg="#1a0f00", pady=7)
        bar.pack(fill="x")
        tk.Frame(top, bg="#6e3a00", height=1).pack(fill="x")
        tk.Label(bar, text="🧩  JIGSAW PUZZLE",
                 font=_retro(13, "bold"),
                 bg="#1a0f00", fg="#e67e22").pack(side="left", padx=10)
        tk.Label(bar, text=lvl["title"],
                 font=_retro(9),
                 bg="#1a0f00", fg="#aaaaaa").pack(side="left", padx=4)
        Btn(bar, "🏠",
            lambda: self.app.show("level_select"),
            bg="#6e3a00", fg="#ffffff", w=46, fs=10,
            pad_bg="#1a0f00").pack(side="right", padx=8)

        # ── Load & slice image ─────────────────────────────────────────────
        img_path = os.path.join(os.path.dirname(__file__), "images", "birthpill.webp")
        img = Image.open(img_path).convert("RGB")
        img = img.resize((self._IMG_W, self._IMG_H), Image.LANCZOS)

        pw = self._IMG_W  // self._COLS   # piece width
        ph = self._IMG_H  // self._ROWS   # piece height

        self._pw = pw
        self._ph = ph

        pieces_orig = []   # PhotoImage for each piece (correct order)
        for r in range(self._ROWS):
            for c in range(self._COLS):
                box   = (c*pw, r*ph, (c+1)*pw, (r+1)*ph)
                piece = img.crop(box)
                # Add a subtle border so pieces are distinguishable
                draw  = ImageDraw.Draw(piece)
                draw.rectangle([0,0,pw-1,ph-1], outline="#e67e22", width=2)
                photo = ImageTk.PhotoImage(piece)
                self._photos.append(photo)
                pieces_orig.append(photo)

        # Shuffle piece order for the tray
        self._n       = self._COLS * self._ROWS
        self._order   = list(range(self._n))   # piece_idx → original slot
        _r.shuffle(self._order)

        # ── Puzzle board (target slots) ───────────────────────────────────
        board_lbl = tk.Label(self, text="🎯  Place pieces here:",
                              font=_retro(9, "bold"),
                              bg=C["bg"], fg="#e67e22")
        board_lbl.pack(pady=(8, 2))

        board_f = tk.Frame(self, bg="#0a0a0a")
        board_f.pack()

        for slot_idx in range(self._n):
            r, c = divmod(slot_idx, self._COLS)
            cv = tk.Canvas(board_f, width=pw, height=ph,
                            bg="#1a1a1a", highlightthickness=1,
                            highlightbackground="#333333")
            cv.grid(row=r, column=c, padx=1, pady=1)
            # Draw slot number hint
            cv.create_text(pw//2, ph//2, text=str(slot_idx+1),
                            font=_retro(8), fill="#333333")
            cv.bind("<Button-1>", lambda e, s=slot_idx: self._place(s))
            self._slot_cvs[slot_idx] = cv

        # ── Piece tray (shuffled pieces to pick from) ─────────────────────
        tray_lbl = tk.Label(self, text="📦  Pick a piece:",
                             font=_retro(9, "bold"),
                             bg=C["bg"], fg=C["grey"])
        tray_lbl.pack(pady=(8, 2))

        tray_f = tk.Frame(self, bg=C["bg"])
        tray_f.pack()

        tray_cols = self._COLS
        for tray_i, piece_idx in enumerate(self._order):
            r, c = divmod(tray_i, tray_cols)
            cv = tk.Canvas(tray_f, width=pw, height=ph,
                            bg=C["card"], highlightthickness=1,
                            highlightbackground=C["accent3"])
            cv.grid(row=r, column=c, padx=1, pady=1)
            cv.create_image(0, 0, anchor="nw",
                             image=pieces_orig[piece_idx])
            cv.bind("<Button-1>", lambda e, pi=piece_idx, ti=tray_i:
                    self._select(pi, ti))
            self._piece_btns[piece_idx] = cv

        self._pieces_orig = pieces_orig

        # Status bar
        self._status_lbl = tk.Label(self, text="Click a piece, then click its slot on the board.",
                                     font=_retro(9),
                                     bg=C["bg"], fg=C["grey"],
                                     wraplength=380, justify="center")
        self._status_lbl.pack(pady=(6, 2))

        self._done_f = tk.Frame(self, bg=C["bg"])
        self._done_f.pack()

    # ── Select a piece from the tray ──────────────────────────────────────────
    def _select(self, piece_idx, tray_i):
        if self._solved:
            return
        # Deselect previous
        if self._selected is not None:
            prev_cv = self._piece_btns.get(self._selected)
            if prev_cv:
                prev_cv.configure(highlightbackground=C["accent3"],
                                   highlightthickness=1)
        self._selected = piece_idx
        # Highlight selected
        cv = self._piece_btns.get(piece_idx)
        if cv:
            cv.configure(highlightbackground="#e67e22",
                          highlightthickness=3)
        SFX.play("click")
        self._status_lbl.configure(
            text=f"Piece selected! Now click its slot on the board.",
            fg="#e67e22")

    # ── Place selected piece into a slot ──────────────────────────────────────
    def _place(self, slot_idx):
        if self._solved or self._selected is None:
            return

        # Remove any existing piece from this slot
        if slot_idx in self._placed:
            old_piece = self._placed[slot_idx]
            # Restore old piece to tray
            old_cv = self._piece_btns.get(old_piece)
            if old_cv:
                old_cv.delete("all")
                old_cv.create_image(0, 0, anchor="nw",
                                     image=self._pieces_orig[old_piece])
                old_cv.configure(highlightbackground=C["accent3"],
                                  highlightthickness=1)

        # Place piece on board slot
        piece_idx = self._selected
        self._placed[slot_idx] = piece_idx

        slot_cv = self._slot_cvs[slot_idx]
        slot_cv.delete("all")
        slot_cv.create_image(0, 0, anchor="nw",
                              image=self._pieces_orig[piece_idx])

        # Mark as correct / wrong
        if piece_idx == slot_idx:
            slot_cv.configure(highlightbackground=C["correct"], highlightthickness=2)
            SFX.play("correct")
        else:
            slot_cv.configure(highlightbackground=C["wrong"], highlightthickness=2)
            SFX.play("wrong")

        # Hide piece from tray
        tray_cv = self._piece_btns.get(piece_idx)
        if tray_cv:
            tray_cv.delete("all")
            tray_cv.configure(bg=C["locked"],
                               highlightbackground=C["locked"])

        # Deselect
        self._selected = None

        # Check completion
        correct_count = sum(1 for s, p in self._placed.items() if s == p)
        total_placed  = len(self._placed)
        self._status_lbl.configure(
            text=f"✅ {correct_count} / {self._n} correct  |  {total_placed} placed")

        if correct_count == self._n:
            self._on_complete()

    # ── All pieces correctly placed ───────────────────────────────────────────
    def _on_complete(self):
        self._solved = True
        SFX.play("win")
        self.app.quiz_score += 1
        xp = 20
        self.app.total_xp_session += xp
        self.app.quiz_answers.append({
            "question": "Jigsaw: Birth Control Pills",
            "chosen":   "Completed", "correct": "Completed",
            "is_right": True, "xp": xp,
            "explanation": "You successfully assembled the Birth Control Pills jigsaw!"
        })

        for w in self._done_f.winfo_children():
            w.destroy()
        tk.Label(self._done_f, text="🎉  PUZZLE COMPLETE!",
                 font=_retro(16, "bold"),
                 bg=C["bg"], fg="#e67e22").pack(pady=(8, 2))
        tk.Label(self._done_f, text=f"⚡ +{xp} XP",
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["xp"]).pack()
        Btn(self._done_f, "SEE RESULTS  ✔", self._finish,
            bg="#e67e22", fg="#ffffff", w=240, fs=13,
            pad_bg=C["bg"]).pack(pady=(10, 4))

    def _finish(self):
        SFX.play("click")
        self.app.quiz_index += 1
        self.app.show("result")


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Crossword  (Coming Soon placeholder)
# ══════════════════════════════════════════════════════════════════════════════
class CrosswordScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        lvl = self.app.current_level
        tk.Frame(self, bg="#9b59b6", height=3).pack(fill="x")
        tk.Label(self, text="📝", font=("Segoe UI Emoji", 64),
                 bg=C["bg"]).pack(pady=(50, 8))
        tk.Label(self, text="CROSSWORD PUZZLE",
                 font=_retro(20, "bold"),
                 bg=C["bg"], fg="#9b59b6").pack()
        tk.Label(self, text=f"{lvl['title']}",
                 font=_retro(12),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(4, 0))
        tk.Frame(self, bg="#9b59b6", height=2, width=200).pack(pady=12)
        tk.Label(self, text="🚧  Coming Soon  🚧",
                 font=_retro(14, "bold"),
                 bg=C["bg"], fg=C["medium"]).pack(pady=8)
        tk.Label(self, text="This mini-game is under construction.\nCheck back soon!",
                 font=_retro(10),
                 bg=C["bg"], fg=C["grey"],
                 justify="center").pack(pady=4)
        Btn(self, "🏠  Back to Levels",
            lambda: self.app.show("level_select"),
            bg=C["card2"], fg=C["white"], w=240, fs=12,
            pad_bg=C["bg"]).pack(pady=(30, 0))


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Image Hint  (Coming Soon placeholder — not built yet)
# ══════════════════════════════════════════════════════════════════════════════
class ImageHintScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        lvl = self.app.current_level
        tk.Frame(self, bg="#e74c3c", height=3).pack(fill="x")
        tk.Label(self, text="🖼️", font=("Segoe UI Emoji", 64),
                 bg=C["bg"]).pack(pady=(50, 8))
        tk.Label(self, text="IMAGE WITH HINT",
                 font=_retro(20, "bold"),
                 bg=C["bg"], fg="#e74c3c").pack()
        tk.Label(self, text=f"{lvl['title']}",
                 font=_retro(12),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(4, 0))
        tk.Frame(self, bg="#e74c3c", height=2, width=200).pack(pady=12)
        tk.Label(self, text="🚧  Coming Soon  🚧",
                 font=_retro(14, "bold"),
                 bg=C["bg"], fg=C["medium"]).pack(pady=8)
        tk.Label(self, text="This mini-game is under construction.\nImages and hints will be added soon!",
                 font=_retro(10),
                 bg=C["bg"], fg=C["grey"],
                 justify="center").pack(pady=4)
        Btn(self, "🏠  Back to Levels",
            lambda: self.app.show("level_select"),
            bg=C["card2"], fg=C["white"], w=240, fs=12,
            pad_bg=C["bg"]).pack(pady=(30, 0))


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Game Over
# ══════════════════════════════════════════════════════════════════════════════
class GameOverScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()
        self.after(200, lambda: SFX.play("gameover"))

    def _build(self):
        app = self.app
        lvl = app.current_level

        # Neon top border
        tk.Frame(self, bg=C["wrong"], height=3).pack(fill="x")
        tk.Label(self, text="💔", font=("Segoe UI Emoji",64),
                 bg=C["bg"]).pack(pady=(60,6))
        tk.Label(self, text="GAME  OVER",
                 font=_retro(30, "bold"),
                 bg=C["bg"], fg=C["wrong"]).pack()
        # Neon divider
        div = tk.Canvas(self, width=300, height=4, bg=C["bg"], highlightthickness=0)
        div.pack(pady=6)
        div.create_rectangle(0,1,300,2, fill=C["wrong"], outline="")
        tk.Label(self, text=f"Level {lvl['id']}  ·  {lvl['title']}",
                 font=_retro(11),
                 bg=C["bg"], fg=C["grey"]).pack()

        # Score card
        sc_wrap = tk.Frame(self, bg=C["wrong"], padx=2, pady=2)
        sc_wrap.pack(padx=50, pady=14)
        sc = tk.Frame(sc_wrap, bg=C["card"], padx=24, pady=14)
        sc.pack()
        q = app.quiz_index
        tk.Label(sc, text=f"{app.quiz_score} / {q}",
                 font=_retro(30, "bold"),
                 bg=C["card"], fg=C["white"]).pack()
        tk.Label(sc, text="correct answers",
                 font=_retro(9),
                 bg=C["card"], fg=C["grey"]).pack()
        tk.Label(sc, text=f"⚡ {app.total_xp_session} XP",
                 font=_retro(11, "bold"),
                 bg=C["card"], fg=C["xp"]).pack(pady=(6,0))

        tk.Label(self, text="Don't give up — knowledge saves lives!",
                 font=_retro(9),
                 bg=C["bg"], fg=C["grey"],
                 wraplength=340).pack(pady=4)

        Btn(self, "🔁  TRY AGAIN", self._retry,
            bg=C["wrong"], fg=C["white"], w=250, fs=13,
            pad_bg=C["bg"]).pack(pady=(18,8))
        Btn(self, "🏠  LEVEL SELECT",
            lambda: self.app.show("level_select"),
            bg=C["card"], fg=C["white"], w=250, fs=11,
            pad_bg=C["bg"]).pack()

    def _retry(self):
        SFX.play("start")
        self.app.total_xp_session = 0
        self.app.show("story")

# SCREEN — Result
# ══════════════════════════════════════════════════════════════════════════════
class ResultScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app    = app
        self._stars, self._new_badges = self._save()
        score = app.quiz_score
        total = len(app.current_level["questions"])
        pct   = score / total
        # Pick win or fail sound based on pass threshold (60%)
        if pct == 1.0:
            self.after(300, lambda: SFX.play("win_perfect"))
        elif pct >= 0.6:
            self.after(300, lambda: SFX.play("win"))
        else:
            self.after(300, lambda: SFX.play("fail"))
        self._build()

    def _save(self):
        app   = self.app
        lvl   = app.current_level
        lid   = lvl["id"]
        qt    = lvl.get("quiz_type", "standard")
        if qt == "kahoot":
            total = len(lvl.get("kahoot", lvl.get("questions", [1])))
        elif qt == "myth_fact":
            total = len(lvl.get("myth_fact", lvl.get("questions", [1])))
        elif qt == "hangman":
            total = len(lvl.get("hangman", lvl.get("questions", [1])))
        elif qt in ("jigsaw", "crossword", "image_hint"):
            total = 1   # single-completion mini-games count as 1
        else:
            diff  = app.chosen_difficulty.lower()
            total = len(lvl.get(diff, lvl.get("questions", [1])))
        score = app.quiz_score
        pct   = score / total
        stars = 3 if pct==1.0 else (2 if pct>=0.6 else 1)

        p  = load_json(PROGRESS_DB)
        hs = p.setdefault("high_scores", {})
        prev = hs.get(str(lid), {}).get("score", 0)
        if score >= prev:
            hs[str(lid)] = {"score": score, "total": total, "stars": stars}

        if lid not in p.get("completed_levels", []):
            p.setdefault("completed_levels", []).append(lid)

        # XP
        bonus_xp = XP_PERFECT if pct == 1.0 else 0
        app.total_xp_session += bonus_xp
        p["total_xp"] = p.get("total_xp", 0) + app.total_xp_session

        # Unlock next
        next_id = lid + 1
        all_ids = [l["id"] for l in load_json(QUESTIONS_DB)["levels"]]
        if next_id in all_ids and next_id not in p.get("unlocked_levels",[]):
            p.setdefault("unlocked_levels",[]).append(next_id)
            self.after(900, lambda: SFX.play("unlock"))

        # Badges
        completed = p.get("completed_levels", [])
        existing  = p.get("badges", [])
        new_b = []
        checks = [
            ("first_step",   lid == 1),
            ("beginner",     1 in completed),
            ("intermediate", all(x in completed for x in [1,2,3,4])),
            ("expert",       all(x in completed for x in [1,2,3,4,5,6])),
            ("deciwise",     all(x in completed for x in range(1, 7))),
            ("perfect_run",  pct == 1.0),
            ("speedster",    app.fast_answers >= 5),
        ]
        for key, earned in checks:
            if earned and key not in existing:
                existing.append(key)
                new_b.append(key)
        p["badges"] = existing

        # Leaderboard
        lb = p.setdefault("leaderboard", [])
        lb.append({
            "name":  app.player_name or "Player",
            "level": lid,
            "score": score,
            "total": total,
            "xp":    app.total_xp_session,
            "stars": stars,
        })
        lb.sort(key=lambda x: (-x["xp"], -x["score"]))
        p["leaderboard"] = lb[:10]

        # Flag for congrats popup on level select
        if pct >= 0.6:
            app.congrats_level = {"lvl": lvl, "score": score,
                                   "total": total, "stars": stars, "pct": pct}
        else:
            app.congrats_level = None

        save_json(PROGRESS_DB, p)
        return stars, new_b

    def _build(self):
        app     = self.app
        lvl     = app.current_level
        qt      = lvl.get("quiz_type", "standard")
        if qt == "kahoot":
            total = len(lvl.get("kahoot", lvl.get("questions", [1])))
        elif qt == "myth_fact":
            total = len(lvl.get("myth_fact", lvl.get("questions", [1])))
        elif qt == "hangman":
            total = len(lvl.get("hangman", lvl.get("questions", [1])))
        elif qt in ("jigsaw", "crossword", "image_hint"):
            total = 1   # single-completion mini-games count as 1
        else:
            diff  = app.chosen_difficulty.lower()
            total = len(lvl.get(diff, lvl.get("questions", [1])))
        score   = app.quiz_score
        pct     = score / total
        stars   = self._stars
        answers = app.quiz_answers

        if   pct == 1.0: r_icon,r_msg,r_sub = "🏆","Perfect Score!","You're a family planning expert!"
        elif pct >= 0.6: r_icon,r_msg,r_sub = "👏","Well Done!","Great knowledge on family planning!"
        else:             r_icon,r_msg,r_sub = "📚","Keep Learning!","Review and try again!"

        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=20)

        # Result header card
        result_color = C["correct"] if pct >= 0.6 else C["wrong"]
        tk.Frame(inn, bg=result_color, height=3).pack(fill="x", pady=(0,0))
        hdr_f = tk.Frame(inn, bg=_darken(result_color, 0.2), pady=16)
        hdr_f.pack(fill="x")
        tk.Label(hdr_f, text=r_icon, font=("Segoe UI Emoji",52),
                 bg=C["bg"]).pack()
        tk.Label(hdr_f, text=r_msg, font=_retro(20, "bold"),
                 bg=_darken(result_color, 0.2), fg=C["white"]).pack(pady=(4,0))
        tk.Label(hdr_f, text=r_sub, font=_retro(9),
                 bg=_darken(result_color, 0.2), fg=C["white"]).pack()
        tk.Frame(inn, bg=result_color, height=3).pack(fill="x", pady=(0,8))
        tk.Label(inn, text="⭐"*stars+"☆"*(3-stars),
                 font=_retro(28), bg=C["bg"], fg=C["gold"]).pack(pady=4)

        # Score + XP row
        row = tk.Frame(inn, bg=C["bg"])
        row.pack(fill="x", pady=12)

        sc_f = tk.Frame(row, bg=C["card"], padx=18, pady=12,
                        highlightbackground=C["accent2"], highlightthickness=1)
        sc_f.pack(side="left", expand=True, fill="both", padx=(0,6))
        tk.Label(sc_f, text=f"{score}/{total}",
                 font=_retro(22, "bold"),
                 bg=C["card"], fg=C["white"]).pack()
        tk.Label(sc_f, text="Correct", font=_retro(9),
                 bg=C["card"], fg=C["grey"]).pack()

        xp_f = tk.Frame(row, bg=C["card2"], padx=18, pady=12,
                        highlightbackground=C["xp"], highlightthickness=1)
        xp_f.pack(side="left", expand=True, fill="both", padx=(6,0))
        tk.Label(xp_f, text=f"+{app.total_xp_session}",
                 font=_retro(22, "bold"),
                 bg=C["card2"], fg=C["xp"]).pack()
        tk.Label(xp_f, text="XP Earned", font=_retro(9),
                 bg=C["card2"], fg=C["grey"]).pack()

        # Progress bar
        bar_bg = tk.Frame(inn, bg=C["locked"], height=10)
        bar_bg.pack(fill="x", pady=(0,14))
        bw = int((WINDOW_W-40) * pct)
        tk.Frame(bar_bg, bg=C["correct"] if pct>=0.6 else C["wrong"],
                 height=10, width=bw).place(x=0,y=0)

        # New badges
        if self._new_badges:
            tk.Label(inn, text="🎖  New Badge(s) Earned!",
                     font=_retro(12, "bold"),
                     bg=C["bg"], fg=C["gold"]).pack(anchor="w", pady=(0,4))
            for bk in self._new_badges:
                bd = BADGES[bk]
                bf = tk.Frame(inn, bg=C["card2"], padx=12, pady=8,
                              highlightbackground=C["gold"],
                              highlightthickness=1)
                bf.pack(fill="x", pady=3)
                tk.Label(bf, text=f"{bd['icon']}  {bd['name']}",
                         font=_retro(11, "bold"),
                         bg=C["card2"], fg=C["gold"]).pack(anchor="w")
                tk.Label(bf, text=bd["desc"],
                         font=_retro(9),
                         bg=C["card2"], fg=C["grey"]).pack(anchor="w")

        # Answer review
        tk.Label(inn, text="Answer Review",
                 font=_retro(13, "bold"),
                 bg=C["bg"], fg=C["accent"],
                 anchor="w").pack(fill="x", pady=(8,6))

        for i, a in enumerate(answers):
            is_r = a["is_right"]
            bc   = C["correct"] if is_r else C["wrong"]
            row  = tk.Frame(inn, bg=C["card"], padx=12, pady=8,
                            highlightbackground=bc, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"Q{i+1}: {a['question']}",
                     font=_retro(10, "bold"),
                     bg=C["card"], fg=C["white"],
                     wraplength=366, justify="left").pack(anchor="w")
            tk.Label(row,
                     text=f"{'✅' if is_r else '❌'}  {a['chosen']}  (⚡+{a.get('xp',0)} XP)",
                     font=_retro(10),
                     bg=C["card"], fg=bc,
                     wraplength=366, justify="left").pack(anchor="w")
            if not is_r:
                tk.Label(row, text=f"✔ {a['correct']}",
                         font=_retro(10, "bold"),
                         bg=C["card"], fg=C["easy"],
                         wraplength=366).pack(anchor="w")
            if a.get("explanation"):
                tk.Label(row, text=f"💡 {a['explanation']}",
                         font=_retro(9),
                         bg=C["card"], fg=C["grey"],
                         wraplength=366).pack(anchor="w", pady=(3,0))

        tk.Label(inn, text="", bg=C["bg"]).pack()

        Btn(inn, "🔁  Retry Level", self._retry,
            bg=C["accent2"], fg=C["white"], w=250, fs=12,
            pad_bg=C["bg"]).pack(pady=(4,6))
        Btn(inn, "🏠  Level Select",
            lambda: [SFX.play("back"), self.app.show("level_select")],
            bg=C["card"], fg=C["white"], w=250, fs=12,
            pad_bg=C["bg"]).pack(pady=(0,6))
        Btn(inn, "🏆  Leaderboard",
            lambda: self.app.show("leaderboard"),
            bg=C["card2"], fg=C["white"], w=250, fs=12,
            pad_bg=C["bg"]).pack(pady=(0,24))

    def _retry(self):
        SFX.play("start")
        self.app.total_xp_session = 0
        self.app.show("story")

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Leaderboard
# ══════════════════════════════════════════════════════════════════════════════
class LeaderboardScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["banner"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏆  Leaderboard",
                 font=_retro(16, "bold"),
                 bg=C["banner"], fg=C["gold"]).pack(side="left", padx=16)
        Btn(hdr, "← Back",
            lambda: self.app.show("splash"),
            bg=C["card2"], fg=C["white"], w=90, fs=10,
            pad_bg=C["banner"]).pack(side="right", padx=12)

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=16)

        try:
            p  = load_json(PROGRESS_DB)
            lb = p.get("leaderboard", [])
        except Exception:
            lb = []

        rank_icons = ["🥇","🥈","🥉"] + ["  "]*10
        medal_cols = [C["gold"], C["silver"], C["bronze"]]

        if not lb:
            tk.Label(inn, text="No scores yet.\nPlay a level to appear here!",
                     font=_retro(12),
                     bg=C["bg"], fg=C["grey"],
                     justify="center").pack(pady=60)
        else:
            tk.Label(inn, text="Top 10 Scores",
                     font=_retro(11),
                     bg=C["bg"], fg=C["grey"]).pack(pady=(14,8))
            for i, entry in enumerate(lb[:10]):
                mc  = medal_cols[i] if i < 3 else C["grey"]
                row = tk.Frame(inn, bg=C["card"], padx=14, pady=10,
                               highlightbackground=mc,
                               highlightthickness=1 if i<3 else 0)
                row.pack(fill="x", pady=4)

                left = tk.Frame(row, bg=C["card"])
                left.pack(side="left", fill="x", expand=True)

                tk.Label(left,
                         text=f"{rank_icons[i]}  {entry['name']}",
                         font=_retro(12, "bold"),
                         bg=C["card"], fg=mc).pack(anchor="w")
                tk.Label(left,
                         text=f"Level {entry['level']}  ·  {entry['score']}/{entry['total']}  ·  ⭐{'⭐'*entry['stars']}",
                         font=_retro(9),
                         bg=C["card"], fg=C["grey"]).pack(anchor="w")

                tk.Label(row,
                         text=f"⚡{entry['xp']} XP",
                         font=_retro(12, "bold"),
                         bg=C["card"], fg=C["xp"]).pack(side="right")

        # Reset button
        tk.Label(inn, text="", bg=C["bg"]).pack()
        Btn(inn, "🗑  Clear Scores",
            self._clear,
            bg=C["card2"], fg=C["wrong"], w=200, fs=10,
            pad_bg=C["bg"]).pack(pady=(0,30))

    def _clear(self):
        try:
            p = load_json(PROGRESS_DB)
            p["leaderboard"] = []
            save_json(PROGRESS_DB, p)
        except Exception:
            pass
        self.app.show("leaderboard")


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Badges
# ══════════════════════════════════════════════════════════════════════════════
class BadgesScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["banner"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🎖  Badges & Achievements",
                 font=_retro(15, "bold"),
                 bg=C["banner"], fg=C["gold"]).pack(side="left", padx=16)
        Btn(hdr, "← Back",
            lambda: self.app.show("splash"),
            bg=C["card2"], fg=C["white"], w=90, fs=10,
            pad_bg=C["banner"]).pack(side="right", padx=12)

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=16)

        try:
            p       = load_json(PROGRESS_DB)
            earned  = p.get("badges", [])
            total_xp= p.get("total_xp", 0)
        except Exception:
            earned, total_xp = [], 0

        tk.Label(inn, text=f"Total XP: ⚡ {total_xp}",
                 font=_retro(13, "bold"),
                 bg=C["bg"], fg=C["xp"]).pack(pady=(16,4))
        tk.Label(inn, text=f"{len(earned)} / {len(BADGES)} badges unlocked",
                 font=_retro(10),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(0,14))

        for key, bd in BADGES.items():
            got = key in earned
            bg  = C["card2"] if got else C["locked"]
            bc  = C["gold"] if got else C["locked"]

            row = tk.Frame(inn, bg=bg, padx=14, pady=12,
                           highlightbackground=bc,
                           highlightthickness=1)
            row.pack(fill="x", pady=5)

            tk.Label(row, text=bd["icon"],
                     font=("Segoe UI Emoji",26),
                     bg=bg).pack(side="left", padx=(0,10))

            info = tk.Frame(row, bg=bg)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=bd["name"],
                     font=_retro(11, "bold"),
                     bg=bg,
                     fg=C["gold"] if got else C["grey"]).pack(anchor="w")
            tk.Label(info, text=bd["desc"],
                     font=_retro(9),
                     bg=bg,
                     fg=C["white"] if got else C["locked"]).pack(anchor="w")

            tk.Label(row, text="✔" if got else "🔒",
                     font=_retro(16),
                     bg=bg,
                     fg=C["correct"] if got else C["grey"]).pack(side="right")

        tk.Label(inn, text="", bg=C["bg"], height=2).pack()


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
