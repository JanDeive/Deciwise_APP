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

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
QUESTIONS_DB = os.path.join(DATA_DIR, "questions.json")
PROGRESS_DB  = os.path.join(DATA_DIR, "progress.json")

# ── Palette  (Light Green / Mint theme) ──────────────────────────────────────
C = {
    "bg":        "#f0faf2",   # near-white mint background
    "card":      "#ffffff",   # pure white cards
    "card2":     "#e8f5eb",   # soft mint card variant
    "accent":    "#1e8449",   # deep green accent
    "accent2":   "#27ae60",   # medium green
    "accent3":   "#a9dfbf",   # pale green highlight
    "easy":      "#1e8449",   # easy level colour
    "medium":    "#d68910",   # amber medium
    "hard":      "#cb4335",   # red hard
    "expert":    "#7d3c98",   # purple expert
    "white":     "#1a1a1a",   # near-black for text on light bg
    "grey":      "#5d6d7e",   # mid grey text
    "correct":   "#1e8449",   # correct green
    "wrong":     "#cb4335",   # wrong red
    "gold":      "#d4ac0d",   # gold stars (slightly darker for light bg)
    "silver":    "#808b96",   # silver
    "bronze":    "#a04000",   # bronze
    "locked":    "#d5dbdb",   # light grey for locked elements
    "dark":      "#f0faf2",   # matches bg (used for button text bg)
    "timer_ok":  "#1e8449",   # timer green
    "timer_warn":"#d68910",   # timer amber
    "timer_bad": "#cb4335",   # timer red
    "xp":        "#1a6fad",   # XP blue (darker for light bg)
    "lives":     "#cb4335",   # lives red
    "banner":    "#d5f0de",   # light mint banner/header strip
}

# Timer seconds per difficulty
TIMER = {"Easy": 30, "Medium": 22, "Hard": 16}

# XP rewards
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
        self._cv.bind_all("<MouseWheel>",
            lambda e: self._cv.yview_scroll(int(-1*(e.delta/120)), "units"))
    def top(self): self._cv.yview_moveto(0)

