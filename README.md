# ⚽ Match Day Quiz — World Cup 2026

A fast, shareable daily quiz that goes live after every World Cup 2026 match day.
Recap trivia, a screenshot-ready score card, friend challenges, a daily leaderboard, day
streaks, and a **tournament-long competition with a champion crowned at the end**.

New here? Read **`DECISIONS.md`** for the *why* behind every choice. This file is the
*how-to-run-it*.

---

## What's in the box

| File | Purpose |
|---|---|
| `index.html` | The whole app. One file, no build step. |
| `quizzes/` | `latest.json` (loaded on open), `index.json` (archive), one `matchday-*.json` per day, `SCHEMA.md`. |
| `generate_quiz.py` | Pulls match data and writes a new quiz automatically. |
| `DECISIONS.md` | The product/strategy decisions. |
| `README.md` | This file. |

---

## 1. Try it now

Double-click `index.html`. It opens in your browser, fully playable with the built-in
sample quiz. To load the real JSON files, run a tiny local server:

```bash
cd "FWC26 Quiz Game"
python3 -m http.server 8000
# open http://localhost:8000
```

---

## 2. Generate a new quiz (the daily engine)

```bash
python3 generate_quiz.py                # yesterday's match day
python3 generate_quiz.py 2026-06-17     # a specific date
python3 generate_quiz.py --today        # today's fixtures (preview mode)
```

It pulls the free, no-key **openfootball** World Cup 2026 feed, builds 10 questions, and
writes `quizzes/matchday-<date>.json`, refreshes `quizzes/latest.json`, and updates the
archive in `quizzes/index.json`. If results are in it makes a recap (scores/winners/goals);
if not, a preview (matchups/cities/groups) — re-run after full time to upgrade it.

Richer questions later: only `fetch_matches()` knows about the data source — swap it for a
paid API (API-Football, Sportmonks, BALLDONTLIE) and everything else still works.

---

## 3. Tournament-long competition 🏆

Beyond each day's board, the app keeps an **overall leaderboard**: every player's best score
per match day, summed across the whole tournament. Players see it via the **🏆 Overall** tab
on the results screen and the **Tournament standings** button on the home screen. When the
tournament ends, whoever tops the overall board is crowned **Tournament Champion** in-app.

Two settings near the top of `index.html` control it:

```js
TOURNAMENT_END: "2026-07-19",   // after this date, the leader becomes the champion
PRIZE: "🏆 Bragging rights as Tournament Champion"   // change to a real prize if you have one
```

> The overall board is only as complete as the leaderboard storage. On-device storage means
> each phone sees its own totals; to run a *real* shared season-long competition, turn on the
> global board (next section). That's what makes "someone wins at the end" meaningful across
> all your players.

---

## 4. The global leaderboard (needed for a real shared competition)

Out of the box, scores/streaks/standings are stored **on each visitor's device** — works
instantly, zero setup, but everyone sees only their own board. For a shared board (and a real
champion across all players), wire up **Supabase** (free tier):

1. Create a project at supabase.com.
2. SQL editor → run:
   ```sql
   create table scores (
     id bigint generated always as identity primary key,
     name text not null, score int not null, correct int,
     quiz text not null, ts bigint
   );
   alter table scores enable row level security;
   create policy "anyone can read"   on scores for select using (true);
   create policy "anyone can insert" on scores for insert with check (true);
   ```
3. In `index.html`, fill the `CONFIG` block:
   ```js
   SUPABASE_URL: "https://YOURPROJECT.supabase.co",
   SUPABASE_ANON_KEY: "your-anon-public-key",
   ```
The app auto-switches from on-device to the shared board, including the overall standings.

---

## 5. Put it online (free) with GitHub Pages

This project is already a GitHub repo. To host it:

1. On the repo's GitHub page → **Settings → Pages** → Source: **Deploy from a branch**,
   Branch **main**, folder **/ (root)** → Save.
2. The repo must be **Public** for free Pages (Settings → bottom → change visibility).
3. Wait a few minutes; your live link appears at the top of the Pages screen:
   `https://<you>.github.io/FWC26-Quiz-Game/`

### Updating the live site after you change anything
The live site only updates when you **push** your changes to GitHub. In **GitHub Desktop**:
open the app → you'll see your changed files listed → type a short summary →
**Commit to main** → **Push origin**. Pages rebuilds automatically in 1–2 minutes.

---

## 6. Make it update itself every match day (GitHub Actions)

Create `.github/workflows/daily-quiz.yml`:
```yaml
name: Daily quiz
on:
  schedule:
    - cron: "0 6 * * *"     # 06:00 UTC daily
  workflow_dispatch:
permissions:
  contents: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python3 generate_quiz.py
      - run: |
          git config user.name  "quiz-bot"
          git config user.email "bot@users.noreply.github.com"
          git add quizzes data
          git commit -m "auto: quiz for $(date -u +%F)" || echo "no changes"
          git push
```
With Pages + this workflow, the quiz rebuilds and redeploys daily, hands-off. (Once this is
running in the cloud, you can delete the local 7 AM scheduled task — it does the same job.)

---

## 7. Customize

- **Name & colours:** title text in `index.html`; palette is the `:root` CSS variables.
- **Timer / points:** `CONFIG.QUIZ_SECONDS` and the `PTS` map.
- **Tournament end / prize:** `CONFIG.TOURNAMENT_END` and `CONFIG.PRIZE`.
- **Questions:** edit any `quizzes/*.json` by hand (see `quizzes/SCHEMA.md`).

---

## 8. Go-viral checklist

1. **Post your own score card every match day** with the day's hook. You're content engine #1.
2. **Seed challenge links in football group chats** — the warmest install.
3. **Reply under big match-recap posts** the moment a game ends, at peak attention.
4. **Hype the title race:** as the tournament goes on, post the overall top 3 — a season-long
   leaderboard with a champion at the end is what keeps people coming back every single day.
5. **Keep quizzes live on time, every match day.** Consistency turns players into a habit.
6. **Add the global board once people share** — ship on-device today, wire Supabase when it pops.

Kickoff was June 11; the final is July 19. Five-week window — make every match day count.
