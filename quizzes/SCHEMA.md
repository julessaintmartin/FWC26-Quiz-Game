# Quiz JSON schema

Every daily quiz is one file: `quizzes/matchday-YYYY-MM-DD.json`.

```jsonc
{
  "id": "2026-06-17",            // unique id, = the match date
  "matchday": "Matchday 7",      // label shown in the app
  "date": "2026-06-17",          // ISO date of the matches
  "title": "Matchday 7 Recap",   // headline
  "subtitle": "England, Portugal & Argentina get going",
  "generated": "auto",           // "auto" (from pipeline) or "manual"
  "questions": [
    {
      "q": "Question text?",
      "options": ["A", "B", "C", "D"],   // 2-4 options
      "answer": 1,                        // 0-based index of the correct option
      "explain": "One line shown after answering.",
      "difficulty": "easy"                // easy | medium | hard (controls points)
    }
    // ...10 questions
  ]
}
```

Two index files keep the app pointed at the right content:

- `quizzes/index.json` — `{ "quizzes": [ {id, date, matchday, title}, ... ] }`, newest first.
  Powers the "past quizzes" archive.
- `quizzes/latest.json` — a copy of the most recent quiz. The app loads this on open.

The generator (`generate_quiz.py`) writes all three automatically.
