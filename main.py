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

# Quiz modes — key matches the JSON field name
QUIZ_MODES = [
    {
        "key":   "questions",
        "label": "Standard Quiz",
        "icon":  "📝",
        "color": C["accent"],
        "desc":  "Multiple-choice questions on family planning",
    },
    {
        "key":   "myth_busting",
        "label": "Myth Busting",
        "icon":  "🔍",
        "color": "#ffaa00",
        "desc":  "Separate fact from fiction on common myths",
    },
    {
        "key":   "scenario",
        "label": "Scenario Challenge",
        "icon":  "🎭",
        "color": "#cc44ff",
        "desc":  "Real-life case situations — what would you do?",
    },
    {
        "key":   "couple_decisions",
        "label": "Couple Decision",
        "icon":  "💑",
        "color": "#c0392b",
        "desc":  "2 players decide together — see how choices combine!",
    },
]

# Timer seconds per difficulty
TIMER = {"Easy": 30, "Medium": 22, "Hard": 16}
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
}

BADGES = {
    "first_step":   {"icon": "🌱", "name": "First Step",     "desc": "Complete Level 1"},
    "beginner":     {"icon": "📗", "name": "Beginner",        "desc": "Complete Act I (Levels 1-2)"},
    "intermediate": {"icon": "📘", "name": "Intermediate",    "desc": "Complete Act II (Levels 3-4)"},
    "expert":       {"icon": "📕", "name": "Expert",          "desc": "Complete Act III (Levels 5-6)"},
    "perfect_run":  {"icon": "🏆", "name": "Perfect Run",     "desc": "Score 100% on any level"},
    "speedster":    {"icon": "⚡", "name": "Speedster",       "desc": "Answer 5 questions quickly"},
    "deciwise":     {"icon": "🎓", "name": "DeciWise Master", "desc": "Complete all 6 levels"},
}