# ── Styled button factory ─────────────────────────────────────────────────────
def Btn(parent, text, cmd, bg=None, fg=None, w=None, h=None,
        fs=12, r=14, pad_bg=None):
    bg  = bg  or C["accent"]
    fg  = fg  or C["dark"]
    pad_bg = pad_bg or C["bg"]
    f   = tk.Frame(parent, bg=pad_bg)
    fnt = tkfont.Font(family="Segoe UI", size=fs, weight="bold")
    bw  = w or (fnt.measure(text)+60)
    bh  = h or (fs*2+20)

    cv = tk.Canvas(f, width=bw, height=bh, bg=pad_bg, highlightthickness=0)
    cv.pack()

    def draw(color=bg):
        cv.delete("all")
        rr(cv, 2,2, bw-2,bh-2, r=r, fill=color, outline="")
        cv.create_text(bw//2, bh//2, text=text, fill=fg, font=fnt)

    draw()
    cv.bind("<Enter>",    lambda e: draw(_darken(bg,0.82)))
    cv.bind("<Leave>",    lambda e: draw(bg))
    cv.bind("<Button-1>", lambda e: [draw(_darken(bg,0.65)),
                                      f.after(100, lambda: draw(bg)), cmd()])
    f._cv   = cv
    f._draw = draw
    f._bg   = bg
    f._fg   = fg
    f._fnt  = fnt
    f._bw   = bw
    f._bh   = bh
    f._text = text   # store label so animations can redraw it
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
        self.player_name   = ""
        self.current_level = None
        self.quiz_index    = 0
        self.quiz_score    = 0
        self.quiz_answers  = []
        self.lives         = MAX_LIVES
        self.total_xp_session = 0
        self.fast_answers  = 0   # for speedster badge

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
        }
        self._frame = screens[name](self, self, **kw)
        self._frame.pack(fill="both", expand=True)

    def start_level(self):
        """Reset per-level quiz state and go to quiz."""
        self.quiz_index   = 0
        self.quiz_score   = 0
        self.quiz_answers = []
        self.lives        = MAX_LIVES
        self.fast_answers = 0
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
        body.pack(fill="both", expand=True, padx=40)

        tk.Label(body, text="Family Planning Quiz",
                 font=("Segoe UI", 13), bg=C["bg"],
                 fg=C["grey"]).pack(pady=(0,4))

        sep = tk.Canvas(body, width=260, height=3,
                        bg=C["bg"], highlightthickness=0)
        sep.pack(pady=(0,20))
        sep.create_rectangle(0,0,260,3, fill=C["accent2"], outline="")

        # Name entry
        tk.Label(body, text="Enter Your Name",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["bg"], fg=C["white"]).pack()
        self._name_var = tk.StringVar()
        # Load saved name
        try:
            p = load_json(PROGRESS_DB)
            self._name_var.set(p.get("player_name",""))
        except Exception:
            pass

        entry = tk.Entry(body, textvariable=self._name_var,
                         font=("Segoe UI", 13),
                         bg=C["card"], fg=C["white"],
                         insertbackground=C["accent"],
                         relief="flat", bd=0,
                         highlightbackground=C["accent2"],
                         highlightthickness=1,
                         justify="center")
        entry.pack(fill="x", ipady=8, pady=(6,24))
        entry.focus()
        entry.bind("<Return>", lambda e: self._go())

        btn = Btn(body, "  PLAY  ▶", self._go,
                  bg=C["accent"], fg=C["dark"], w=240, fs=14, pad_bg=C["bg"])
        btn.pack(pady=(0,12))

        # Nav row
        nav = tk.Frame(body, bg=C["bg"])
        nav.pack()
        Btn(nav, "🏆 Leaderboard",
            lambda: self.app.show("leaderboard"),
            bg=C["card2"], fg=C["white"], w=160, fs=10,
            pad_bg=C["bg"]).pack(side="left", padx=6)
        Btn(nav, "🎖 Badges",
            lambda: self.app.show("badges"),
            bg=C["card2"], fg=C["white"], w=160, fs=10,
            pad_bg=C["bg"]).pack(side="left", padx=6)

        tk.Label(self, text="v2.0  |  DeciWise Capstone Edition",
                 font=("Segoe UI", 8), bg=C["bg"],
                 fg=C["locked"]).pack(side="bottom", pady=8)

    def _draw_header(self):
        cv = self._cv
        cv.delete("all")
        # Background gradient (simulated with rectangles)
        for i in range(40):
            ratio = i / 40
            col = _lerp(C["bg"], C["accent3"], ratio*0.6)
            cv.create_rectangle(0, i*5, WINDOW_W, i*5+6,
                                 fill=col, outline="")
        cv.create_text(WINDOW_W//2, 80, text="DeciWise",
                        font=("Segoe UI", 42, "bold"),
                        fill=C["accent"])
        cv.create_text(WINDOW_W//2, 128, text="🌿",
                        font=("Segoe UI Emoji", 36))
        cv.create_text(WINDOW_W//2, 175, text="Learn • Decide • Grow",
                        font=("Segoe UI", 11), fill=C["grey"])

    def _go(self):
        name = self._name_var.get().strip() or "Player"
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
# SCREEN — Level Select  (Act-based journey map)
# ══════════════════════════════════════════════════════════════════════════════
class LevelSelectScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self._build()

    def _build(self):
        p         = load_json(PROGRESS_DB)
        levels    = load_json(QUESTIONS_DB)["levels"]
        unlocked  = p.get("unlocked_levels", [1])
        completed = p.get("completed_levels", [])
        scores    = p.get("high_scores", {})
        total_xp  = p.get("total_xp", 0)
        lvl_map   = {l["id"]: l for l in levels}

        # ── Top bar ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["banner"], pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌿 DeciWise",
                 font=("Segoe UI", 15, "bold"),
                 bg=C["banner"], fg=C["accent"]).pack(side="left", padx=14)
        # XP pill
        xp_f = tk.Frame(hdr, bg=C["banner"])
        xp_f.pack(side="right", padx=14)
        tk.Label(xp_f, text=f"⚡ {total_xp} XP",
                 font=("Segoe UI", 11, "bold"),
                 bg=C["banner"], fg=C["xp"]).pack(side="left")
        name = self.app.player_name or p.get("player_name","Player")
        tk.Label(hdr, text=f"👤 {name}",
                 font=("Segoe UI", 10),
                 bg=C["banner"], fg=C["grey"]).pack(side="right", padx=4)

        # ── Scrollable body ───────────────────────────────────────────────
        sf = ScrollFrame(self, bg=C["bg"])
        sf.pack(fill="both", expand=True)
        inner = sf.inner

        tk.Label(inner, text="Your Learning Journey",
                 font=("Segoe UI", 12, "bold"),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(14,2))

        total_stars = sum(scores.get(str(i),{}).get("stars",0)
                          for i in range(1,7))
        tk.Label(inner, text=f"⭐ {total_stars} / 18 stars",
                 font=("Segoe UI", 10),
                 bg=C["bg"], fg=C["gold"]).pack(pady=(0,12))

        # ── Act sections ─────────────────────────────────────────────────
        for act_id, (act_label, act_title, act_color, lids) in ACT_MAP.items():
            act_done = all(lid in completed for lid in lids)
            act_open = any(lid in unlocked  for lid in lids)

            # Act header
            ah = tk.Frame(inner, bg=_darken(act_color, 0.25), pady=8)
            ah.pack(fill="x", padx=10, pady=(8,0))
            tk.Label(ah, text=f"{act_label}  ·  {act_title}",
                     font=("Segoe UI", 12, "bold"),
                     bg=_darken(act_color, 0.25),
                     fg=act_color).pack(side="left", padx=12)
            if act_done:
                tk.Label(ah, text="✔ COMPLETE",
                         font=("Segoe UI", 10, "bold"),
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

        outer = tk.Frame(parent, bg=C["bg"], pady=4, padx=14)
        outer.pack(fill="x")

        card = tk.Frame(outer, bg=bg, padx=14, pady=10,
                        highlightbackground=act_color if is_open else bg,
                        highlightthickness=1 if is_open else 0)
        card.pack(fill="x")

        row1 = tk.Frame(card, bg=bg)
        row1.pack(fill="x")

        # Level number circle
        num_cv = tk.Canvas(row1, width=32, height=32,
                            bg=bg, highlightthickness=0)
        num_cv.pack(side="left", padx=(0,8))
        rr(num_cv, 1,1,31,31, r=16,
           fill=act_color if is_open else C["locked"])
        num_cv.create_text(16,16, text=str(lid),
                            fill=C["dark"] if is_open else C["grey"],
                            font=("Segoe UI",11,"bold"))

        info = tk.Frame(row1, bg=bg)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=lvl["title"],
                 font=("Segoe UI",12,"bold"),
                 bg=bg, fg=C["white"] if is_open else C["grey"]).pack(anchor="w")
        tk.Label(info, text=f"{lvl['difficulty']}  |  5 Questions  |  ⏱ {TIMER[lvl['difficulty']]}s each",
                 font=("Segoe UI",9),
                 bg=bg, fg=diff_color if is_open else C["locked"]).pack(anchor="w")

        if is_open:
            status = tk.Frame(row1, bg=bg)
            status.pack(side="right")
            if is_done:
                tk.Label(status, text=f"⭐"*stars_n+"☆"*(3-stars_n),
                         font=("Segoe UI",14), bg=bg, fg=C["gold"]).pack()
                tk.Label(status, text=f"{hs_score}/{hs_total}",
                         font=("Segoe UI",9), bg=bg, fg=C["grey"]).pack()
            else:
                tk.Label(status, text="PLAY ▶",
                         font=("Segoe UI",11,"bold"),
                         bg=bg, fg=C["accent"],
                         cursor="hand2").pack()
        else:
            tk.Label(row1, text="🔒",
                     font=("Segoe UI",16), bg=bg,
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
                             font=("Segoe UI",15,"bold"),
                             bg=C["bg"], fg=C["bg"])
        self._t1.pack()
        self._t2 = tk.Label(self._banner,
                             text=f"{lvl['difficulty']}  ·  {timer_s}s per question  ·  ❤ {MAX_LIVES} lives",
                             font=("Segoe UI",10),
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
                          font=("Segoe UI",9,"bold"), tags="t")
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
                                   font=("Segoe UI Emoji",50), bg=C["bg"])
        self._icon_lbl.pack(pady=(16,4))

        self._hdr_lbl = tk.Label(inn, text="📖  Story",
                                  font=("Segoe UI",12,"bold"),
                                  bg=C["bg"], fg=C["bg"], anchor="w")
        self._hdr_lbl.pack(fill="x", pady=(0,6))

        sc = tk.Frame(inn, bg=C["card"], padx=16, pady=14,
                      highlightbackground=C["accent2"], highlightthickness=1)
        sc.pack(fill="x")
        self._st = tk.Label(sc, text="",
                             font=("Segoe UI",11),
                             bg=C["card"], fg=C["white"],
                             wraplength=368, justify="left", anchor="nw")
        self._st.pack(anchor="w")

        # Info strip
        qn = len(lvl["questions"])
        self._info = tk.Label(inn,
                               text=f"❓ {qn} Questions  |  ⏱ {timer_s}s each  |  ❤ {MAX_LIVES} lives",
                               font=("Segoe UI",10),
                               bg=C["bg"], fg=C["bg"])
        self._info.pack(pady=12)

        # XP info
        xp_est = qn * XP_CORRECT
        self._xp_lbl = tk.Label(inn,
                                  text=f"⚡ Earn up to {xp_est + XP_PERFECT} XP on this level",
                                  font=("Segoe UI",9),
                                  bg=C["bg"], fg=C["bg"])
        self._xp_lbl.pack(pady=(0,8))

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
        if step == 0:
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
            # Restore full interactive drawing once fade is complete
            self._begin_f._draw()
            self._back_f._draw()

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
        qs    = lvl["questions"]
        q     = qs[idx]
        total = len(qs)

        # ── HUD bar ──────────────────────────────────────────────────────
        hud = tk.Frame(self, bg=C["banner"], pady=8)
        hud.pack(fill="x")

        # Lives
        lives_f = tk.Frame(hud, bg=C["banner"])
        lives_f.pack(side="left", padx=10)
        for i in range(MAX_LIVES):
            tk.Label(lives_f,
                     text="❤" if i < app.lives else "🖤",
                     font=("Segoe UI",14),
                     bg=C["banner"],
                     fg=C["lives"] if i < app.lives else C["locked"]).pack(side="left")

        # Question counter
        tk.Label(hud, text=f"Q {idx+1}/{total}",
                 font=("Segoe UI",11,"bold"),
                 bg=C["banner"], fg=C["white"]).pack(side="left", padx=6)

        # XP
        tk.Label(hud, text=f"⚡{app.total_xp_session}",
                 font=("Segoe UI",10,"bold"),
                 bg=C["banner"], fg=C["xp"]).pack(side="left", padx=4)

        # Timer
        self._timer_lbl = tk.Label(hud,
                                    text=f"⏱ {self._t_left}s",
                                    font=("Segoe UI",12,"bold"),
                                    bg=C["banner"], fg=C["timer_ok"])
        self._timer_lbl.pack(side="right", padx=6)

        # Pause
        pk = tk.Label(hud, text="⏸",
                       font=("Segoe UI",14),
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
        tk.Label(inn, text=f"[ {lvl['difficulty']} ]",
                 font=("Segoe UI",10,"bold"),
                 bg=C["bg"], fg=diff_c, anchor="w").pack(fill="x", pady=(10,4))

        # Question card
        qc = tk.Frame(inn, bg=C["card"], padx=16, pady=14,
                      highlightbackground=C["accent2"],
                      highlightthickness=1)
        qc.pack(fill="x")
        tk.Label(qc, text=q["question"],
                 font=("Segoe UI",12,"bold"),
                 bg=C["card"], fg=C["white"],
                 wraplength=360, justify="left").pack(anchor="w")

        tk.Label(inn, text="", bg=C["bg"], height=1).pack()

        # Options
        self._opts = {}
        for opt in q["options"]:
            bf = tk.Frame(inn, bg=C["bg"], pady=3)
            bf.pack(fill="x")
            cv = tk.Canvas(bf, height=50, bg=C["bg"], highlightthickness=0)
            cv.pack(fill="x")
            fnt = tkfont.Font(family="Segoe UI", size=11)

            def draw(cv=cv, text=opt, col=C["accent2"]):
                cv.delete("all")
                w = cv.winfo_width() or WINDOW_W-32
                rr(cv,2,2,w-2,48,r=12, fill=col, outline="")
                cv.create_text(w//2,25, text=text,
                                fill=C["white"], font=fnt, width=w-24)

            cv.bind("<Configure>", lambda e,c=cv,t=opt: draw(c,t))
            cv.bind("<Button-1>",  lambda e,o=opt: self._pick(o))
            cv.bind("<Enter>",  lambda e,c=cv,t=opt: draw(c,t,_darken(C["accent2"])))
            cv.bind("<Leave>",  lambda e,c=cv,t=opt: draw(c,t,C["accent2"]))
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
                                 font=("Segoe UI",10),
                                 bg=C["card"], fg=C["white"],
                                 wraplength=360, justify="left")
        self._expl_l.pack(anchor="w")

        # XP flash (hidden)
        self._xp_f = tk.Frame(inn, bg=C["bg"])
        self._xp_l = tk.Label(self._xp_f, text="",
                               font=("Segoe UI",12,"bold"),
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
                 font=("Segoe UI",28,"bold"),
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
        for opt, (cv, draw_fn) in self._opts.items():
            if opt == correct:       col = C["correct"]
            elif opt == chosen:      col = C["wrong"]
            else:                    col = C["locked"]
            draw_fn(cv, opt, col)
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
        self.after(200, lambda: SFX.play("wrong"))

    def _build(self):
        app = self.app
        lvl = app.current_level

        tk.Label(self, text="💔", font=("Segoe UI Emoji",64),
                 bg=C["bg"]).pack(pady=(80,8))
        tk.Label(self, text="Game Over",
                 font=("Segoe UI",28,"bold"),
                 bg=C["bg"], fg=C["wrong"]).pack()
        tk.Label(self, text=f"You ran out of lives on\nLevel {lvl['id']}: {lvl['title']}",
                 font=("Segoe UI",12),
                 bg=C["bg"], fg=C["grey"],
                 justify="center").pack(pady=10)

        # Score so far
        sc = tk.Frame(self, bg=C["card"], padx=24, pady=16,
                      highlightbackground=C["wrong"], highlightthickness=1)
        sc.pack(padx=40, pady=16)
        q = app.quiz_index
        tk.Label(sc, text=f"{app.quiz_score} / {q}",
                 font=("Segoe UI",26,"bold"),
                 bg=C["card"], fg=C["white"]).pack()
        tk.Label(sc, text="Questions answered correctly",
                 font=("Segoe UI",10),
                 bg=C["card"], fg=C["grey"]).pack()
        tk.Label(sc, text=f"⚡ {app.total_xp_session} XP earned this session",
                 font=("Segoe UI",10,"bold"),
                 bg=C["card"], fg=C["xp"]).pack(pady=(6,0))

        tk.Label(self, text="Don't give up — knowledge saves lives! 💪",
                 font=("Segoe UI",10,"italic"),
                 bg=C["bg"], fg=C["grey"],
                 wraplength=340).pack(pady=6)

        Btn(self, "🔁  Try Again", self._retry,
            bg=C["accent2"], fg=C["white"], w=240, fs=13,
            pad_bg=C["bg"]).pack(pady=(20,8))
        Btn(self, "🏠  Level Select",
            lambda: self.app.show("level_select"),
            bg=C["card"], fg=C["white"], w=240, fs=12,
            pad_bg=C["bg"]).pack()

    def _retry(self):
        SFX.play("start")
        self.app.total_xp_session = 0
        self.app.show("story")


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
        self.after(300, lambda: SFX.play("perfect" if score==total else "complete"))
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

        tk.Label(inn, text=r_icon, font=("Segoe UI Emoji",52),
                 bg=C["bg"]).pack(pady=(20,4))
        tk.Label(inn, text=r_msg, font=("Segoe UI",22,"bold"),
                 bg=C["bg"], fg=C["white"]).pack()
        tk.Label(inn, text=r_sub, font=("Segoe UI",11),
                 bg=C["bg"], fg=C["grey"]).pack(pady=(2,8))

        tk.Label(inn, text="⭐"*stars+"☆"*(3-stars),
                 font=("Segoe UI",32), bg=C["bg"], fg=C["gold"]).pack()

        # Score + XP row
        row = tk.Frame(inn, bg=C["bg"])
        row.pack(fill="x", pady=12)

        sc_f = tk.Frame(row, bg=C["card"], padx=18, pady=12,
                        highlightbackground=C["accent2"], highlightthickness=1)
        sc_f.pack(side="left", expand=True, fill="both", padx=(0,6))
        tk.Label(sc_f, text=f"{score}/{total}",
                 font=("Segoe UI",22,"bold"),
                 bg=C["card"], fg=C["white"]).pack()
        tk.Label(sc_f, text="Correct", font=("Segoe UI",9),
                 bg=C["card"], fg=C["grey"]).pack()

        xp_f = tk.Frame(row, bg=C["card2"], padx=18, pady=12,
                        highlightbackground=C["xp"], highlightthickness=1)
        xp_f.pack(side="left", expand=True, fill="both", padx=(6,0))
        tk.Label(xp_f, text=f"+{app.total_xp_session}",
                 font=("Segoe UI",22,"bold"),
                 bg=C["card2"], fg=C["xp"]).pack()
        tk.Label(xp_f, text="XP Earned", font=("Segoe UI",9),
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
                     font=("Segoe UI",12,"bold"),
                     bg=C["bg"], fg=C["gold"]).pack(anchor="w", pady=(0,4))
            for bk in self._new_badges:
                bd = BADGES[bk]
                bf = tk.Frame(inn, bg=C["card2"], padx=12, pady=8,
                              highlightbackground=C["gold"],
                              highlightthickness=1)
                bf.pack(fill="x", pady=3)
                tk.Label(bf, text=f"{bd['icon']}  {bd['name']}",
                         font=("Segoe UI",11,"bold"),
                         bg=C["card2"], fg=C["gold"]).pack(anchor="w")
                tk.Label(bf, text=bd["desc"],
                         font=("Segoe UI",9),
                         bg=C["card2"], fg=C["grey"]).pack(anchor="w")

        # Answer review
        tk.Label(inn, text="Answer Review",
                 font=("Segoe UI",13,"bold"),
                 bg=C["bg"], fg=C["accent"],
                 anchor="w").pack(fill="x", pady=(8,6))

        for i, a in enumerate(answers):
            is_r = a["is_right"]
            bc   = C["correct"] if is_r else C["wrong"]
            row  = tk.Frame(inn, bg=C["card"], padx=12, pady=8,
                            highlightbackground=bc, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"Q{i+1}: {a['question']}",
                     font=("Segoe UI",10,"bold"),
                     bg=C["card"], fg=C["white"],
                     wraplength=366, justify="left").pack(anchor="w")
            tk.Label(row,
                     text=f"{'✅' if is_r else '❌'}  {a['chosen']}  (⚡+{a.get('xp',0)} XP)",
                     font=("Segoe UI",10),
                     bg=C["card"], fg=bc,
                     wraplength=366, justify="left").pack(anchor="w")
            if not is_r:
                tk.Label(row, text=f"✔ {a['correct']}",
                         font=("Segoe UI",10,"bold"),
                         bg=C["card"], fg=C["easy"],
                         wraplength=366).pack(anchor="w")
            if a.get("explanation"):
                tk.Label(row, text=f"💡 {a['explanation']}",
                         font=("Segoe UI",9),
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
                 font=("Segoe UI",16,"bold"),
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
                     font=("Segoe UI",12),
                     bg=C["bg"], fg=C["grey"],
                     justify="center").pack(pady=60)
        else:
            tk.Label(inn, text="Top 10 Scores",
                     font=("Segoe UI",11),
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
                         font=("Segoe UI",12,"bold"),
                         bg=C["card"], fg=mc).pack(anchor="w")
                tk.Label(left,
                         text=f"Level {entry['level']}  ·  {entry['score']}/{entry['total']}  ·  ⭐{'⭐'*entry['stars']}",
                         font=("Segoe UI",9),
                         bg=C["card"], fg=C["grey"]).pack(anchor="w")

                tk.Label(row,
                         text=f"⚡{entry['xp']} XP",
                         font=("Segoe UI",12,"bold"),
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
                 font=("Segoe UI",15,"bold"),
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
                 font=("Segoe UI",13,"bold"),
                 bg=C["bg"], fg=C["xp"]).pack(pady=(16,4))
        tk.Label(inn, text=f"{len(earned)} / {len(BADGES)} badges unlocked",
                 font=("Segoe UI",10),
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
                     font=("Segoe UI",11,"bold"),
                     bg=bg,
                     fg=C["gold"] if got else C["grey"]).pack(anchor="w")
            tk.Label(info, text=bd["desc"],
                     font=("Segoe UI",9),
                     bg=bg,
                     fg=C["white"] if got else C["locked"]).pack(anchor="w")

            tk.Label(row, text="✔" if got else "🔒",
                     font=("Segoe UI",16),
                     bg=bg,
                     fg=C["correct"] if got else C["grey"]).pack(side="right")

        tk.Label(inn, text="", bg=C["bg"], height=2).pack()


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
