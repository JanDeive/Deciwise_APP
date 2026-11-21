package com.deciwise.mobile

import android.app.Activity
import android.content.Context
import android.content.res.ColorStateList
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.media.AudioManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.media.ToneGenerator
import android.os.Bundle
import android.os.CountDownTimer
import android.os.Handler
import android.os.Looper
import android.text.InputFilter
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.inputmethod.EditorInfo
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.GridLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.max
import kotlin.math.roundToInt
import kotlin.math.sin

private data class LevelScore(val score: Int, val total: Int, val stars: Int)
private data class BoardEntry(
    val name: String,
    val level: Int,
    val score: Int,
    val total: Int,
    val stars: Int
)
private data class AnswerReview(
    val question: String,
    val chosen: String,
    val correct: String,
    val isCorrect: Boolean,
    val explanation: String
)
private data class GameProgress(
    val unlocked: MutableSet<Int> = mutableSetOf(1),
    val completed: MutableSet<Int> = mutableSetOf(),
    val highScores: MutableMap<Int, LevelScore> = mutableMapOf(),
    val badges: MutableSet<String> = mutableSetOf(),
    val leaderboard: MutableList<BoardEntry> = mutableListOf()
)

private data class CrosswordPosition(val row: Int, val column: Int)
private enum class CrosswordDirection(val label: String) {
    ACROSS("Across"),
    DOWN("Down")
}
private data class CrosswordPlacement(
    val word: String,
    val direction: CrosswordDirection,
    val row: Int,
    val column: Int
)
private data class CrosswordWord(
    val word: String,
    val direction: CrosswordDirection,
    val number: Int,
    val hint: String,
    val cells: List<CrosswordPosition>
)

private const val JIGSAW_COLUMNS = 4
private const val JIGSAW_ROWS = 3
private const val JIGSAW_PIECES = JIGSAW_COLUMNS * JIGSAW_ROWS
private const val JOTTO_MAX_GUESSES = 6
private const val CROSSWORD_ROWS = 13
private const val CROSSWORD_COLUMNS = 11
private val CROSSWORD_PLACEMENTS = listOf(
    CrosswordPlacement("FERTILE", CrosswordDirection.DOWN, 0, 1),
    CrosswordPlacement("SPERM", CrosswordDirection.DOWN, 0, 7),
    CrosswordPlacement("CYCLE", CrosswordDirection.DOWN, 0, 10),
    CrosswordPlacement("CERVIX", CrosswordDirection.ACROSS, 1, 0),
    CrosswordPlacement("HORMONE", CrosswordDirection.ACROSS, 4, 4),
    CrosswordPlacement("OVULATION", CrosswordDirection.DOWN, 4, 8),
    CrosswordPlacement("TEMPERATURE", CrosswordDirection.ACROSS, 6, 0),
    CrosswordPlacement("MUCUS", CrosswordDirection.DOWN, 6, 2),
    CrosswordPlacement("SYMPTOM", CrosswordDirection.ACROSS, 9, 4),
    CrosswordPlacement("CHARTING", CrosswordDirection.ACROSS, 12, 2)
)

class MainActivity : Activity() {
    private enum class Screen {
        HOME, LEVELS, STORY, QUIZ, HANGMAN, JIGSAW, CROSSWORD, JOTTO,
        RESULT, GAME_OVER, BADGES, LEADERBOARD
    }