ACT_MAP = {1: ("Act I",   "Foundations",  "#52e088", [1, 2]),
           2: ("Act II",  "Intermediate", "#f39c12", [3, 4]),
           3: ("Act III", "Expert",       "#e74c3c", [5, 6])}

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
    a,b = a.lstrip("#"), b.lstrip("#")
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
        # Main body
        cv.create_rectangle(1, 1, bw-4, bh-4, fill=color, outline="")
        # Top-left highlight edge
        bright = _lerp(color, "#ffffff", 0.30)
        cv.create_line(1, bh-4, 1, 1, fill=bright, width=2)
        cv.create_line(1, 1, bw-4, 1, fill=bright, width=2)
        # Bottom-right shadow edge
        cv.create_line(bw-4, 1, bw-4, bh-4, fill=shadow, width=1)
        cv.create_line(1, bh-4, bw-4, bh-4, fill=shadow, width=1)
        # Label — with 1px shadow for depth
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
        self.player_name    = ""
        self.current_level  = None
        self.quiz_mode      = QUIZ_MODES[0]
        self.quiz_index     = 0
        self.quiz_score     = 0
        self.quiz_answers   = []
        self.lives          = MAX_LIVES
        self.total_xp_session = 0
        self.fast_answers   = 0
        self.congrats_level = None   # set to level dict when player just passed

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
            "result":       ResultScreen,
            "gameover":     GameOverScreen,
            "leaderboard":  LeaderboardScreen,
            "badges":       BadgesScreen,
            "couple_game":  CoupleGameScreen,
        }
        self._frame = screens[name](self, self, **kw)
        self._frame.pack(fill="both", expand=True)

    def start_level(self):
        """Reset per-level quiz state and go to quiz or couple game."""
        self.quiz_index   = 0
        self.quiz_score   = 0
        self.quiz_answers = []
        self.lives        = MAX_LIVES
        self.fast_answers = 0
        if self.quiz_mode["key"] == "couple_decisions":
            self.show("couple_game")
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

        tk.Label(self, text="v2.0  ·  DeciWise  ·  INSERT COIN ▶",
                 font=_retro(7), bg=C["bg"],
                 fg=C["grey"]).pack(side="bottom", pady=6)
        self._blink_insert(self.winfo_children()[-1])

    def _draw_header(self):
        cv = self._cv
        cv.delete("all")
        # Background fill
        cv.create_rectangle(0, 0, WINDOW_W, 220, fill=C["bg"], outline="")
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
        for off, alpha in [(6,"#001a08"),(4,"#003311"),(2,"#005522")]:
            cv.create_text(WINDOW_W//2, 78+off//2,
                            text="DECIWISE",
                            font=_retro(38, "bold"),
                            fill=alpha)
        # Title shadow + foreground
        cv.create_text(WINDOW_W//2 + 2, 77,
                        text="DECIWISE",
                        font=_retro(38, "bold"),
                        fill="#2e6640")
        cv.create_text(WINDOW_W//2, 75,
                        text="DECIWISE",
                        font=_retro(38, "bold"),
                        fill=C["accent"])
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

        # ── Outer neon glow border (layered outlines) ──────────────────────
        for i in range(4):
            self._cv.create_rectangle(
                cx - i, cy - i, cx + cw + i, cy + ch + i,
                outline=dc, fill="", tags="card_top")

        # ── Card body — dark CRT background ───────────────────────────────
        self._cv.create_rectangle(
            cx, cy, cx + cw, cy + ch,
            fill="#1e281e", outline="", tags="card_top")

        # ── Chunky pixel corners ───────────────────────────────────────────
        corner_size = 10
        for ox, oy in [(cx, cy), (cx+cw-corner_size, cy),
                       (cx, cy+ch-corner_size), (cx+cw-corner_size, cy+ch-corner_size)]:
            self._cv.create_rectangle(
                ox, oy, ox+corner_size, oy+corner_size,
                fill=dc, outline="", tags="card_top")

        # ── Top header strip ───────────────────────────────────────────────
        self._cv.create_rectangle(
            cx, cy, cx+cw, cy+38,
            fill=dc, outline="", tags="card_top")
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

        # Level number pill badge
        num_cv = tk.Canvas(row1, width=36, height=36,
                            bg=bg, highlightthickness=0)
        num_cv.pack(side="left", padx=(0,10))
        # Outer glow ring
        if is_open:
            num_cv.create_oval(1, 1, 35, 35, fill=_darken(act_color,0.4), outline="")
        num_cv.create_oval(4, 4, 32, 32,
                            fill=act_color if is_open else C["locked"], outline="")
        num_cv.create_text(18, 18, text=str(lid),
                            fill=C["bg"] if is_open else C["grey"],
                            font=_retro(11, "bold"))

        info = tk.Frame(row1, bg=bg)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=lvl["title"],
                 font=_retro(11, "bold"),
                 bg=bg, fg=C["white"] if is_open else C["grey"]).pack(anchor="w")
        tk.Label(info, text=f"{lvl['difficulty']}  ·  5 Qs  ·  ⏱{TIMER[lvl['difficulty']]}s",
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

# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Story (animated typewriter)
# ══════════════════════════════════════════════════════════════════════════════
class StoryScreen(tk.Frame):
    _TW_DELAY   = 20
    _BOUNCE     = [18,30,44,54,48,52,50,50]
    _FADE_STEPS = 14

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app        = app
        self._aids      = []
        self._done      = False
        self._build()

    def _build(self):
        lvl = self.app.current_level
        self._lvl       = lvl
        self._icon_char = STORY_ICONS.get(lvl.get("story_image",""), "📖")
        diff_c          = lvl["difficulty_color"]
        timer_s         = TIMER[lvl["difficulty"]]

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

        # Scroll body
        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        self._sf = sf
        inn = sf.inner
        inn.configure(padx=18)

        self._icon_lbl = tk.Label(inn, text="",
                                   font=("Segoe UI Emoji",50), bg="#2a3a2a")
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

        # Info strip
        qn = len(lvl["questions"])
        self._info = tk.Label(inn,
                               text=f"❓ {qn} Questions  |  ⏱ {timer_s}s each  |  ❤ {MAX_LIVES} lives",
                               font=_retro(10),
                               bg=C["bg"], fg=C["bg"])
        self._info.pack(pady=(12,4))

        # XP info
        xp_est = qn * XP_CORRECT
        self._xp_lbl = tk.Label(inn,
                                  text=f"⚡ Earn up to {xp_est + XP_PERFECT} XP on this level",
                                  font=_retro(9),
                                  bg=C["bg"], fg=C["bg"])
        self._xp_lbl.pack(pady=(0,4))

        # ── Swipeable quiz mode selector ──────────────────────────────────
        self._mode_idx = 0
        self._swipe_hint = tk.Label(
            inn, text="◀  swipe or tap to change quiz type  ▶",
            font=_retro(9),
            bg=C["bg"], fg=C["bg"])   # invisible until revealed
        self._swipe_hint.pack(pady=(0,4))

        self._mode_cv = tk.Canvas(
            inn, width=WINDOW_W-36, height=110,
            bg=C["bg"], highlightthickness=0)
        self._mode_cv.pack(pady=(0,6))

        # Dot indicators
        self._dot_frame = tk.Frame(inn, bg=C["bg"])
        self._dot_frame.pack(pady=(0,10))
        self._dots = []
        for i in range(len(QUIZ_MODES)):
            d = tk.Canvas(self._dot_frame, width=10, height=10,
                           bg=C["bg"], highlightthickness=0)
            d.pack(side="left", padx=3)
            d.create_oval(1,1,9,9,
                           fill=C["accent"] if i==0 else C["locked"],
                           outline="", tags="dot")
            self._dots.append(d)

        # Swipe detection on mode card
        self._drag_start = None
        self._mode_cv.bind("<ButtonPress-1>",   self._drag_begin)
        self._mode_cv.bind("<ButtonRelease-1>", self._drag_end)

        self._begin_f = Btn(inn, "  BEGIN QUIZ  ▶  ", self._start,
                            bg=C["accent"], fg=C["dark"], w=250, fs=13,
                            pad_bg=C["bg"])
        self._back_f  = Btn(inn, "← Back", self._back,
                            bg=C["card2"], fg=C["white"], w=120, fs=11,
                            pad_bg=C["bg"])
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
        self._swipe_hint.configure(fg=_lerp(C["bg"], C["grey"], t))

        # Draw the mode card on first step
        if step == 0:
            self._draw_mode_card()
            self._begin_f.pack(pady=(0,10))
            self._back_f.pack(pady=(0,24))

        # Fade button colours from bg → final colour
        for btn_f, bc, tc in [(self._begin_f, C["accent"], C["dark"]),
                               (self._back_f,  C["card2"],  C["white"])]:
            col  = _lerp(C["bg"], bc, t)
            tcol = _lerp(C["bg"], tc, t)
            btn_f._cv.delete("all")
            rr(btn_f._cv, 2, 2, btn_f._bw-2, btn_f._bh-2, r=14,
               fill=col, outline="")
            btn_f._cv.create_text(btn_f._bw//2, btn_f._bh//2,
                                   text=btn_f._text,
                                   fill=tcol, font=btn_f._fnt)
        if step < n:
            self._aids.append(self.after(32, lambda: self._reveal(step+1)))
        else:
            self._begin_f._draw()
            self._back_f._draw()

    # ── Mode card drawing ─────────────────────────────────────────────────────
    def _draw_mode_card(self):
        """Render the currently selected quiz mode as a card on the canvas."""
        cv   = self._mode_cv
        mode = QUIZ_MODES[self._mode_idx]
        w    = cv.winfo_width() or WINDOW_W - 36
        h    = 110
        cv.delete("all")

        # Card background
        rr(cv, 2, 2, w-2, h-2, r=16, fill=mode["color"], outline="")

        # Dark tint overlay for readability
        rr(cv, 2, 2, w-2, h-2, r=16,
           fill=_darken(mode["color"], 0.45), outline="",
           stipple="gray50")

        # Emoji icon
        cv.create_text(50, h//2, text=mode["icon"],
                        font=("Segoe UI Emoji", 28))

        # Label
        cv.create_text(w//2 + 16, h//2 - 18,
                        text=mode["label"],
                        font=_retro(14, "bold"),
                        fill="#ffffff", anchor="center")

        # Description
        cv.create_text(w//2 + 16, h//2 + 10,
                        text=mode["desc"],
                        font=_retro(9),
                        fill="#dddddd", anchor="center",
                        width=w - 110)

        # Left / right arrows (if more modes available)
        if self._mode_idx > 0:
            cv.create_text(14, h//2, text="◀",
                            font=_retro(14, "bold"),
                            fill="#ffffff")
        if self._mode_idx < len(QUIZ_MODES) - 1:
            cv.create_text(w - 14, h//2, text="▶",
                            font=_retro(14, "bold"),
                            fill="#ffffff")

        # Update dot indicators
        for i, d in enumerate(self._dots):
            d.itemconfig("dot",
                          fill=mode["color"] if i == self._mode_idx
                          else C["locked"])

        # Update BEGIN button colour to match mode
        self._begin_f._bg = mode["color"]
        self._begin_f._draw()

        # Update app quiz mode
        self.app.quiz_mode = mode

    # ── Swipe / tap handling ──────────────────────────────────────────────────
    def _drag_begin(self, event):
        self._drag_start = event.x

    def _drag_end(self, event):
        if self._drag_start is None:
            return
        dx = event.x - self._drag_start
        self._drag_start = None

        if abs(dx) < 8:
            # Treated as a tap — cycle forward
            self._set_mode((self._mode_idx + 1) % len(QUIZ_MODES))
        elif dx < -30:
            # Swipe left → next mode
            if self._mode_idx < len(QUIZ_MODES) - 1:
                self._set_mode(self._mode_idx + 1)
        elif dx > 30:
            # Swipe right → previous mode
            if self._mode_idx > 0:
                self._set_mode(self._mode_idx - 1)

    def _set_mode(self, idx):
        self._mode_idx = idx
        SFX.play("click")
        self._draw_mode_card()

    def _skip(self):
        [self.after_cancel(a) for a in self._aids]
        self._aids.clear()
        lvl = self._lvl
        self._banner.configure(bg=C["banner"])
        self._t1.configure(bg=C["banner"], fg=C["white"])
        self._t2.configure(bg=C["banner"], fg=lvl["difficulty_color"])
        self._icon_lbl.configure(text=self._icon_char,
                                  font=("Segoe UI Emoji",50))
        self._hdr_lbl.configure(fg=C["accent"])
        self._st.configure(text=lvl["story"])
        self._info.configure(fg=C["grey"])
        self._xp_lbl.configure(fg=C["xp"])
        self._swipe_hint.configure(fg=C["grey"])
        self._draw_mode_card()
        if not self._begin_f.winfo_ismapped(): self._begin_f.pack(pady=(0,10))
        if not self._back_f.winfo_ismapped():  self._back_f.pack(pady=(0,24))
        self._begin_f._draw()
        self._back_f._draw()
        self._done = True

    def _start(self):
        [self.after_cancel(a) for a in self._aids]
        SFX.play("start")
        self.app.start_level()

    def _back(self):
        [self.after_cancel(a) for a in self._aids]
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
        self._t_left = TIMER[app.current_level["difficulty"]]
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
        mode  = app.quiz_mode          # ← selected mode from StoryScreen
        qs    = lvl.get(mode["key"], lvl["questions"])   # fall back to standard
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

        # Mode badge + Question counter
        mode_badge = tk.Label(
            hud,
            text=f"Q {idx+1}/{total}",
            font=_retro(10, "bold"),
            bg=C["banner"], fg=mode["color"])
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
                # Card body
                cv.create_rectangle(2, 2, w-2, 50,
                                     fill=col, outline="")
                # Left neon accent strip (letter box)
                acc = C["accent2"] if col == _col_base else _lerp(col, "#ffffff", 0.2)
                cv.create_rectangle(2, 2, 36, 50, fill=acc, outline="")
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
        if self.app.quiz_index >= len(self.app.current_level["questions"]):
            self.app.show("result")
        else:
            self.app.show("quiz")

    def _go_gameover(self):
        if self._t_aid: self.after_cancel(self._t_aid)
        self.app.show("gameover")

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
                 bg="#2e1a1a").pack(pady=(60,6))
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


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN — Couple Decision Game
# ══════════════════════════════════════════════════════════════════════════════
class CoupleGameScreen(tk.Frame):
    """
    2-player mode. Flow per scenario:
      1. Show scenario text to both players
      2. Player 1 picks Yes/No (Player 2 looks away)
      3. Player 2 picks Yes/No (Player 1 looks away)
      4. Reveal combined outcome + consequence text + XP
      5. Next scenario or final summary
    """
    # Sub-states within one scenario
    _ST_SCENARIO  = "scenario"   # reading the scenario
    _ST_P1_PICK   = "p1_pick"    # P1 choosing
    _ST_P2_PICK   = "p2_pick"    # P2 choosing
    _ST_REVEAL    = "reveal"     # showing outcome

    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app        = app
        self._state     = self._ST_SCENARIO
        self._p1_choice = None
        self._p2_choice = None
        self._total_xp  = 0
        self._results   = []   # list of {scenario, p1, p2, outcome_key, outcome}
        self._build()

    # ── Helpers ──────────────────────────────────────────────────────────────
    @property
    def _decisions(self):
        return self.app.current_level.get("couple_decisions", [])

    @property
    def _current(self):
        return self._decisions[self.app.quiz_index]

    def _hdr(self, parent, text, sub=""):
        """Render the top banner."""
        h = tk.Frame(parent, bg=C["banner"], pady=10)
        h.pack(fill="x")
        tk.Label(h, text=text, font=_retro(14, "bold"),
                 bg=C["banner"], fg="#c0392b").pack()
        if sub:
            tk.Label(h, text=sub, font=_retro(10),
                     bg=C["banner"], fg=C["grey"]).pack()
        return h

    def _progress_bar(self, parent):
        idx   = self.app.quiz_index
        total = len(self._decisions)
        pb_bg = tk.Frame(parent, bg=C["locked"], height=5)
        pb_bg.pack(fill="x")
        tk.Frame(pb_bg, bg="#c0392b", height=5,
                 width=int(WINDOW_W * (idx + 1) / total)).place(x=0, y=0)

    # ══ STATE: scenario ══════════════════════════════════════════════════════
    def _build(self):
        self._clear()
        dec   = self._current
        idx   = self.app.quiz_index
        total = len(self._decisions)

        self._hdr(self, f"💑 Couple Decision  {idx+1}/{total}",
                  sub=f"Level {self.app.current_level['id']}  ·  {self.app.current_level['difficulty']}")
        self._progress_bar(self)

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=18)

        # XP earned so far
        tk.Label(inn, text=f"⚡ {self._total_xp} XP earned this round",
                 font=_retro(10, "bold"),
                 bg=C["bg"], fg=C["xp"]).pack(pady=(12, 4))

        # Scenario card
        sc = tk.Frame(inn, bg=C["card"], padx=16, pady=14,
                      highlightbackground="#c0392b", highlightthickness=2)
        sc.pack(fill="x")
        tk.Label(sc, text="📋  Situation",
                 font=_retro(11, "bold"),
                 bg=C["card"], fg="#c0392b",
                 anchor="w").pack(fill="x", pady=(0, 6))
        tk.Label(sc, text=dec["scenario"],
                 font=_retro(11),
                 bg=C["card"], fg=C["white"],
                 wraplength=364, justify="left").pack(anchor="w")

        # Question
        tk.Label(inn, text=dec["question"],
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["white"],
                 wraplength=380, justify="center").pack(pady=(16, 4))

        # Player labels
        row = tk.Frame(inn, bg=C["bg"])
        row.pack(pady=(4, 16))
        for lbl, color in [(dec["player1_label"], "#3498db"),
                            (dec["player2_label"], "#e67e22")]:
            tk.Label(row, text=f"👤 {lbl}",
                     font=_retro(10, "bold"),
                     bg=C["bg"], fg=color).pack(side="left", padx=20)

        # Begin button
        Btn(inn, "▶  Start — Player 1 Goes First",
            self._go_p1_pick,
            bg="#c0392b", fg=C["white"], w=300, fs=12,
            pad_bg=C["bg"]).pack(pady=(0, 10))

        Btn(inn, "← Back to Level Select",
            lambda: self.app.show("level_select"),
            bg=C["card2"], fg=C["white"], w=200, fs=10,
            pad_bg=C["bg"]).pack(pady=(0, 24))

    # ══ STATE: p1 pick ════════════════════════════════════════════════════════
    def _go_p1_pick(self):
        self._clear()
        dec = self._current
        p1  = dec["player1_label"]
        p2  = dec["player2_label"]

        self._hdr(self, f"👤 {p1}'s Turn",
                  sub=f"{p2} — please look away! 👀")

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=20)

        # Reminder of scenario (brief)
        tk.Label(inn, text=dec["question"],
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["white"],
                 wraplength=370, justify="center").pack(pady=(20, 24))

        # Choice buttons
        for choice in dec["choices"]:
            color = "#27ae60" if choice == "Yes" else "#c0392b"
            Btn(inn, f"  {choice}  ",
                lambda c=choice: self._p1_chose(c),
                bg=color, fg=C["white"], w=200, fs=16,
                pad_bg=C["bg"]).pack(pady=8)

        tk.Label(inn, text=f"Your answer is private — {p2} cannot see it yet.",
                 font=_retro(9),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(16, 0))

    def _p1_chose(self, choice):
        self._p1_choice = choice
        SFX.play("click")
        self._go_handoff()

    # ══ STATE: handoff screen ═════════════════════════════════════════════════
    def _go_handoff(self):
        self._clear()
        dec = self._current
        p2  = dec["player2_label"]

        hdr = tk.Frame(self, bg=C["banner"], pady=30)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✅  Choice Locked In!",
                 font=_retro(16, "bold"),
                 bg=C["banner"], fg="#27ae60").pack()
        tk.Label(hdr, text=f"Now pass the device to  {p2}",
                 font=_retro(12),
                 bg=C["banner"], fg=C["white"]).pack(pady=(6, 0))

        body = tk.Frame(self, bg=C["bg"])
        body.pack(expand=True)
        tk.Label(body, text="🔄",
                 font=("Segoe UI Emoji", 52),
                 bg="#2a3a2a").pack(pady=(40, 10))
        tk.Label(body, text=f"Hand the device to {p2}\nand ask them to answer.",
                 font=_retro(13),
                 bg=C["bg"], fg=C["grey"],
                 justify="center").pack()

        Btn(body, f"▶  {p2} Is Ready",
            self._go_p2_pick,
            bg="#e67e22", fg=C["white"], w=240, fs=13,
            pad_bg=C["bg"]).pack(pady=(30, 0))

    # ══ STATE: p2 pick ════════════════════════════════════════════════════════
    def _go_p2_pick(self):
        self._clear()
        dec = self._current
        p2  = dec["player2_label"]
        p1  = dec["player1_label"]

        self._hdr(self, f"👤 {p2}'s Turn",
                  sub=f"{p1} — please look away! 👀")

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=20)

        tk.Label(inn, text=dec["question"],
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["white"],
                 wraplength=370, justify="center").pack(pady=(20, 24))

        for choice in dec["choices"]:
            color = "#27ae60" if choice == "Yes" else "#c0392b"
            Btn(inn, f"  {choice}  ",
                lambda c=choice: self._p2_chose(c),
                bg=color, fg=C["white"], w=200, fs=16,
                pad_bg=C["bg"]).pack(pady=8)

        tk.Label(inn, text=f"Your answer is private — {p1} cannot see it yet.",
                 font=_retro(9),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(16, 0))

    def _p2_chose(self, choice):
        self._p2_choice = choice
        SFX.play("click")
        self._go_reveal()

    # ══ STATE: reveal ═════════════════════════════════════════════════════════
    def _go_reveal(self):
        self._clear()
        dec        = self._current
        key        = f"{self._p1_choice}-{self._p2_choice}"
        outcome    = dec["outcomes"][key]
        xp         = outcome.get("xp", 0)
        positive   = outcome.get("positive", False)
        self._total_xp += xp
        self.app.quiz_score += (1 if positive else 0)

        self._results.append({
            "scenario": dec["scenario"][:60] + "…",
            "p1": dec["player1_label"],
            "p2": dec["player2_label"],
            "p1_choice": self._p1_choice,
            "p2_choice": self._p2_choice,
            "outcome_key": key,
            "outcome": outcome,
        })

        if positive:
            SFX.play("correct")
        else:
            SFX.play("wrong")

        border_c = C["correct"] if positive else C["wrong"]
        icon     = "✅" if positive else "❌"

        self._hdr(self, "🎯  Outcome Revealed!")
        self._progress_bar(self)

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=18)

        # Choices display
        cr = tk.Frame(inn, bg=C["bg"])
        cr.pack(pady=(14, 6))
        for lbl, choice, color in [
            (dec["player1_label"], self._p1_choice, "#3498db"),
            (dec["player2_label"], self._p2_choice, "#e67e22")
        ]:
            cv_color = "#27ae60" if choice == "Yes" else "#c0392b"
            tk.Label(cr,
                     text=f"{lbl}: {choice}",
                     font=_retro(12, "bold"),
                     bg=C["bg"], fg=cv_color).pack(side="left", padx=16)

        # Outcome card
        oc = tk.Frame(inn, bg=C["card"], padx=16, pady=14,
                      highlightbackground=border_c, highlightthickness=2)
        oc.pack(fill="x", pady=6)
        tk.Label(oc, text=f"{icon}  {outcome['title']}",
                 font=_retro(14, "bold"),
                 bg=C["card"],
                 fg=C["correct"] if positive else C["wrong"]).pack(anchor="w")
        tk.Label(oc, text=outcome["text"],
                 font=_retro(11),
                 bg=C["card"], fg=C["white"],
                 wraplength=364, justify="left").pack(anchor="w", pady=(8, 0))

        # XP flash
        xp_c = C["xp"] if xp > 0 else C["grey"]
        tk.Label(inn, text=f"⚡ +{xp} XP  (Total: {self._total_xp} XP)",
                 font=_retro(11, "bold"),
                 bg=C["bg"], fg=xp_c).pack(pady=(10, 4))

        # Best outcome hint if not positive
        if not positive:
            best = dec["outcomes"].get("Yes-Yes", {})
            if best:
                hf = tk.Frame(inn, bg=C["card2"], padx=14, pady=10,
                              highlightbackground=C["accent2"],
                              highlightthickness=1)
                hf.pack(fill="x", pady=4)
                tk.Label(hf, text="💡 Best Outcome (Yes + Yes):",
                         font=_retro(10, "bold"),
                         bg=C["card2"], fg=C["accent"]).pack(anchor="w")
                tk.Label(hf, text=best.get("text","")[:180]+"…",
                         font=_retro(9),
                         bg=C["card2"], fg=C["grey"],
                         wraplength=358, justify="left").pack(anchor="w")

        # Next or finish
        idx   = self.app.quiz_index
        total = len(self._decisions)
        lbl   = "NEXT SCENARIO  ➜" if idx + 1 < total else "SEE SUMMARY  ✔"
        Btn(inn, lbl, self._next,
            bg=C["accent"], fg=C["dark"], w=260, fs=13,
            pad_bg=C["bg"]).pack(pady=(14, 24))

    # ══ Navigation ════════════════════════════════════════════════════════════
    def _next(self):
        self._p1_choice = None
        self._p2_choice = None
        self.app.quiz_index += 1
        total = len(self._decisions)
        if self.app.quiz_index >= total:
            self._go_summary()
        else:
            self._build()

    def _go_summary(self):
        self._clear()
        total    = len(self._decisions)
        score    = self.app.quiz_score
        pct      = score / total
        self.app.total_xp_session = self._total_xp

        # Determine win/fail
        if pct >= 0.6:
            SFX.play("win" if pct < 1.0 else "win_perfect")
            self.app.congrats_level = {
                "lvl":   self.app.current_level,
                "score": score, "total": total,
                "stars": 3 if pct==1.0 else (2 if pct>=0.8 else 1),
                "pct":   pct
            }
        else:
            SFX.play("fail")
            self.app.congrats_level = None

        self._hdr(self, "💑  Couple Decision Summary")

        sf  = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inn = sf.inner
        inn.configure(padx=18)

        # Score header
        r_icon = "🏆" if pct==1.0 else ("👏" if pct>=0.6 else "📚")
        tk.Label(inn, text=r_icon,
                 font=("Segoe UI Emoji",48),
                 bg="#2a3a2a").pack(pady=(16, 4))
        tk.Label(inn,
                 text=f"{score} / {total} Best Decisions",
                 font=_retro(20, "bold"),
                 bg=C["bg"], fg=C["white"]).pack()
        tk.Label(inn, text=f"⚡ {self._total_xp} XP earned",
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["xp"]).pack(pady=(4, 12))

        # Per-scenario recap
        tk.Label(inn, text="Decision Recap",
                 font=_retro(12, "bold"),
                 bg=C["bg"], fg=C["accent"],
                 anchor="w").pack(fill="x", pady=(0, 6))

        for i, r in enumerate(self._results):
            pos  = r["outcome"].get("positive", False)
            bc   = C["correct"] if pos else C["wrong"]
            icon = "✅" if pos else "❌"
            row  = tk.Frame(inn, bg=C["card"], padx=12, pady=8,
                            highlightbackground=bc, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row,
                     text=f"{icon}  Scenario {i+1}: {r['outcome']['title']}",
                     font=_retro(10, "bold"),
                     bg=C["card"], fg=bc,
                     wraplength=366).pack(anchor="w")
            tk.Label(row,
                     text=f"{r['p1']}: {r['p1_choice']}   {r['p2']}: {r['p2_choice']}   ⚡+{r['outcome'].get('xp',0)}",
                     font=_retro(9),
                     bg=C["card"], fg=C["grey"]).pack(anchor="w")

        tk.Label(inn, text="", bg=C["bg"]).pack()

        Btn(inn, "🔁  Play Again",
            self._retry,
            bg=C["accent2"], fg=C["white"], w=250, fs=12,
            pad_bg=C["bg"]).pack(pady=(4, 6))
        Btn(inn, "🏠  Level Select",
            lambda: self.app.show("level_select"),
            bg=C["card"], fg=C["white"], w=250, fs=12,
            pad_bg=C["bg"]).pack(pady=(0, 24))

    def _retry(self):
        SFX.play("start")
        self.app.quiz_index   = 0
        self.app.quiz_score   = 0
        self._total_xp        = 0
        self._results         = []
        self._p1_choice       = None
        self._p2_choice       = None
        self._build()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()


# ══════════════════════════════════════════════════════════════════════════════
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
        total = len(lvl["questions"])
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
            ("beginner",     all(x in completed for x in [1,2])),
            ("intermediate", all(x in completed for x in [3,4])),
            ("expert",       all(x in completed for x in [5,6])),
            ("deciwise",     all(x in completed for x in range(1,7))),
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
        total   = len(lvl["questions"])
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
                 bg="#1a1a0a" if pct>=0.6 else "#1a0a0a").pack()
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
