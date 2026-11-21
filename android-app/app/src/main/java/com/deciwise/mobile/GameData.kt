package com.deciwise.mobile

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

data class GameQuestion(
    val question: String,
    val options: List<String>,
    val answer: String,
    val explanation: String
)

data class WordClue(val word: String, val hint: String)
data class JigsawPiece(val label: String, val description: String)

data class GameLevel(
    val id: Int,
    val title: String,
    val difficulty: String,
    val difficultyColor: String,
    val quizType: String,
    val story: String,
    val storyImage: String,
    val kahoot: List<GameQuestion>,
    val mythFact: List<GameQuestion>,
    val beginner: List<GameQuestion>,
    val intermediate: List<GameQuestion>,
    val difficult: List<GameQuestion>,
    val hangman: List<WordClue>,
    val jigsaw: List<JigsawPiece>,
    val crossword: List<WordClue>,
    val jotto: List<WordClue>
)

object GameData {
    fun readLevels(context: Context): List<GameLevel> {
        val source = context.assets.open("questions.json")
            .bufferedReader()
            .use { it.readText() }
        val levels = JSONObject(source).getJSONArray("levels")
        return (0 until levels.length()).map { parseLevel(levels.getJSONObject(it)) }
    }

    private fun parseLevel(source: JSONObject): GameLevel {
        val quizOptions = listOf("MYTH", "FACT")
        return GameLevel(
            id = source.getInt("id"),
            title = source.optString("title"),
            difficulty = source.optString("difficulty", "Easy"),
            difficultyColor = source.optString("difficulty_color", "#C97B5A"),
            quizType = source.optString("quiz_type", "standard"),
            story = source.optString("story"),
            storyImage = source.optString("story_image"),
            kahoot = questions(source.optJSONArray("kahoot")),
            mythFact = questions(source.optJSONArray("myth_fact"), quizOptions),
            beginner = questions(source.optJSONArray("beginner")),
            intermediate = questions(source.optJSONArray("intermediate")),
            difficult = questions(source.optJSONArray("difficult")),
            hangman = wordClues(source.optJSONArray("hangman")),
            jigsaw = jigsawPieces(source.optJSONArray("jigsaw")),
            crossword = wordClues(source.optJSONArray("crossword")),
            jotto = wordClues(source.optJSONArray("jotto"))
        )
    }

    private fun questions(array: JSONArray?, defaultOptions: List<String> = emptyList()) =
        (0 until (array?.length() ?: 0)).map { index ->
            val item = array!!.getJSONObject(index)
            val options = item.optJSONArray("options")?.strings() ?: defaultOptions
            GameQuestion(
                question = item.optString("question"),
                options = options,
                answer = item.optString("answer"),
                explanation = item.optString("explanation")
            )
        }

    private fun wordClues(array: JSONArray?) =
        (0 until (array?.length() ?: 0)).map { index ->
            val item = array!!.getJSONObject(index)
            WordClue(item.optString("word").uppercase(), item.optString("hint"))
        }

    private fun jigsawPieces(array: JSONArray?) =
        (0 until (array?.length() ?: 0)).map { index ->
            val item = array!!.getJSONObject(index)
            JigsawPiece(item.optString("label"), item.optString("description"))
        }

    private fun JSONArray.strings() =
        (0 until length()).map { getString(it) }
}