    private val colors = Colors
    private lateinit var levels: List<GameLevel>
    private lateinit var progress: GameProgress
    private lateinit var page: LinearLayout
    private var screen = Screen.HOME
    private var currentLevel: GameLevel? = null
    private var selectedChapterIndex = 0
    private var chosenDifficulty = "Beginner"
    private var questions = emptyList<GameQuestion>()
    private var questionIndex = 0
    private var levelScore = 0
    private var lives = 3
    private var fastAnswers = 0
    private var review = mutableListOf<AnswerReview>()
    private var questionFeedback: AnswerReview? = null
    private var questionTimer: CountDownTimer? = null
    private var questionDurationMs = 0L
    private var questionRemainingMs = 0L
    private var lastTickSecond = Int.MAX_VALUE
    private var timerLabel: TextView? = null
    private var hangmanIndex = 0
    private var hangmanWrong = 0
    private var hangmanGuessed = mutableSetOf<Char>()
    private var hangmanRoundFinished = false
    private var jigsawTiles = emptyList<Bitmap>()
    private var jigsawOrder = mutableListOf<Int>()
    private var jigsawPlacements = mutableMapOf<Int, Int>()
    private var selectedJigsawPiece: Int? = null
    private var jigsawStatus = ""
    private var jigsawCompleted = false
    private var crosswordFeedback = ""
    private var crosswordWords = emptyList<CrosswordWord>()
    private val crosswordSolution = mutableMapOf<CrosswordPosition, Char>()
    private val crosswordLetters = mutableMapOf<CrosswordPosition, Char>()
    private val crosswordAcrossByCell = mutableMapOf<CrosswordPosition, Int>()
    private val crosswordDownByCell = mutableMapOf<CrosswordPosition, Int>()
    private val crosswordCellViews = mutableMapOf<CrosswordPosition, EditText>()
    private val crosswordCellFrames = mutableMapOf<CrosswordPosition, FrameLayout>()
    private var crosswordActiveWordIndex = 0
    private var crosswordActiveCell: CrosswordPosition? = null
    private var crosswordActiveTitleView: TextView? = null
    private var crosswordActiveClueView: TextView? = null
    private var crosswordDirectionButton: Button? = null
    private var crosswordStatusView: TextView? = null
    private var crosswordChecked = false
    private var crosswordSolved = false
    private var crosswordProgrammaticChange = false
    private var jottoSecret = WordClue("", "")
    private var jottoGuesses = mutableListOf<Pair<String, Int>>()
    private var jottoFeedback = ""
    private var jottoInputText = ""
    private var jottoStatusView: TextView? = null
    private var jottoFinished = false
    private var jottoWon = false
    private var musicTrack: AudioTrack? = null
    private val soundHandler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = colors.background
        window.navigationBarColor = colors.background
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
        levels = GameData.readLevels(this)
        progress = readProgress(this)
        if (progress.unlocked.addAll(levels.map { it.id })) writeProgress()
        renderHome()
    }

    override fun onResume() {
        super.onResume()
        startMusic()
    }

    override fun onPause() {
        stopMusic()
        questionTimer?.cancel()
        super.onPause()
    }

    override fun onDestroy() {
        stopMusic()
        super.onDestroy()
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        playBackSound()
        when (screen) {
            Screen.HOME -> super.onBackPressed()
            Screen.LEVELS, Screen.BADGES, Screen.LEADERBOARD -> renderHome()
            Screen.STORY, Screen.QUIZ, Screen.HANGMAN, Screen.JIGSAW, Screen.CROSSWORD,
            Screen.JOTTO, Screen.RESULT, Screen.GAME_OVER -> renderLevels()
        }
    }

    private fun beginPage(title: String): LinearLayout {
        questionTimer?.cancel()
        timerLabel = null
        val scroll = ScrollView(this).apply {
            isFillViewport = true
            setBackgroundColor(colors.background)
        }
        page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(12), dp(20), dp(28))
        }
        scroll.addView(page)
        setContentView(scroll)
        if (title.isNotEmpty()) {
            val header = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            if (screen != Screen.HOME) {
                val back = TextView(this).apply {
                    text = "‹  Back"
                    textSize = 15f
                    setTextColor(colors.accent)
                    setTypeface(null, Typeface.BOLD)
                    setPadding(0, dp(8), dp(12), dp(8))
                    setOnClickListener { onBackPressed() }
                }
                header.addView(back)
            }
            val heading = TextView(this).apply {
                text = title
                textSize = 25f
                setTextColor(colors.ink)
                setTypeface(null, Typeface.BOLD)
            }
            header.addView(
                heading,
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
            )
            page.addView(header)
            space(page, 8)
        }
        return page
    }

    private fun renderHome() {
        screen = Screen.HOME
        val body = beginPage("")
        val cleared = progress.completed.size
        val completionRatio = cleared.toFloat() / levels.size.coerceAtLeast(1)
        val totalStars = progress.highScores.values.sumOf { it.stars }
        val hero = card(body, colors.banner) {
            val logo = TextView(this@MainActivity).apply {
                text = "💑"
                textSize = 30f
                gravity = Gravity.CENTER
                background = GradientDrawable().apply {
                    shape = GradientDrawable.OVAL
                    setColor(this@MainActivity.colors.accent)
                }
            }
            addView(logo, LinearLayout.LayoutParams(dp(72), dp(72)).apply {
                gravity = Gravity.CENTER_HORIZONTAL
                bottomMargin = dp(7)
            })
            text(this, "DeciWise", 28f, colors.accent, true).gravity = Gravity.CENTER
            text(this, "Family Planning Quiz", 14f, colors.muted).gravity = Gravity.CENTER
            val dots = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
            }
            listOf(colors.accent, colors.accent2, colors.border, colors.accent2, colors.accent)
                .forEach { dotColor ->
                    val dot = View(this@MainActivity).apply {
                        background = GradientDrawable().apply {
                            shape = GradientDrawable.OVAL
                            setColor(dotColor)
                        }
                    }
                    dots.addView(dot, LinearLayout.LayoutParams(dp(8), dp(8)).apply {
                        leftMargin = dp(4)
                        rightMargin = dp(4)
                    })
                }
            addView(dots, matchWidth())
        }
        hero.minimumHeight = dp(190)
        val journey = card(body) {
            val heading = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            val label = TextView(this@MainActivity).apply {
                text = "YOUR ADVENTURE"
                textSize = 13f
                setTextColor(colors.muted)
                setTypeface(typeface, Typeface.BOLD)
            }
            heading.addView(label, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            val badge = TextView(this@MainActivity).apply {
                text = "🎖 ${progress.badges.size} BADGES"
                textSize = 11f
                setTextColor(colors.gold)
                setTypeface(typeface, Typeface.BOLD)
                setPadding(dp(8), dp(4), dp(8), dp(4))
                background = roundedDrawable(colors.peach, 8)
            }
            heading.addView(badge)
            addView(heading)

            val stats = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            val questCount = TextView(this@MainActivity).apply {
                text = "$cleared / ${levels.size} quests cleared"
                textSize = 15f
                setTextColor(colors.ink)
                setTypeface(typeface, Typeface.BOLD)
            }
            stats.addView(questCount, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            val stars = TextView(this@MainActivity).apply {
                text = "⭐ $totalStars / ${levels.size * 3}"
                textSize = 14f
                setTextColor(colors.gold)
                setTypeface(typeface, Typeface.BOLD)
            }
            stats.addView(stars)
            addView(stats, matchWidth())
            addProgressTrack(this, completionRatio, colors.accent)

            val next = levels.firstOrNull {
                it.id in progress.unlocked && it.id !in progress.completed
            }
            text(
                this,
                if (next == null) "ALL QUESTS CLEARED · AMAZING!"
                else "NEXT QUEST · ${next.title}",
                13f,
                colors.accent,
                true
            )
        }
        journey.minimumHeight = dp(110)
        actionButton(
            body,
            when {
                cleared == levels.size && levels.isNotEmpty() -> "Replay Adventure  →"
                cleared > 0 -> "Continue Adventure  →"
                else -> "Start Your Adventure  →"
            },
            colors.accent
        ) { renderLevels() }
        actionButton(body, "🎖  Badges & Achievements", colors.peach) { renderBadges() }
        text(body, "v2.0  ·  DeciWise  ·  Family Planning Quiz", 11f, colors.muted)
    }

    private fun renderLevels() {
        screen = Screen.LEVELS
        val body = beginPage("Choose your next quest")
        val chapters = listOf(
            Triple("Planning", "Chapter 1 · Family Planning", levels.filter { it.id in 1..2 }),
            Triple("Methods", "Chapter 2 · Contraceptives", levels.filter { it.id in 3..4 }),
            Triple("Fertility", "Chapter 3 · Fertility Awareness", levels.filter { it.id in 5..6 })
        )
        val tabs = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
        }
        chapters.forEachIndexed { index, chapter ->
            val completedCount = chapter.third.count { it.id in progress.completed }
            val active = index == selectedChapterIndex
            val tab = Button(this).apply {
                text = "${chapter.first}\n$completedCount/${chapter.third.size}"
                textSize = 12f
                isAllCaps = false
                setTextColor(if (active) Color.WHITE else colors.muted)
                backgroundTintList = ColorStateList.valueOf(
                    if (active) chapterColor(index) else colors.card
                )
                minWidth = 0
                minimumWidth = 0
                setPadding(dp(3), dp(5), dp(3), dp(5))
                setOnClickListener {
                    playClickSound()
                    selectedChapterIndex = index
                    renderLevels()
                }
            }
            tabs.addView(
                tab,
                LinearLayout.LayoutParams(0, dp(52), 1f).apply {
                    leftMargin = dp(3)
                    rightMargin = dp(3)
                }
            )
        }
        body.addView(tabs, matchWidth())
        val chapter = chapters[selectedChapterIndex]
        val chapterLevels = chapter.third
        val doneCount = chapterLevels.count { it.id in progress.completed }
        val chapterColor = chapterColor(selectedChapterIndex)
        text(
            body,
            "${chapter.second}  ·  $doneCount of ${chapterLevels.size} done",
            15f,
            colors.muted
        )
        val totalStars = progress.highScores.values.sumOf { it.stars }
        text(body, "★ $totalStars / ${levels.size * 3} stars", 13f, colors.gold, true)
        chapterLevels.forEach { level -> levelCard(body, level, chapterColor) }
    }

    private fun levelCard(parent: LinearLayout, level: GameLevel, chapterColor: Int) {
        val unlocked = level.id in progress.unlocked
        val score = progress.highScores[level.id]
        val panel = card(parent, if (unlocked) colors.card else colors.locked) {}
        val row = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val number = TextView(this).apply {
            text = level.id.toString()
            textSize = 17f
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            setTypeface(typeface, Typeface.BOLD)
            background = roundedDrawable(
                if (unlocked) chapterColor else colors.lockedText,
                7
            )
        }
        row.addView(number, LinearLayout.LayoutParams(dp(42), dp(48)))
        val titleColumn = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(12), 0, 0, 0)
        }
        val title = TextView(this).apply {
            text = level.title
            textSize = 16f
            setTextColor(if (unlocked) colors.ink else colors.lockedText)
            setTypeface(typeface, Typeface.BOLD)
        }
        titleColumn.addView(title)
        val status = when {
            score != null -> "QUEST CLEARED  ·  Best ${score.score}/${score.total}"
            unlocked -> "QUEST AVAILABLE"
            else -> "LOCKED  ·  Finish the previous quest"
        }
        titleColumn.addView(TextView(this).apply {
            text = status
            textSize = 12f
            setTextColor(if (unlocked) colors.muted else colors.lockedText)
        })
        row.addView(
            titleColumn,
            LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
        )
        panel.addView(row, matchWidth())

        val chips = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(0, dp(9), 0, 0)
        }
        addChip(chips, level.difficulty, difficultyColor(level.difficulty), Color.WHITE)
        val mode = modeLabel(level.quizType)
        addChip(chips, mode.second, colors.peach, modeColor(level.quizType))
        panel.addView(chips, matchWidth())

        if (score != null) {
            text(panel, "★".repeat(score.stars) + "☆".repeat(3 - score.stars),
                15f, colors.gold, true)
        }
        if (unlocked) {
            actionButton(panel, if (score == null) "⚔  Start Quest  →" else "★  Replay",
                chapterColor) {
                currentLevel = level
                chosenDifficulty = defaultDifficulty(level)
                renderStory()
            }
        }
    }

    private fun addChip(parent: LinearLayout, label: String, background: Int, foreground: Int) {
        val chip = TextView(this).apply {
            text = label
            textSize = 11f
            setTextColor(foreground)
            setTypeface(typeface, Typeface.BOLD)
            setPadding(dp(9), dp(4), dp(9), dp(4))
            this.background = roundedDrawable(background, 6)
        }
        parent.addView(chip, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply {
            rightMargin = dp(7)
        })
    }

    private fun chapterColor(index: Int) = when (index) {
        1 -> colors.chapterTwo
        2 -> colors.chapterThree
        else -> colors.accent
    }

    private fun defaultDifficulty(level: GameLevel) = when (level.difficulty.lowercase()) {
        "medium" -> "Intermediate"
        "hard" -> "Difficult"
        else -> "Beginner"
    }

    private fun difficultyColor(difficulty: String) = when (difficulty.lowercase()) {
        "medium", "intermediate" -> colors.medium
        "hard", "difficult" -> colors.hard
        else -> colors.easy
    }

    private fun modeLabel(quizType: String): Pair<String, String> = when (quizType) {
        "kahoot" -> "🎮 KAHOOT" to "Kahoot"
        "myth_fact" -> "🧠 MYTH OR FACT" to "Myth/Fact"
        "hangman" -> "🎯 HANGMAN" to "Hangman"
        "jigsaw" -> "🧩 JIGSAW PUZZLE" to "Jigsaw"
        "crossword" -> "📝 CROSSWORD" to "Crossword"
        "jotto" -> "🔤 JOTTO" to "Jotto"
        else -> "📝 QUIZ" to "Quiz"
    }

    private fun modeColor(quizType: String) = when (quizType) {
        "kahoot" -> colors.kahootRed
        "myth_fact" -> colors.myth
        "hangman" -> colors.kahootBlue
        "jigsaw" -> colors.medium
        "crossword" -> colors.successInk
        "jotto" -> colors.wrong
        else -> colors.accent
    }

    private fun questionCount(level: GameLevel) = when (level.quizType) {
        "kahoot" -> level.kahoot.size
        "myth_fact" -> level.mythFact.size
        "hangman" -> level.hangman.size
        "jigsaw" -> JIGSAW_PIECES
        "crossword" -> level.crossword.size
        "jotto" -> level.jotto.size
        else -> when (chosenDifficulty) {
            "Intermediate" -> level.intermediate.size
            "Difficult" -> level.difficult.size
            else -> level.beginner.size
        }
    }

    private fun timerFor(level: GameLevel) = when (level.quizType) {
        "kahoot" -> 20
        "myth_fact" -> 25
        else -> when (chosenDifficulty) {
            "Intermediate" -> 22
            "Difficult" -> 16
            else -> 30
        }
    }

    private fun renderStory() {
        val level = currentLevel ?: return renderLevels()
        screen = Screen.STORY
        val body = beginPage("Level ${level.id}")
        card(body) {
            text(this, storyIcon(level.storyImage), 44f, colors.accent, true)
            text(this, level.title, 22f, colors.ink, true)
            val levelDetails = if (level.quizType in setOf("jigsaw", "crossword", "jotto")) {
                level.difficulty
            } else {
                "${level.difficulty} · ${timerFor(level)}s per question · ❤ 3 lives"
            }
            text(this, levelDetails, 13f, colors.accent, true)
            text(this, level.story, 16f, colors.ink)
        }
        val activitySummary = when (level.quizType) {
            "jigsaw" -> "🧩 $JIGSAW_PIECES picture pieces"
            "crossword" -> "📝 ${questionCount(level)} crossword clues"
            "jotto" -> "🔤 ${questionCount(level)} Jotto words"
            else -> "❓ ${questionCount(level)} questions"
        }
        text(body, "$activitySummary  |  ❤ 3 lives", 14f, colors.muted)
        when (level.quizType) {
            "kahoot" -> {
                text(body, "🎮  KAHOOT STYLE  —  20s per question", 14f, colors.kahootRed, true)
                actionButton(body, "START KAHOOT  ▶", colors.kahootRed) { startLevel() }
            }
            "myth_fact" -> {
                text(body, "🧠  MYTH OR FACT  —  Choose wisely!", 14f, colors.myth, true)
                actionButton(body, "START QUIZ  ▶", colors.myth) { startLevel() }
            }
            "hangman", "jigsaw", "crossword", "jotto" -> {
                val mode = modeLabel(level.quizType)
                text(body, mode.first, 16f, colors.accent, true)
                actionButton(body, "START ${mode.second}  ▶", colors.kahootBlue) { startLevel() }
            }
            else -> {
                text(body, "── CHOOSE DIFFICULTY ──", 13f, colors.accent, true)
                val difficultyRow = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                }
                listOf(
                    Triple("Beginner", colors.easy, "30s"),
                    Triple("Intermediate", colors.medium, "22s"),
                    Triple("Difficult", colors.hard, "16s")
                ).forEach { (name, color, timer) ->
                    val button = Button(this).apply {
                        text = "${if (chosenDifficulty == name) "✓ " else ""}$name\n$timer"
                        textSize = 11f
                        isAllCaps = false
                        setTextColor(Color.WHITE)
                        backgroundTintList = ColorStateList.valueOf(color)
                        minWidth = 0
                        minimumWidth = 0
                        minHeight = dp(58)
                        setPadding(dp(2), dp(4), dp(2), dp(4))
                        setOnClickListener {
                            playClickSound()
                            chosenDifficulty = name
                            renderStory()
                        }
                    }
                    difficultyRow.addView(
                        button,
                        LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f).apply {
                            leftMargin = dp(3)
                            rightMargin = dp(3)
                        }
                    )
                }
                body.addView(difficultyRow, matchWidth())
                actionButton(body, "START QUIZ  ▶", colors.accent) { startLevel() }
            }
        }
    }

    private fun startLevel() {
        val level = currentLevel ?: return renderLevels()
        questionTimer?.cancel()
        levelScore = 0
        lives = 3
        fastAnswers = 0
        review.clear()
        questionIndex = 0
        questionFeedback = null
        crosswordFeedback = ""
        crosswordWords = emptyList()
        crosswordSolution.clear()
        crosswordLetters.clear()
        crosswordAcrossByCell.clear()
        crosswordDownByCell.clear()
        crosswordCellViews.clear()
        crosswordCellFrames.clear()
        crosswordActiveWordIndex = 0
        crosswordActiveCell = null
        crosswordChecked = false
        crosswordSolved = false
        crosswordProgrammaticChange = false
        jottoGuesses.clear()
        jottoFeedback = ""
        jottoInputText = ""
        jottoStatusView = null
        jottoFinished = false
        jottoWon = false
        playStartSound()

        when (level.quizType) {
            "kahoot" -> {
                questions = level.kahoot
                screen = Screen.QUIZ
                renderQuiz()
            }
            "myth_fact" -> {
                questions = level.mythFact
                screen = Screen.QUIZ
                renderQuiz()
            }
            "jigsaw" -> {
                jigsawTiles = loadJigsawTiles()
                jigsawOrder = jigsawTiles.indices.shuffled().toMutableList()
                jigsawPlacements.clear()
                selectedJigsawPiece = null
                jigsawStatus = ""
                jigsawCompleted = false
                screen = Screen.JIGSAW
                renderJigsaw()
            }
            "hangman" -> {
                hangmanIndex = 0
                hangmanWrong = 0
                hangmanGuessed.clear()
                hangmanRoundFinished = false
                screen = Screen.HANGMAN
                renderHangman()
            }
            "crossword" -> {
                prepareCrossword(level)
                screen = Screen.CROSSWORD
                renderCrossword()
            }
            "jotto" -> {
                jottoSecret = level.jotto.randomOrNull() ?: WordClue("CYCLE", "Monthly pattern")
                screen = Screen.JOTTO
                renderJotto()
            }
            else -> {
                questions = when (chosenDifficulty) {
                    "Intermediate" -> level.intermediate
                    "Difficult" -> level.difficult
                    else -> level.beginner
                }
                screen = Screen.QUIZ
                renderQuiz()
            }
        }
    }

    private fun loadJigsawTiles(): List<Bitmap> {
        val image = assets.open("birthpill.webp").use { BitmapFactory.decodeStream(it) }
            ?: error("Unable to decode the bundled jigsaw image.")
        val tileWidth = image.width / JIGSAW_COLUMNS
        val tileHeight = image.height / JIGSAW_ROWS
        return buildList(JIGSAW_PIECES) {
            for (row in 0 until JIGSAW_ROWS) {
                for (column in 0 until JIGSAW_COLUMNS) {
                    add(Bitmap.createBitmap(
                        image,
                        column * tileWidth,
                        row * tileHeight,
                        tileWidth,
                        tileHeight
                    ))
                }
            }
        }
    }

    private fun renderJigsaw() {
        val level = currentLevel ?: return renderLevels()
        screen = Screen.JIGSAW
        val body = beginPage("🧩 Jigsaw")
        text(body, level.title, 20f, colors.ink, true)
        text(body, "Place each picture piece into its matching slot.", 14f, colors.muted)
        text(body, "🎯  Puzzle board", 14f, colors.accent, true)

        val board = GridLayout(this).apply {
            columnCount = JIGSAW_COLUMNS
            useDefaultMargins = false
            setPadding(dp(4), dp(4), dp(4), dp(4))
            background = roundedDrawable(colors.peach, 10, colors.accent)
        }
        jigsawTiles.indices.forEach { slotIndex ->
            val slot = FrameLayout(this).apply {
                background = roundedDrawable(colors.peach, 4, colors.border)
                setOnClickListener { onJigsawSlotTap(slotIndex) }
            }
            val placedPiece = jigsawPlacements[slotIndex]
            if (placedPiece == null) {
                val number = TextView(this).apply {
                    text = (slotIndex + 1).toString()
                    textSize = 14f
                    gravity = Gravity.CENTER
                    setTextColor(colors.muted)
                }
                slot.addView(number, FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                ))
            } else {
                val tile = ImageView(this).apply {
                    setImageBitmap(jigsawTiles[placedPiece])
                    scaleType = ImageView.ScaleType.FIT_XY
                    setPadding(dp(2), dp(2), dp(2), dp(2))
                    background = roundedDrawable(
                        Color.WHITE,
                        4,
                        if (placedPiece == slotIndex) colors.successInk else colors.wrong
                    )
                }
                slot.addView(tile, FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                ))
            }
            board.addView(slot, GridLayout.LayoutParams().apply {
                width = 0
                height = dp(67)
                columnSpec = GridLayout.spec(slotIndex % JIGSAW_COLUMNS, 1f)
                rowSpec = GridLayout.spec(slotIndex / JIGSAW_COLUMNS)
                setMargins(dp(2), dp(2), dp(2), dp(2))
            })
        }
        body.addView(board, matchWidth())

        val selected = selectedJigsawPiece
        text(
            body,
            jigsawStatus.ifEmpty {
                "Step 1: select a piece below  →  Step 2: tap its slot above"
            },
            13f,
            if (selected == null) colors.muted else colors.accent,
            selected != null
        )
        val correctCount = jigsawPlacements.count { (slot, piece) -> slot == piece }
        text(body, "$correctCount / ${jigsawTiles.size} placed correctly",
            14f, if (jigsawCompleted) colors.successInk else colors.accent, true)
        text(body, "📦  Pieces (shuffled)", 14f, colors.muted, true)

        val tray = GridLayout(this).apply {
            columnCount = JIGSAW_COLUMNS
            useDefaultMargins = false
        }
        jigsawOrder.forEachIndexed { trayIndex, pieceIndex ->
            val placedSlot = jigsawPlacements.entries
                .firstOrNull { it.value == pieceIndex }?.key
            val trayCell = FrameLayout(this)
            if (placedSlot == null) {
                val tile = ImageView(this).apply {
                    setImageBitmap(jigsawTiles[pieceIndex])
                    scaleType = ImageView.ScaleType.FIT_XY
                    setPadding(dp(2), dp(2), dp(2), dp(2))
                    background = roundedDrawable(
                        Color.WHITE,
                        4,
                        if (selected == pieceIndex) colors.accent else colors.border
                    )
                    setOnClickListener { selectJigsawPiece(pieceIndex) }
                }
                trayCell.addView(tile, FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                ))
            } else {
                val correctlyPlaced = placedSlot == pieceIndex
                trayCell.background = roundedDrawable(colors.locked, 4, colors.border)
                val marker = TextView(this).apply {
                    text = if (correctlyPlaced) "✓" else "✗"
                    textSize = 24f
                    gravity = Gravity.CENTER
                    setTextColor(if (correctlyPlaced) colors.successInk else colors.wrong)
                }
                trayCell.addView(marker, FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                ))
            }
            tray.addView(trayCell, GridLayout.LayoutParams().apply {
                width = 0
                height = dp(67)
                columnSpec = GridLayout.spec(trayIndex % JIGSAW_COLUMNS, 1f)
                rowSpec = GridLayout.spec(trayIndex / JIGSAW_COLUMNS)
                setMargins(dp(2), dp(2), dp(2), dp(2))
            })
        }
        body.addView(tray, matchWidth())

        if (jigsawCompleted) {
            card(body, colors.success) {
                text(this, "🎉  PUZZLE COMPLETE!", 20f, colors.successInk, true)
                text(this, "You assembled the Birth Control Pills jigsaw!",
                    14f, colors.ink)
            }
            actionButton(body, "SEE RESULTS  ✔", colors.accent) {
                finishLevel(1, 1)
            }
        }
    }

    private fun selectJigsawPiece(pieceIndex: Int) {
        if (jigsawCompleted || jigsawPlacements.values.contains(pieceIndex)) return
        selectedJigsawPiece = pieceIndex
        jigsawStatus = "Piece selected ✔  Now tap the slot where it belongs."
        playClickSound()
        renderJigsaw()
    }

    private fun placeJigsawPiece(slotIndex: Int) {
        if (jigsawCompleted) return
        val selected = selectedJigsawPiece
        if (selected == null) {
            jigsawStatus = "Select a piece below first."
            renderJigsaw()
            return
        }
        jigsawPlacements.remove(slotIndex)
        jigsawPlacements[slotIndex] = selected
        selectedJigsawPiece = null
        val isCorrect = selected == slotIndex
        playTone(isCorrect)
        jigsawStatus = if (isCorrect) "Correct placement!" else "Not quite. Move pieces until they all fit."
        val correctCount = jigsawPlacements.count { (slot, piece) -> slot == piece }
        if (correctCount == jigsawTiles.size) {
            jigsawCompleted = true
            review.add(
                AnswerReview(
                    "Jigsaw: ${currentLevel?.title ?: "Puzzle"}",
                    "Completed",
                    "Completed",
                    true,
                    "You assembled the Birth Control Pills jigsaw."
                )
            )
        }
        renderJigsaw()
    }

    private fun onJigsawSlotTap(slotIndex: Int) {
        if (jigsawCompleted) return
        if (selectedJigsawPiece == null) {
            val piece = jigsawPlacements.remove(slotIndex)
            if (piece == null) {
                jigsawStatus = "Select a piece below first."
            } else {
                selectedJigsawPiece = piece
                jigsawStatus = "Piece lifted from the board. Tap its matching slot."
                playClickSound()
            }
            renderJigsaw()
            return
        }
        placeJigsawPiece(slotIndex)
    }

    private fun renderQuiz() {
        val level = currentLevel ?: return
        if (questions.isEmpty()) return finishLevel(0, 1)
        screen = Screen.QUIZ
        val question = questions[questionIndex]
        val body = beginPage(level.title)
        val timerSeconds = timerFor(level)
        questionDurationMs = timerSeconds * 1000L
        questionRemainingMs = questionDurationMs
        val isKahoot = level.quizType == "kahoot"
        val isMythFact = level.quizType == "myth_fact"
        val darkPanel = isKahoot || isMythFact
        val panelColor = if (isMythFact) colors.mythPanel else colors.kahootPanel
        val foreground = if (darkPanel) Color.WHITE else colors.ink

        card(body, if (darkPanel) panelColor else colors.card) {
            val hud = LinearLayout(this@MainActivity).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            val counter = TextView(this@MainActivity).apply {
                text = if (isMythFact) "🧠  ${questionIndex + 1} / ${questions.size}"
                else "Q ${questionIndex + 1} / ${questions.size}"
                textSize = 14f
                setTextColor(foreground)
                setTypeface(typeface, Typeface.BOLD)
            }
            hud.addView(counter, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
            val heartCount = TextView(this@MainActivity).apply {
                text = "❤".repeat(lives.coerceAtLeast(0)) + "🖤".repeat((3 - lives).coerceAtLeast(0))
                textSize = 15f
                setTextColor(colors.wrong)
            }
            hud.addView(heartCount)
            if (questionFeedback == null) {
                timerLabel = TextView(this@MainActivity).apply {
                    text = "⏱ $timerSeconds"
                    textSize = 15f
                    setTextColor(if (darkPanel) colors.easy else colors.muted)
                    setTypeface(typeface, Typeface.BOLD)
                    setPadding(dp(8), 0, 0, 0)
                }
                hud.addView(timerLabel)
            }
            addView(hud)
            if (isMythFact) {
                text(this, "📋  Is this a MYTH or a FACT?",
                    13f, colors.accent2, true)
            }
            text(this, question.question, 20f, foreground, true)
        }
        addProgressTrack(body, (questionIndex + 1f) / questions.size, if (isMythFact) colors.myth else colors.kahootRed)

        val feedback = questionFeedback
        if (feedback == null) {
            when {
                isKahoot -> addQuizTiles(body, question, feedback, isMythFact = false)
                isMythFact -> addQuizTiles(body, question, feedback, isMythFact = true)
                else -> question.options.forEach { option ->
                    actionButton(body, option, colors.card) { answerQuestion(option) }
                }
            }
            startQuestionTimer(timerSeconds)
        } else {
            if (isKahoot || isMythFact) {
                addQuizTiles(body, question, feedback, isMythFact)
            }
            card(body, if (feedback.isCorrect) colors.success else colors.peach) {
                text(this, if (feedback.isCorrect) "✅ Correct!" else "❌ Not quite",
                    18f, if (feedback.isCorrect) colors.successInk else colors.accent, true)
                text(this, feedback.explanation, 15f, colors.ink)
                if (!feedback.isCorrect) {
                    text(this, "❤ $lives / 3 lives remaining", 14f, colors.wrong, true)
                }
            }
            actionButton(
                body,
                if (questionIndex + 1 == questions.size) "See Results" else "Next Question",
                colors.accent
            ) {
                questionFeedback = null
                questionIndex++
                if (questionIndex >= questions.size) finishLevel(levelScore, questions.size)
                else renderQuiz()
            }
        }
    }

    private fun addQuizTiles(
        parent: LinearLayout,
        question: GameQuestion,
        feedback: AnswerReview?,
        isMythFact: Boolean
    ) {
        val grid = GridLayout(this).apply {
            columnCount = 2
            useDefaultMargins = true
        }
        val tileColors = if (isMythFact) {
            listOf(colors.kahootRed, colors.kahootGreen)
        } else {
            listOf(colors.kahootRed, colors.kahootBlue, colors.kahootYellow, colors.kahootGreen)
        }
        val icons = listOf("▲", "■", "●", "◆")
        question.options.forEachIndexed { index, option ->
            val color = when {
                feedback == null -> tileColors[index % tileColors.size]
                option == feedback.correct -> colors.kahootGreen
                option == feedback.chosen -> colors.kahootRed
                else -> colors.kahootMuted
            }
            val tileText = if (isMythFact) {
                if (option.equals("MYTH", ignoreCase = true)) "❌\nMYTH" else "✅\nFACT"
            } else {
                "${icons[index % icons.size]}\n$option"
            }
            val button = Button(this).apply {
                text = tileText
                textSize = if (isMythFact) 19f else 15f
                isAllCaps = false
                isEnabled = feedback == null
                setTextColor(if (color == colors.kahootYellow) colors.ink else Color.WHITE)
                backgroundTintList = null
                background = roundedDrawable(color, 14)
                minWidth = 0
                minimumWidth = 0
                minHeight = dp(if (isMythFact) 132 else 104)
                setPadding(dp(8), dp(8), dp(8), dp(8))
                setOnClickListener {
                    playClickSound()
                    answerQuestion(option)
                }
            }
            val params = GridLayout.LayoutParams().apply {
                width = 0
                height = dp(if (isMythFact) 132 else 104)
                columnSpec = GridLayout.spec(index % 2, 1f)
                rowSpec = GridLayout.spec(index / 2)
                setMargins(dp(4), dp(4), dp(4), dp(4))
            }
            grid.addView(button, params)
        }
        parent.addView(grid, matchWidth())
    }

    private fun startQuestionTimer(seconds: Int) {
        questionTimer?.cancel()
        lastTickSecond = seconds + 1
        questionTimer = object : CountDownTimer(seconds * 1000L, 250L) {
            override fun onTick(millisUntilFinished: Long) {
                questionRemainingMs = millisUntilFinished
                val seconds = ((millisUntilFinished + 999) / 1000).toInt()
                timerLabel?.text = "⏱ $seconds s"
                if (seconds in 1..5 && seconds < lastTickSecond) {
                    lastTickSecond = seconds
                    playTickSound()
                }
            }

            override fun onFinish() {
                questionRemainingMs = 0
                answerQuestion(null, timedOut = true)
            }
        }.start()
    }

    private fun answerQuestion(answer: String?, timedOut: Boolean = false) {
        if (questionFeedback != null) return
        questionTimer?.cancel()
        val question = questions.getOrNull(questionIndex) ?: return
        val isCorrect = !timedOut && answer == question.answer
        if (isCorrect) {
            levelScore++
            if (questionRemainingMs > questionDurationMs / 2) fastAnswers++
        } else {
            lives--
        }
        playTone(isCorrect)
        val reviewItem = AnswerReview(
            question.question,
            answer ?: "Time ran out",
            question.answer,
            isCorrect,
            question.explanation
        )
        review.add(reviewItem)
        questionFeedback = reviewItem
        if (lives <= 0) renderGameOver() else renderQuiz()
    }

    private fun renderHangman() {
        val level = currentLevel ?: return
        val item = level.hangman.getOrNull(hangmanIndex) ?: return finishLevel(levelScore, level.hangman.size)
        screen = Screen.HANGMAN
        val body = beginPage(level.title)
        card(body) {
            text(this, "WORD ${hangmanIndex + 1} / ${level.hangman.size}", 13f, colors.accent, true)
            text(this, "💡 ${item.hint}", 15f, colors.ink)
            text(this, item.word.map { if (it in hangmanGuessed) "$it " else "_ " }.joinToString(""),
                29f, colors.ink, true)
            text(this, "Wrong guesses: $hangmanWrong / 6", 14f, colors.wrong, true)
        }
        card(body, colors.peach) {
            text(this, "🎯  HANGMAN", 13f, colors.accent, true)
            addView(hangmanDrawing(), LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(180)
            ))
        }
        if (!hangmanRoundFinished) {
            val keyboard = GridLayout(this).apply {
                columnCount = 7
                useDefaultMargins = true
            }
            ('A'..'Z').forEachIndexed { index, letter ->
                val key = Button(this).apply {
                    text = letter.toString()
                    isAllCaps = false
                    isEnabled = letter !in hangmanGuessed
                    setTextColor(Color.WHITE)
                    backgroundTintList = ColorStateList.valueOf(
                        if (letter in hangmanGuessed) colors.muted else colors.accent
                    )
                    setOnClickListener {
                        playClickSound()
                        guessHangman(letter)
                    }
                    minWidth = 0
                    minimumWidth = 0
                    minHeight = dp(44)
                }
                val params = GridLayout.LayoutParams().apply {
                    width = 0
                    height = dp(48)
                    columnSpec = GridLayout.spec(index % 7, 1f)
                    rowSpec = GridLayout.spec(index / 7)
                    setMargins(dp(2), dp(2), dp(2), dp(2))
                }
                keyboard.addView(key, params)
            }
            body.addView(keyboard)
        } else {
            val solved = hangmanWrong < 6
            card(body, if (solved) colors.success else colors.peach) {
                text(this, if (solved) "Word solved!" else "The word was ${item.word}",
                    18f, if (solved) colors.successInk else colors.accent, true)
            }
            actionButton(body,
                if (hangmanIndex + 1 == level.hangman.size) "See Results" else "Next Word",
                colors.accent) {
                hangmanIndex++
                if (hangmanIndex >= level.hangman.size) {
                    finishLevel(levelScore, level.hangman.size)
                } else {
                    hangmanWrong = 0
                    hangmanGuessed.clear()
                    hangmanRoundFinished = false
                    renderHangman()
                }
            }
        }
    }

    private fun hangmanDrawing(): View = object : View(this) {
        private val structurePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = colors.accent
            strokeWidth = 5f
            strokeCap = Paint.Cap.ROUND
            style = Paint.Style.STROKE
        }
        private val figurePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = colors.ink
            strokeWidth = 4f
            strokeCap = Paint.Cap.ROUND
            style = Paint.Style.STROKE
        }
        private val ropePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = colors.muted
            strokeWidth = 3f
            strokeCap = Paint.Cap.ROUND
            style = Paint.Style.STROKE
        }
        private val markerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
        }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val scale = minOf(width / 320f, height / 200f)
            val offsetX = (width - 320f * scale) / 2f
            val offsetY = (height - 200f * scale) / 2f
            canvas.save()
            canvas.translate(offsetX, offsetY)
            canvas.scale(scale, scale)

            canvas.drawLine(70f, 160f, 245f, 160f, structurePaint)
            canvas.drawLine(105f, 160f, 105f, 20f, structurePaint)
            canvas.drawLine(105f, 20f, 205f, 20f, structurePaint)
            canvas.drawLine(205f, 20f, 205f, 45f, ropePaint)

            if (hangmanWrong >= 1) canvas.drawCircle(205f, 63f, 17f, figurePaint)
            if (hangmanWrong >= 2) canvas.drawLine(205f, 80f, 205f, 128f, figurePaint)
            if (hangmanWrong >= 3) canvas.drawLine(205f, 92f, 180f, 112f, figurePaint)
            if (hangmanWrong >= 4) canvas.drawLine(205f, 92f, 230f, 112f, figurePaint)
            if (hangmanWrong >= 5) canvas.drawLine(205f, 128f, 180f, 157f, figurePaint)
            if (hangmanWrong >= 6) canvas.drawLine(205f, 128f, 230f, 157f, figurePaint)

            repeat(6) { index ->
                markerPaint.color = if (index < hangmanWrong) colors.wrong else colors.border
                canvas.drawCircle(120f + index * 16f, 184f, 5f, markerPaint)
            }
            canvas.restore()
        }
    }

    private fun guessHangman(letter: Char) {
        if (hangmanRoundFinished) return
        val level = currentLevel ?: return
        val word = level.hangman[hangmanIndex].word
        hangmanGuessed.add(letter)
        if (letter in word) {
            playTone(true)
            if (word.all { it in hangmanGuessed }) {
                levelScore++
                review.add(AnswerReview("Hangman · ${level.hangman[hangmanIndex].hint}",
                    word, word, true, level.hangman[hangmanIndex].hint))
                hangmanRoundFinished = true
            }
        } else {
            playTone(false)
            hangmanWrong++
            if (hangmanWrong >= 6) {
                lives--
                review.add(AnswerReview("Hangman · ${level.hangman[hangmanIndex].hint}",
                    "Unsolved", word, false, level.hangman[hangmanIndex].hint))
                hangmanRoundFinished = true
            }
        }
        if (lives <= 0) renderGameOver() else renderHangman()
    }

    private fun prepareCrossword(level: GameLevel) {
        val hints = level.crossword.associate { it.word.uppercase() to it.hint }
        val starts = CROSSWORD_PLACEMENTS
            .map { CrosswordPosition(it.row, it.column) }
            .distinct()
            .sortedWith(compareBy<CrosswordPosition> { it.row }.thenBy { it.column })
        val numbers = starts.mapIndexed { index, position -> position to index + 1 }.toMap()

        crosswordWords = CROSSWORD_PLACEMENTS.mapIndexed { wordIndex, placement ->
            val word = placement.word
            val cells = word.indices.map { offset ->
                if (placement.direction == CrosswordDirection.ACROSS) {
                    CrosswordPosition(placement.row, placement.column + offset)
                } else {
                    CrosswordPosition(placement.row + offset, placement.column)
                }
            }
            cells.forEachIndexed { letterIndex, position ->
                val letter = word[letterIndex]
                val existing = crosswordSolution[position]
                check(existing == null || existing == letter) {
                    "Conflicting crossword letters at ${position.row},${position.column}."
                }
                crosswordSolution[position] = letter
                val wordAtCell = if (placement.direction == CrosswordDirection.ACROSS) {
                    crosswordAcrossByCell
                } else {
                    crosswordDownByCell
                }
                check(wordAtCell.put(position, wordIndex) == null) {
                    "Overlapping words share the same crossword direction."
                }
            }
            CrosswordWord(
                word = word,
                direction = placement.direction,
                number = numbers.getValue(CrosswordPosition(placement.row, placement.column)),
                hint = checkNotNull(hints[word]) { "Missing crossword clue for $word." },
                cells = cells
            )
        }
        crosswordActiveWordIndex = 0
        crosswordActiveCell = crosswordWords.firstOrNull()?.cells?.firstOrNull()
    }

    private fun renderCrossword() {
        val level = currentLevel ?: return
        if (crosswordWords.isEmpty()) prepareCrossword(level)
        if (crosswordWords.isEmpty()) return

        screen = Screen.CROSSWORD
        val body = beginPage(level.title)
        card(body) {
            text(this, "📝  CROSSWORD  ·  ${crosswordWords.size} WORDS",
                13f, colors.accent, true)
            val activeWord = crosswordWords[crosswordActiveWordIndex]
            crosswordActiveTitleView = text(
                this,
                "${activeWord.number} ${activeWord.direction.label}  ·  " +
                    "${activeWord.word.length} letters",
                13f,
                colors.muted,
                true
            )
            crosswordActiveClueView = text(this, activeWord.hint, 17f, colors.ink, true)
            text(this, "Tap a cell and type. Use Switch Direction at crossings.",
                12f, colors.muted)
            crosswordDirectionButton = Button(this@MainActivity).apply {
                text = "Switch Direction"
                isAllCaps = false
                textSize = 13f
                setTextColor(colors.ink)
                backgroundTintList = ColorStateList.valueOf(colors.locked)
                setOnClickListener {
                    playClickSound()
                    switchCrosswordDirection()
                }
            }
            addView(crosswordDirectionButton, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(42)
            ))
            refreshActiveCrosswordClue()
        }

        val availableCellWidth = (resources.displayMetrics.widthPixels - dp(94)) / CROSSWORD_COLUMNS
        val cellSize = minOf(dp(36), availableCellWidth).coerceAtLeast(dp(20))
        val board = GridLayout(this).apply {
            rowCount = CROSSWORD_ROWS
            columnCount = CROSSWORD_COLUMNS
            useDefaultMargins = false
            alignmentMode = GridLayout.ALIGN_BOUNDS
        }
        val numberedCells = crosswordWords.associate {
            CrosswordPosition(it.cells.first().row, it.cells.first().column) to it.number
        }
        for (row in 0 until CROSSWORD_ROWS) {
            for (column in 0 until CROSSWORD_COLUMNS) {
                val position = CrosswordPosition(row, column)
                val frame = FrameLayout(this)
                val solutionLetter = crosswordSolution[position]
                if (solutionLetter == null) {
                    frame.setBackgroundColor(colors.locked)
                } else {
                    val cell = EditText(this).apply {
                        inputType = android.text.InputType.TYPE_CLASS_TEXT or
                            android.text.InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
                        imeOptions = EditorInfo.IME_ACTION_NONE
                        filters = arrayOf(InputFilter.LengthFilter(1))
                        textSize = 14f
                        gravity = Gravity.CENTER
                        setSingleLine(true)
                        includeFontPadding = false
                        setPadding(0, 0, 0, 0)
                        setTextColor(colors.ink)
                        background = null
                        setText(crosswordLetters[position]?.toString().orEmpty())
                    }
                    cell.onFocusChangeListener = View.OnFocusChangeListener { _, hasFocus ->
                        if (hasFocus) activateCrosswordCell(position)
                    }
                    cell.addTextChangedListener(object : android.text.TextWatcher {
                        override fun beforeTextChanged(
                            text: CharSequence?, start: Int, count: Int, after: Int
                        ) = Unit

                        override fun onTextChanged(
                            text: CharSequence?, start: Int, before: Int, count: Int
                        ) = Unit

                        override fun afterTextChanged(text: android.text.Editable?) {
                            onCrosswordTextChanged(position, cell, text?.toString().orEmpty())
                        }
                    })
                    frame.addView(cell, FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                    ))
                    numberedCells[position]?.let { number ->
                        val numberLabel = TextView(this).apply {
                            text = number.toString()
                            textSize = 7f
                            setTextColor(colors.accent)
                            setPadding(dp(2), 0, 0, 0)
                            gravity = Gravity.TOP or Gravity.START
                            isClickable = false
                            isFocusable = false
                        }
                        frame.addView(numberLabel, FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        ))
                    }
                    crosswordCellViews[position] = cell
                    crosswordCellFrames[position] = frame
                }
                board.addView(frame, GridLayout.LayoutParams().apply {
                    width = cellSize
                    height = cellSize
                    rowSpec = GridLayout.spec(row)
                    columnSpec = GridLayout.spec(column)
                    setMargins(dp(1), dp(1), dp(1), dp(1))
                })
            }
        }
        card(body, colors.peach) {
            addView(board, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply { gravity = Gravity.CENTER })
        }
        updateCrosswordCellStyles()

        crosswordStatusView = text(
            body,
            crosswordFeedback.ifEmpty { "Fill in the grid, then check your answers." },
            14f,
            if (crosswordSolved) colors.successInk else colors.muted,
            crosswordSolved
        )
        if (crosswordSolved) {
            card(body, colors.success) {
                text(this, "🎉  CROSSWORD COMPLETE!", 19f, colors.successInk, true)
                text(this, "All answers fit the puzzle.", 14f, colors.ink)
            }
            actionButton(body, "SEE RESULTS  ✔", colors.accent) {
                finishLevel(1, 1)
            }
        } else {
            val actions = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER
            }
            val checkButton = crosswordButton("Check Answers", colors.accent) {
                checkCrosswordAnswers()
            }
            val revealButton = crosswordButton("Reveal All", colors.locked) {
                revealCrosswordAnswers()
            }.apply { setTextColor(colors.ink) }
            actions.addView(checkButton, LinearLayout.LayoutParams(0, dp(52), 1f).apply {
                rightMargin = dp(4)
            })
            actions.addView(revealButton, LinearLayout.LayoutParams(0, dp(52), 1f).apply {
                leftMargin = dp(4)
            })
            body.addView(actions, matchWidth())
            addCrosswordClueSection(body, CrosswordDirection.ACROSS)
            addCrosswordClueSection(body, CrosswordDirection.DOWN)
        }
    }

    private fun crosswordButton(label: String, backgroundColor: Int, action: () -> Unit) =
        Button(this).apply {
            text = label
            isAllCaps = false
            textSize = 14f
            setTextColor(Color.WHITE)
            backgroundTintList = ColorStateList.valueOf(backgroundColor)
            setOnClickListener {
                playClickSound()
                action()
            }
        }

    private fun addCrosswordClueSection(parent: LinearLayout, direction: CrosswordDirection) {
        val entries = crosswordWords.withIndex().filter { it.value.direction == direction }
        card(parent) {
            text(this, direction.label.uppercase(), 14f, colors.accent, true)
            entries.forEach { (index, word) ->
                val clue = TextView(this@MainActivity).apply {
                    text = "${word.number}.  ${word.hint} (${word.word.length})"
                    textSize = 14f
                    setTextColor(colors.ink)
                    setPadding(dp(10), dp(8), dp(10), dp(8))
                    background = roundedDrawable(colors.background, 8, colors.border)
                    setOnClickListener {
                        selectCrosswordWord(index)
                    }
                }
                addView(clue, LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                ).apply { bottomMargin = dp(4) })
            }
        }
    }

    private fun activateCrosswordCell(position: CrosswordPosition) {
        val across = crosswordAcrossByCell[position]
        val down = crosswordDownByCell[position]
        if (crosswordActiveWordIndex != across && crosswordActiveWordIndex != down) {
            crosswordActiveWordIndex = across ?: down ?: return
        }
        crosswordActiveCell = position
        refreshActiveCrosswordClue()
        updateCrosswordCellStyles()
    }

    private fun switchCrosswordDirection() {
        val position = crosswordActiveCell ?: return
        val across = crosswordAcrossByCell[position]
        val down = crosswordDownByCell[position]
        if (across == null || down == null) return
        crosswordActiveWordIndex = if (crosswordActiveWordIndex == across) down else across
        refreshActiveCrosswordClue()
        updateCrosswordCellStyles()
    }

    private fun selectCrosswordWord(index: Int) {
        val word = crosswordWords.getOrNull(index) ?: return
        crosswordActiveWordIndex = index
        crosswordActiveCell = word.cells.first()
        refreshActiveCrosswordClue()
        updateCrosswordCellStyles()
        crosswordActiveCell?.let { crosswordCellViews[it]?.requestFocus() }
    }

    private fun refreshActiveCrosswordClue() {
        val word = crosswordWords.getOrNull(crosswordActiveWordIndex) ?: return
        crosswordActiveTitleView?.text = "${word.number} ${word.direction.label}  ·  " +
            "${word.word.length} letters"
        crosswordActiveClueView?.text = word.hint
        val position = crosswordActiveCell
        crosswordDirectionButton?.isEnabled = position != null &&
            crosswordAcrossByCell.containsKey(position) &&
            crosswordDownByCell.containsKey(position)
    }

    private fun onCrosswordTextChanged(
        position: CrosswordPosition,
        cell: EditText,
        text: String
    ) {
        if (crosswordProgrammaticChange) return
        val letter = text.filter { it.isLetter() }.take(1).uppercase()
        if (letter != text) {
            crosswordProgrammaticChange = true
            cell.setText(letter)
            cell.setSelection(letter.length)
            crosswordProgrammaticChange = false
        }
        if (letter.isEmpty()) {
            crosswordLetters.remove(position)
        } else {
            crosswordLetters[position] = letter.first()
        }
        crosswordChecked = false
        crosswordFeedback = ""
        crosswordStatusView?.apply {
            this.text = "Fill in the grid, then check your answers."
            setTextColor(colors.muted)
        }
        updateCrosswordCellStyles()
        if (letter.isNotEmpty()) moveToNextCrosswordCell(position)
    }

    private fun moveToNextCrosswordCell(position: CrosswordPosition) {
        val word = crosswordWords.getOrNull(crosswordActiveWordIndex) ?: return
        val index = word.cells.indexOf(position)
        val next = word.cells.getOrNull(index + 1) ?: return
        crosswordActiveCell = next
        crosswordCellViews[next]?.requestFocus()
        refreshActiveCrosswordClue()
        updateCrosswordCellStyles()
    }

    private fun updateCrosswordCellStyles() {
        val activeCells = crosswordWords.getOrNull(crosswordActiveWordIndex)?.cells?.toSet().orEmpty()
        crosswordCellFrames.forEach { (position, frame) ->
            val letter = crosswordLetters[position]
            val isCorrect = letter == crosswordSolution[position]
            val selected = position == crosswordActiveCell
            val backgroundColor = when {
                crosswordChecked && isCorrect -> colors.success
                selected -> colors.banner
                position in activeCells -> colors.peach
                else -> Color.WHITE
            }
            val borderColor = when {
                crosswordChecked && isCorrect -> colors.successInk
                crosswordChecked && letter != null && !isCorrect -> colors.wrong
                selected -> colors.accent
                position in activeCells -> colors.accent2
                else -> colors.border
            }
            frame.background = roundedDrawable(backgroundColor, 3, borderColor)
            crosswordCellViews[position]?.apply {
                setTextColor(
                    if (crosswordChecked && letter != null && !isCorrect) colors.wrong
                    else colors.ink
                )
                isEnabled = !crosswordSolved
            }
        }
    }

    private fun checkCrosswordAnswers() {
        if (crosswordSolved) return
        crosswordChecked = true
        val correctCount = crosswordSolution.count { (position, answer) ->
            crosswordLetters[position] == answer
        }
        if (correctCount == crosswordSolution.size) {
            crosswordSolved = true
            crosswordFeedback = "Every letter is correct!"
            review.add(
                AnswerReview(
                    "Crossword: ${currentLevel?.title ?: "Puzzle"}",
                    "Completed",
                    "Completed",
                    true,
                    "You completed the crossword puzzle."
                )
            )
            playCompletionSound(true)
            renderCrossword()
        } else {
            crosswordFeedback = "$correctCount / ${crosswordSolution.size} letters correct. Keep going."
            playTone(false)
            crosswordStatusView?.apply {
                text = crosswordFeedback
                setTextColor(colors.wrong)
            }
            updateCrosswordCellStyles()
        }
    }

    private fun revealCrosswordAnswers() {
        if (crosswordSolved) return
        crosswordProgrammaticChange = true
        crosswordSolution.forEach { (position, letter) ->
            crosswordLetters[position] = letter
            crosswordCellViews[position]?.setText(letter.toString())
        }
        crosswordProgrammaticChange = false
        crosswordChecked = true
        crosswordFeedback = "All answers revealed. Tap Check Answers to complete."
        crosswordStatusView?.text = crosswordFeedback
        updateCrosswordCellStyles()
    }

    private fun renderJotto() {
        val level = currentLevel ?: return
        screen = Screen.JOTTO
        val body = beginPage(level.title)
        card(body) {
            text(this, "🔤  JOTTO", 14f, colors.accent, true)
            text(this, "Guess the ${jottoSecret.word.length}-letter word  ·  " +
                "${JOTTO_MAX_GUESSES - jottoGuesses.size} guesses left",
                18f, colors.ink, true)
            text(this, "The score is how many letters your guess shares with the secret, " +
                "regardless of position.", 14f, colors.muted)
            text(this, "Hint: ${jottoSecret.hint}", 15f, colors.accent, true)
        }

        text(body, "GUESS BOARD", 14f, colors.accent, true)
        repeat(JOTTO_MAX_GUESSES) { rowIndex ->
            val guess = jottoGuesses.getOrNull(rowIndex)
            val matchedLetters = guess?.first?.let { jottoMatchedPositions(it) }.orEmpty()
            val row = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = Gravity.CENTER_VERTICAL
            }
            repeat(jottoSecret.word.length) { letterIndex ->
                val letter = guess?.first?.getOrNull(letterIndex)
                val isMatch = letterIndex in matchedLetters
                val cellColor = when {
                    letter == null -> colors.card
                    isMatch -> colors.peach
                    else -> colors.locked
                }
                val borderColor = when {
                    letter == null -> colors.border
                    isMatch -> colors.medium
                    else -> colors.muted
                }
                val tile = TextView(this).apply {
                    text = letter?.toString() ?: ""
                    textSize = 16f
                    gravity = Gravity.CENTER
                    setTextColor(
                        if (letter == null || isMatch) colors.ink else colors.muted
                    )
                    background = roundedDrawable(cellColor, 7, borderColor)
                }
                row.addView(tile, LinearLayout.LayoutParams(dp(36), dp(36)).apply {
                    setMargins(dp(1), dp(1), dp(1), dp(1))
                })
            }
            val score = TextView(this).apply {
                text = guess?.second?.toString() ?: "·"
                textSize = 18f
                gravity = Gravity.CENTER
                setTextColor(
                    when (guess?.second) {
                        null -> colors.muted
                        jottoSecret.word.length -> colors.successInk
                        0 -> colors.wrong
                        else -> colors.gold
                    }
                )
                background = roundedDrawable(colors.background, 8, colors.border)
            }
            row.addView(score, LinearLayout.LayoutParams(dp(36), dp(36)).apply {
                leftMargin = dp(6)
                topMargin = dp(1)
                bottomMargin = dp(1)
            })
            body.addView(row, matchWidth())
        }

        card(body) {
            text(this, "LETTERS USED", 13f, colors.muted, true)
            val usedLetters = jottoGuesses.flatMap { it.first.toList() }.toSet()
            val alphabet = GridLayout(this@MainActivity).apply {
                columnCount = 13
                useDefaultMargins = false
            }
            ('A'..'Z').forEachIndexed { index, letter ->
                val used = letter in usedLetters
                val marker = TextView(this@MainActivity).apply {
                    text = letter.toString()
                    textSize = 11f
                    gravity = Gravity.CENTER
                    setTextColor(if (used) colors.gold else colors.muted)
                    background = if (used) roundedDrawable(colors.peach, 5) else null
                }
                alphabet.addView(marker, GridLayout.LayoutParams().apply {
                    width = 0
                    height = dp(28)
                    columnSpec = GridLayout.spec(index % 13, 1f)
                    rowSpec = GridLayout.spec(index / 13)
                    setMargins(dp(1), dp(1), dp(1), dp(1))
                })
            }
            addView(alphabet, LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ))
        }

        if (jottoFinished) {
            card(body, if (jottoWon) colors.success else colors.peach) {
                text(this, if (jottoWon) "🎉  WORD FOUND!" else "OUT OF GUESSES",
                    19f, if (jottoWon) colors.successInk else colors.wrong, true)
                text(this, "The word was ${jottoSecret.word}.", 16f, colors.ink, true)
                if (jottoWon) {
                    text(this, "Solved in ${jottoGuesses.size} " +
                        if (jottoGuesses.size == 1) "guess." else "guesses.",
                        14f, colors.muted)
                } else {
                    text(this, "$lives lives remaining.", 14f, colors.muted)
                }
            }
            actionButton(body, "SEE RESULTS  ✔", colors.accent) {
                if (!jottoWon && lives <= 0) {
                    renderGameOver()
                } else {
                    finishLevel(if (jottoWon) 1 else 0, 1)
                }
            }
        } else {
            text(body, "Enter a ${jottoSecret.word.length}-letter guess:", 14f, colors.ink, true)
            val input = EditText(this).apply {
                hint = "Type your guess"
                inputType = android.text.InputType.TYPE_CLASS_TEXT or
                    android.text.InputType.TYPE_TEXT_FLAG_CAP_CHARACTERS
                imeOptions = EditorInfo.IME_ACTION_DONE
                filters = arrayOf(InputFilter.LengthFilter(jottoSecret.word.length))
                textSize = 18f
                setSingleLine(true)
                setPadding(dp(12), dp(8), dp(12), dp(8))
                background = roundedDrawable(colors.card, 8, colors.border)
                setText(jottoInputText)
                addTextChangedListener(object : android.text.TextWatcher {
                    override fun beforeTextChanged(
                        text: CharSequence?, start: Int, count: Int, after: Int
                    ) = Unit

                    override fun onTextChanged(
                        text: CharSequence?, start: Int, before: Int, count: Int
                    ) = Unit

                    override fun afterTextChanged(text: android.text.Editable?) {
                        jottoInputText = text?.toString().orEmpty().uppercase()
                        if (jottoFeedback.isNotEmpty()) {
                            jottoFeedback = ""
                            jottoStatusView?.apply {
                                this.text = ""
                                setTextColor(colors.muted)
                            }
                        }
                    }
                })
            }
            body.addView(input, matchWidth())
            jottoStatusView = text(
                body,
                jottoFeedback.ifEmpty { "Guess letters in any position; the score is your clue." },
                14f,
                if (jottoFeedback.isEmpty()) colors.muted else colors.wrong,
                jottoFeedback.isNotEmpty()
            )
            input.setOnEditorActionListener { _, actionId, _ ->
                if (actionId == EditorInfo.IME_ACTION_DONE) {
                    submitJottoInput(input.text.toString())
                    true
                } else {
                    false
                }
            }
            actionButton(body, "GUESS  ▶", colors.accent) {
                submitJottoInput(input.text.toString())
            }
        }
    }

    private fun submitJottoInput(rawGuess: String) {
        val guess = rawGuess.trim().uppercase()
        if (guess.length != jottoSecret.word.length || !guess.all { it.isLetter() }) {
            jottoFeedback = "Enter exactly ${jottoSecret.word.length} letters."
            jottoStatusView?.apply {
                text = jottoFeedback
                setTextColor(colors.wrong)
            }
            return
        }
        if (jottoGuesses.any { it.first == guess }) {
            jottoFeedback = "You already tried that word. Make a different guess."
            jottoStatusView?.apply {
                text = jottoFeedback
                setTextColor(colors.wrong)
            }
            return
        }
        jottoFeedback = ""
        submitJottoGuess(guess)
    }

    private fun submitJottoGuess(guess: String) {
        if (jottoFinished) return
        val secret = jottoSecret.word
        val overlap = jottoMatchedPositions(guess).size
        jottoGuesses.add(guess to overlap)
        jottoInputText = ""
        if (guess == secret) {
            jottoFinished = true
            jottoWon = true
            levelScore = 1
            review.add(AnswerReview("Jotto · ${jottoSecret.hint}", guess, secret, true, jottoSecret.hint))
        } else if (jottoGuesses.size >= JOTTO_MAX_GUESSES) {
            jottoFinished = true
            jottoWon = false
            lives--
            review.add(AnswerReview("Jotto · ${jottoSecret.hint}", guess, secret, false, jottoSecret.hint))
        }
        playTone(overlap > 0)
        renderJotto()
    }

    private fun jottoMatchedPositions(guess: String): Set<Int> {
        val remaining = jottoSecret.word.groupingBy { it }.eachCount().toMutableMap()
        val matched = mutableSetOf<Int>()
        guess.forEachIndexed { index, letter ->
            val count = remaining[letter] ?: 0
            if (count > 0) {
                matched.add(index)
                remaining[letter] = count - 1
            }
        }
        return matched
    }

    private fun finishLevel(score: Int, total: Int) {
        questionTimer?.cancel()
        levelScore = score
        val level = currentLevel ?: return renderLevels()
        val safeTotal = max(1, total)
        val ratio = score.toDouble() / safeTotal
        val stars = when {
            ratio >= 1.0 -> 3
            ratio >= 0.6 -> 2
            else -> 1
        }
        playCompletionSound(stars == 3)
        progress.completed.add(level.id)
        val previous = progress.highScores[level.id]
        if (previous == null || score.toDouble() / safeTotal >=
            previous.score.toDouble() / max(1, previous.total)) {
            progress.highScores[level.id] = LevelScore(score, safeTotal, stars)
        }
        if (levels.any { it.id == level.id + 1 }) progress.unlocked.add(level.id + 1)
        awardBadges(level.id, ratio)
        progress.leaderboard.add(
            BoardEntry("Player", level.id, score, safeTotal, stars)
        )
        progress.leaderboard.sortWith(
            compareByDescending<BoardEntry> { it.score.toDouble() / max(1, it.total) }
                .thenByDescending { it.stars }
                .thenByDescending { it.score }
        )
        while (progress.leaderboard.size > 10) progress.leaderboard.removeLast()
        writeProgress()
        renderResult(score, safeTotal, stars)
    }

    private fun awardBadges(levelId: Int, ratio: Double) {
        val completed = progress.completed
        if (1 in completed) progress.badges.add("first_step")
        if (1 in completed && 2 in completed) progress.badges.add("beginner")
        if ((1..4).all { it in completed }) progress.badges.add("intermediate")
        if (5 in completed && 6 in completed) progress.badges.add("expert")
        if ((1..6).all { it in completed }) progress.badges.add("deciwise")
        if (ratio >= 1.0) progress.badges.add("perfect_run")
        if (fastAnswers >= 5) progress.badges.add("speedster")
    }

    private fun renderResult(score: Int, total: Int, stars: Int) {
        screen = Screen.RESULT
        val body = beginPage("Quest Complete")
        card(body, if (score == total) colors.success else colors.card) {
            text(this, if (score == total) "🏆 Perfect Score!" else "Well Done!",
                24f, colors.ink, true)
            text(this, "⭐".repeat(stars) + "☆".repeat(3 - stars),
                25f, colors.gold, true)
            text(this, "$score / $total correct", 22f, colors.ink, true)
            text(this, "New badges: ${progress.badges.size} / ${badgeInfo.size}",
                14f, colors.muted)
        }
        if (review.isNotEmpty()) {
            text(body, "ANSWER REVIEW", 14f, colors.accent, true)
            review.takeLast(10).forEach { item ->
                card(body, colors.card) {
                    text(this, item.question, 15f, colors.ink, true)
                    text(this, "${if (item.isCorrect) "✓" else "✗"}  ${item.chosen}",
                        14f, if (item.isCorrect) colors.successInk else colors.wrong)
                    if (!item.isCorrect) text(this, "Answer: ${item.correct}", 14f, colors.successInk)
                    if (item.explanation.isNotBlank()) text(this, item.explanation, 13f, colors.muted)
                }
            }
        }
        actionButton(body, "Retry Quest", colors.accent) { renderStory() }
        actionButton(body, "Level Select", colors.peach) { renderLevels() }
    }

    private fun renderGameOver() {
        questionTimer?.cancel()
        playGameOverSound()
        screen = Screen.GAME_OVER
        val body = beginPage("Quest Over")
        card(body, colors.peach) {
            text(this, "💔", 40f, colors.wrong, true)
            text(this, "Keep Learning!", 24f, colors.ink, true)
            text(this, "You can retry this level and try a different approach.",
                15f, colors.muted)
        }
        actionButton(body, "Retry Quest", colors.accent) {
            lives = 3
            levelScore = 0
            fastAnswers = 0
            review.clear()
            renderStory()
        }
        actionButton(body, "Level Select", colors.card) { renderLevels() }
    }

    private fun renderBadges() {
        screen = Screen.BADGES
        val body = beginPage("Badges & Achievements")
        text(body, "${progress.badges.size} / ${badgeInfo.size} unlocked",
            15f, colors.muted, true)
        badgeInfo.forEach { (key, info) ->
            val unlocked = key in progress.badges
            card(body, if (unlocked) colors.peach else colors.locked) {
                text(this, "${info.first}  ${info.second}", 18f,
                    if (unlocked) colors.gold else colors.lockedText, true)
                text(this, info.third, 14f, colors.muted)
                text(this, if (unlocked) "UNLOCKED" else "LOCKED",
                    12f, if (unlocked) colors.successInk else colors.muted, true)
            }
        }
    }

    private fun renderLeaderboard() {
        screen = Screen.LEADERBOARD
        val body = beginPage("Leaderboard")
        if (progress.leaderboard.isEmpty()) {
            card(body) { text(this, "Play a quest to add a score.", 16f, colors.muted) }
        } else {
            progress.leaderboard.forEachIndexed { index, entry ->
                card(body, if (index < 3) colors.peach else colors.card) {
                    text(this, "${index + 1}.  ${entry.name}", 18f, colors.ink, true)
                    text(this, "Level ${entry.level} · ${entry.score}/${entry.total} · " +
                        "${(100.0 * entry.score / max(1, entry.total)).roundToInt()}% · " +
                        "${"★".repeat(entry.stars)}",
                        14f, colors.muted)
                }
            }
        }
        actionButton(body, "Clear Scores", colors.card) {
            progress.leaderboard.clear()
            writeProgress()
            renderLeaderboard()
        }
    }

    private fun readProgress(context: Context): GameProgress {
        val saved = context.getSharedPreferences("deciwise", Context.MODE_PRIVATE)
            .getString("progress", null) ?: return GameProgress()
        return try {
            val data = JSONObject(saved)
            val result = GameProgress()
            result.unlocked.clear()
            result.unlocked.addAll(data.optJSONArray("unlocked").asIntSet())
            result.completed.addAll(data.optJSONArray("completed").asIntSet())
            val highScores = data.optJSONObject("high_scores") ?: JSONObject()
            val keys = highScores.keys()
            while (keys.hasNext()) {
                val id = keys.next().toIntOrNull() ?: continue
                val score = highScores.getJSONObject(id.toString())
                result.highScores[id] = LevelScore(
                    score.optInt("score"),
                    score.optInt("total", 1),
                    score.optInt("stars", 1)
                )
            }
            val badges = data.optJSONArray("badges")
            for (index in 0 until (badges?.length() ?: 0)) {
                result.badges.add(badges!!.optString(index))
            }
            val board = data.optJSONArray("leaderboard")
            for (index in 0 until (board?.length() ?: 0)) {
                val row = board!!.optJSONObject(index) ?: continue
                result.leaderboard.add(
                    BoardEntry(
                        row.optString("name", "Player"),
                        row.optInt("level"),
                        row.optInt("score"),
                        row.optInt("total", 1),
                        row.optInt("stars", 1)
                    )
                )
            }
            result
        } catch (_: Exception) {
            GameProgress()
        }
    }

    private fun writeProgress() {
        val highScores = JSONObject()
        progress.highScores.forEach { (id, score) ->
            highScores.put(id.toString(), JSONObject().apply {
                put("score", score.score)
                put("total", score.total)
                put("stars", score.stars)
            })
        }
        val data = JSONObject().apply {
            put("unlocked", JSONArray(progress.unlocked.sorted()))
            put("completed", JSONArray(progress.completed.sorted()))
            put("high_scores", highScores)
            put("badges", JSONArray(progress.badges.sorted()))
            put("leaderboard", JSONArray().apply {
                progress.leaderboard.forEach { entry ->
                    put(JSONObject().apply {
                        put("name", entry.name)
                        put("level", entry.level)
                        put("score", entry.score)
                        put("total", entry.total)
                        put("stars", entry.stars)
                    })
                }
            })
        }
        getSharedPreferences("deciwise", Context.MODE_PRIVATE)
            .edit()
            .putString("progress", data.toString())
            .apply()
    }

    private fun JSONArray?.asIntSet(): Set<Int> =
        (0 until (this?.length() ?: 0)).mapNotNull { this?.optInt(it) }.toSet()

    private fun startMusic() {
        if (musicTrack?.playState == AudioTrack.PLAYSTATE_PLAYING) return
        stopMusic()
        val sampleRate = 22_050
        val noteMs = 280
        val notes = intArrayOf(
            262, 330, 392, 330, 220, 262, 330, 262,
            175, 220, 262, 220, 196, 247, 294, 247
        )
        val samplesPerNote = sampleRate * noteMs / 1000
        val pcm = ShortArray(samplesPerNote * notes.size)
        notes.forEachIndexed { noteIndex, frequency ->
            for (sample in 0 until samplesPerNote) {
                val edge = minOf(sample, samplesPerNote - sample - 1)
                val envelope = (edge / (sampleRate * 0.012f)).coerceIn(0f, 1f)
                val phase = 2.0 * Math.PI * frequency * sample / sampleRate
                pcm[noteIndex * samplesPerNote + sample] =
                    (sin(phase) * envelope * 4_500).toInt().toShort()
            }
        }
        val track = AudioTrack.Builder()
            .setAudioAttributes(
                AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build()
            )
            .setAudioFormat(
                AudioFormat.Builder()
                    .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                    .setSampleRate(sampleRate)
                    .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                    .build()
            )
            .setBufferSizeInBytes(pcm.size * 2)
            .setTransferMode(AudioTrack.MODE_STATIC)
            .build()
        val written = track.write(pcm, 0, pcm.size, AudioTrack.WRITE_BLOCKING)
        if (written > 0) {
            track.setLoopPoints(0, pcm.size, -1)
            track.setVolume(0.24f)
            track.play()
            musicTrack = track
        } else {
            track.release()
        }
    }

    private fun stopMusic() {
        musicTrack?.let {
            it.pause()
            it.flush()
            it.release()
        }
        musicTrack = null
    }

    private fun playTone(correct: Boolean) {
        playSystemTone(
            if (correct) ToneGenerator.TONE_PROP_ACK else ToneGenerator.TONE_PROP_NACK,
            120,
            32
        )
    }

    private fun playClickSound() =
        playSystemTone(ToneGenerator.TONE_PROP_BEEP, 40, 18)

    private fun playBackSound() =
        playSystemTone(ToneGenerator.TONE_PROP_BEEP, 55, 20)

    private fun playTickSound() =
        playSystemTone(ToneGenerator.TONE_PROP_BEEP, 18, 8)

    private fun playStartSound() {
        soundHandler.postDelayed({
            playSystemTone(ToneGenerator.TONE_PROP_ACK, 80, 24)
        }, 120)
    }

    private fun playCompletionSound(perfect: Boolean) {
        if (!perfect) {
            playSystemTone(ToneGenerator.TONE_PROP_ACK, 150, 26)
            return
        }
        listOf(ToneGenerator.TONE_PROP_BEEP, ToneGenerator.TONE_PROP_ACK, ToneGenerator.TONE_PROP_ACK)
            .forEachIndexed { index, tone ->
                soundHandler.postDelayed({
                    playSystemTone(tone, 90, 28)
                }, index * 190L)
            }
    }

    private fun playGameOverSound() =
        playSystemTone(ToneGenerator.TONE_PROP_NACK, 240, 26)

    private fun playSystemTone(toneType: Int, durationMs: Int, volume: Int) {
        val tone = ToneGenerator(AudioManager.STREAM_MUSIC, volume)
        tone.startTone(toneType, durationMs)
        soundHandler.postDelayed({ tone.release() }, durationMs + 100L)
    }

    private fun card(
        parent: LinearLayout,
        background: Int = colors.card,
        content: LinearLayout.() -> Unit
    ): LinearLayout {
        val panel = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(14), dp(16), dp(14))
            this.background = GradientDrawable().apply {
                setColor(background)
                cornerRadius = dp(16).toFloat()
                setStroke(dp(1), this@MainActivity.colors.border)
            }
        }
        parent.addView(
            panel,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(7)
                bottomMargin = dp(7)
            }
        )
        panel.content()
        return panel
    }

    private fun addProgressTrack(parent: LinearLayout, progress: Float, color: Int) {
        val ratio = progress.coerceIn(0f, 1f)
        val track = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            background = roundedDrawable(colors.border, 5)
        }
        if (ratio > 0f) {
            track.addView(
                View(this).apply { background = roundedDrawable(color, 5) },
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, ratio)
            )
        }
        if (ratio < 1f) {
            track.addView(
                View(this),
                LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.MATCH_PARENT, 1f - ratio)
            )
        }
        parent.addView(
            track,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(8)
            ).apply {
                topMargin = dp(8)
                bottomMargin = dp(8)
            }
        )
    }

    private fun roundedDrawable(color: Int, radiusDp: Int, stroke: Int? = null) =
        GradientDrawable().apply {
            setColor(color)
            cornerRadius = dp(radiusDp).toFloat()
            if (stroke != null) setStroke(dp(1), stroke)
        }

    private fun text(
        parent: LinearLayout,
        value: String,
        size: Float,
        color: Int = colors.ink,
        bold: Boolean = false
    ): TextView {
        val view = TextView(this).apply {
            text = value
            textSize = size
            setTextColor(color)
            if (bold) setTypeface(typeface, Typeface.BOLD)
            setPadding(0, dp(3), 0, dp(3))
        }
        parent.addView(
            view,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        )
        return view
    }

    private fun actionButton(
        parent: LinearLayout,
        title: String,
        background: Int,
        enabled: Boolean = true,
        action: () -> Unit
    ): Button {
        val button = Button(this).apply {
            text = title
            isAllCaps = false
            isEnabled = enabled
            textSize = 16f
            setTextColor(
                if (background == colors.card || background == colors.peach) {
                    colors.ink
                } else {
                    Color.WHITE
                }
            )
            backgroundTintList = ColorStateList.valueOf(background)
            setPadding(dp(14), dp(8), dp(14), dp(8))
            setOnClickListener {
                playClickSound()
                action()
            }
        }
        parent.addView(
            button,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            ).apply {
                topMargin = dp(5)
                bottomMargin = dp(5)
            }
        )
        return button
    }

    private fun space(parent: LinearLayout, heightDp: Int) {
        parent.addView(View(this), LinearLayout.LayoutParams(1, dp(heightDp)))
    }

    private fun matchWidth() =
        LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply {
            topMargin = dp(8)
            bottomMargin = dp(8)
        }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).roundToInt()

    private fun storyIcon(key: String) = when (key.lowercase()) {
        "couple" -> "💑"
        "health_center" -> "🏥"
        "seminar" -> "📋"
        "classroom" -> "🏫"
        "midwife" -> "👩‍⚕️"
        "counselor" -> "🧑‍💼"
        "condom" -> "🛡️"
        else -> "📖"
    }

    companion object {
        private val badgeInfo = linkedMapOf(
            "first_step" to Triple("🌱", "First Step", "Complete Level 1"),
            "beginner" to Triple("📗", "Beginner", "Complete Levels 1 and 2"),
            "intermediate" to Triple("📘", "Intermediate", "Complete Levels 1–4"),
            "expert" to Triple("📕", "Expert", "Complete Levels 5 and 6"),
            "deciwise" to Triple("🎓", "DeciWise Master", "Complete all six levels"),
            "perfect_run" to Triple("🏆", "Perfect Run", "Get a perfect score"),
            "speedster" to Triple("⚡", "Speedster", "Answer five questions quickly")
        )
    }
}

