# 🌿 DeciWise — Family Planning Quiz Game
### Capstone Edition

A story-driven, level-based quiz game about **Family Planning**, built with
**Python + Tkinter** (UI) and **pygame** (sound). No internet connection
required after setup — everything runs locally.

---

## 📋 Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | **3.8 – 3.13** | Must be added to PATH during install |
| pygame | **2.6.1** | Only external dependency — for sound |
| Tkinter | built-in | Included with Python on Windows/macOS |

> **Kivy is NOT used.** The game runs on Python's built-in `tkinter` library,
> so no heavyweight framework install is needed.

---

## 🚀 Setup & Run

### Step 1 — Install Python

Download and install Python from the official site:

**https://www.python.org/downloads/**

- Recommended version: **Python 3.11** or **3.13**
- On Windows: tick **"Add Python to PATH"** during installation

Verify it worked by opening a terminal and running:

```bash
python --version
```

You should see something like `Python 3.13.0`.

---

### Step 2 — Clone or Download the Repository

**Option A — Git clone:**
```bash
git clone https://github.com/YOUR_USERNAME/deciwise.git
cd deciwise
```

**Option B — Download ZIP:**
1. Click the green **Code** button on GitHub
2. Select **Download ZIP**
3. Extract the folder
4. Open a terminal inside the extracted folder

---

### Step 3 — Install Dependencies

Install the only required package (pygame for sound effects):

```bash
pip install -r requirements.txt
```

Or install it directly:

```bash
pip install pygame==2.6.1
```

> If `pip` is not found, try `python -m pip install -r requirements.txt`

---

### Step 4 — Run the Game

**Windows (double-click):**
```
run.bat
```

**Any platform (terminal):**
```bash
python main.py
```

The game window will open at 430 × 800 pixels, centered on your screen.

---

## 🗂 Project Structure

```
deciwise/
├── main.py              ← Main game application (all screens & logic)
├── sound.py             ← Synthesized sound effects (no audio files needed)
├── requirements.txt     ← Python dependencies (pygame only)
├── run.bat              ← Windows one-click launcher
├── .gitignore           ← Excludes __pycache__ from the repo
├── README.md            ← This file
└── data/
    ├── questions.json   ← All levels, stories & questions (editable)
    └── progress.json    ← Player progress, scores & badges (auto-generated)
```

---

## 🎮 Game Features

### Content
- **Theme:** Family Planning (contraception, maternal health, reproductive health)
- **6 Levels** grouped into 3 Acts of increasing difficulty
- **Animated story** before each level (typewriter effect, icon bounce, fade-in)
- **5 questions** per level with 4 options each and explanations after every answer

### Acts & Difficulty
| Act | Levels | Difficulty | Timer |
|-----|--------|-----------|-------|
| Act I — Foundations | 1, 2 | Easy | 30s / question |
| Act II — Intermediate | 3, 4 | Medium | 22s / question |
| Act III — Expert | 5, 6 | Hard | 16s / question |

### Mechanics
- ❤ **Lives system** — 3 hearts per level; lose one per wrong answer or timeout
- ⏱ **Countdown timer** — colour-coded (green → amber → red)
- ⚡ **XP system** — earn XP for correct answers and speed bonuses
- ⏸ **Pause** — freeze timer mid-quiz
- 🔒 **Progressive unlocking** — complete a level to unlock the next
- ⭐ **Star ratings** — 1–3 stars per level based on score

### Progression
- 🎖 **7 Badges** — earned by completing acts, perfect scores, and speed runs
- 🏆 **Leaderboard** — top 10 scores saved locally, sorted by XP
- 📊 **All-time XP** — accumulates across all sessions

### Screens
1. **Splash** — name entry, leaderboard and badge shortcuts
2. **Level Select** — act-based journey map with score history
3. **Story** — animated narrative with skip option
4. **Quiz** — timed questions with live HUD (lives, timer, XP, progress bar)
5. **Result** — score, XP, new badges, full answer review
6. **Game Over** — triggered when lives reach zero
7. **Leaderboard** — top 10 with gold/silver/bronze medals
8. **Badges** — gallery of all achievements

---

## 🔊 Sound Effects

All sounds are **synthesized in code** using pygame — no audio files are
bundled. The `sound.py` module generates waveforms at runtime.

| Sound | Trigger |
|---|---|
| `start` | Start game, Begin quiz, Retry |
| `click` | Open level, Next question |
| `correct` | Right answer |
| `wrong` | Wrong answer, Time's up, Game Over |
| `complete` | Result screen (any score) |
| `perfect` | Result screen (100% score) |
| `unlock` | New level unlocked |
| `tick` | Typewriter animation + last 5s countdown |
| `back` | Back / Home navigation |

---

## 🗃 Data Files

### `data/questions.json`
Contains all game content. You can edit this file to change stories, questions,
options, answers, and explanations. Structure:

```json
{
  "levels": [
    {
      "id": 1,
      "title": "Level Title",
      "difficulty": "Easy",
      "difficulty_color": "#2ecc71",
      "story": "The story text shown before the quiz...",
      "story_image": "couple",
      "questions": [
        {
          "question": "Question text?",
          "options": ["A", "B", "C", "D"],
          "answer": "B",
          "explanation": "Why B is correct."
        }
      ]
    }
  ]
}
```

### `data/progress.json`
Auto-generated and updated as you play. **Do not edit manually** unless
resetting progress. To reset all progress, replace the file contents with:

```json
{
  "unlocked_levels": [1],
  "completed_levels": [],
  "high_scores": {},
  "total_xp": 0,
  "badges": [],
  "leaderboard": [],
  "player_name": ""
}
```

---

## ❓ Troubleshooting

**`ModuleNotFoundError: No module named 'pygame'`**
```bash
pip install pygame==2.6.1
```

**`ModuleNotFoundError: No module named 'tkinter'`**
- Windows: reinstall Python and make sure "tcl/tk" is checked during setup
- Linux: `sudo apt-get install python3-tk`
- macOS: reinstall Python from python.org (the Homebrew version sometimes omits tkinter)

**`python` not recognized in terminal**
- Re-run the Python installer and check **"Add Python to PATH"**
- Or use the full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe main.py`

**Game window does not appear**
- Make sure you are running from inside the project folder
- Try: `cd path\to\deciwise` then `python main.py`

**Sound not working**
- This is non-fatal — the game still runs without sound if pygame fails
- Check that pygame installed correctly: `python -c "import pygame; print(pygame.version.ver)"`

---

## 👥 Built With

| Tool | Purpose |
|---|---|
| Python 3.x | Core language |
| Tkinter | GUI framework (built-in) |
| pygame | Sound synthesis |
| JSON | Data storage (questions + progress) |

---

## 📄 License

This project is submitted as a capstone academic requirement.  
Content is based on publicly available family planning health guidelines
(WHO, DOH Philippines).