private object Colors {
    val background = Color.rgb(253, 246, 240)
    val card = Color.WHITE
    val peach = Color.rgb(254, 240, 230)
    val banner = Color.rgb(251, 232, 220)
    val accent = Color.rgb(201, 123, 90)
    val accent2 = Color.rgb(232, 168, 135)
    val ink = Color.rgb(61, 35, 20)
    val muted = Color.rgb(160, 128, 112)
    val gold = Color.rgb(201, 132, 42)
    val border = Color.rgb(239, 226, 216)
    val easy = Color.rgb(74, 191, 138)
    val medium = Color.rgb(232, 160, 64)
    val hard = Color.rgb(217, 107, 107)
    val success = Color.rgb(218, 243, 224)
    val successInk = Color.rgb(65, 140, 90)
    val wrong = Color.rgb(190, 75, 75)
    val locked = Color.rgb(243, 235, 230)
    val lockedText = Color.rgb(175, 160, 150)
    val chapterTwo = Color.rgb(212, 146, 42)
    val chapterThree = Color.rgb(141, 94, 170)
    val kahootPanel = Color.rgb(26, 26, 46)
    val mythPanel = Color.rgb(74, 42, 24)
    val kahootRed = Color.rgb(231, 76, 60)
    val kahootBlue = Color.rgb(52, 152, 219)
    val kahootYellow = Color.rgb(241, 196, 22)
    val kahootGreen = Color.rgb(46, 204, 113)
    val kahootMuted = Color.rgb(150, 150, 150)
    val myth = Color.rgb(142, 68, 173)
}
