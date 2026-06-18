#!/usr/bin/env python3
"""
generate_quiz.py — the auto-update pipeline for Match Day Quiz (World Cup 2026)

What it does
------------
1. Pulls the public-domain World Cup 2026 fixture/result feed (openfootball — no API key).
2. Finds the matches for a given date (default: yesterday, i.e. the match day that just finished).
3. Builds a 10-question recap-trivia quiz:
     - if results are in  -> score / winner / goals questions
     - always            -> confirmed-fact questions (venue, group, matchup) so we
                            never ship fewer than 10, even before scores land
4. Writes  quizzes/matchday-YYYY-MM-DD.json
   updates quizzes/index.json   (archive, newest first)
   writes  quizzes/latest.json  (what the app loads on open)

Usage
-----
    python3 generate_quiz.py                # yesterday's match day
    python3 generate_quiz.py 2026-06-17     # a specific date
    python3 generate_quiz.py --today        # today

Swapping the data source
------------------------
Only `fetch_matches()` knows about the feed. To use a richer paid API
(API-Football, Sportmonks, BALLDONTLIE) for goalscorers etc., reimplement
that one function to return the same shape:
    [{team1, team2, group, ground, score1, score2, date}, ...]
Everything downstream stays the same.
"""

import json, sys, os, random, urllib.request, datetime
from pathlib import Path

FEED = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
OUT  = Path(__file__).parent / "quizzes"

HOST_CITIES = ["Atlanta","Boston (Foxborough)","Dallas (Arlington)","Guadalajara (Zapopan)",
    "Houston","Kansas City","Los Angeles (Inglewood)","Mexico City","Miami (Miami Gardens)",
    "Monterrey (Guadalupe)","New York/New Jersey (East Rutherford)","Philadelphia",
    "San Francisco Bay Area (Santa Clara)","Seattle","Toronto","Vancouver"]

# ----------------------------------------------------------------------
# 1. DATA SOURCE  (the only feed-specific function)
# ----------------------------------------------------------------------
def fetch_matches(date_str):
    """Return the list of matches on `date_str` (YYYY-MM-DD).

    Tries the live feed first; if the network is unavailable, falls back to a
    local cache at data/worldcup.json (run `python3 generate_quiz.py --cache`
    once from a networked machine to create it)."""
    data = None
    try:
        req = urllib.request.Request(FEED, headers={"User-Agent": "matchday-quiz/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        # keep a local cache for offline runs
        try:
            (Path(__file__).parent / "data").mkdir(exist_ok=True)
            (Path(__file__).parent / "data" / "worldcup.json").write_text(json.dumps(data))
        except Exception:
            pass
    except Exception as e:
        cache = Path(__file__).parent / "data" / "worldcup.json"
        if cache.exists():
            print(f"  (network unavailable — using cached {cache})")
            data = json.loads(cache.read_text())
        else:
            raise SystemExit(f"Could not reach feed and no local cache found: {e}")
    out = []
    for m in data.get("matches", []):
        if m.get("date") != date_str:
            continue
        score = m.get("score", {}).get("ft")  # [a,b] once played, else None
        out.append({
            "team1": m.get("team1"), "team2": m.get("team2"),
            "group": m.get("group"), "ground": m.get("ground"),
            "score1": score[0] if score else None,
            "score2": score[1] if score else None,
            "date": date_str,
        })
    return out

# ----------------------------------------------------------------------
# 2. QUESTION BUILDERS
# ----------------------------------------------------------------------
def mcq(q, correct, distractors, explain, difficulty):
    """Assemble a multiple-choice question with the answer shuffled in."""
    opts = [correct] + [d for d in distractors if d != correct][:3]
    # ensure 4 unique options where possible
    opts = list(dict.fromkeys(opts))
    random.shuffle(opts)
    return {"q": q, "options": opts, "answer": opts.index(correct),
            "explain": explain, "difficulty": difficulty}

def result_questions(m):
    """Questions that only exist once a result is known."""
    qs = []
    t1, t2 = m["team1"], m["team2"]
    s1, s2 = m["score1"], m["score2"]
    if s1 is None or s2 is None:
        return qs
    total = s1 + s2
    # winner
    if s1 == s2:
        winner, ex = "Draw", f"{t1} and {t2} drew {s1}–{s2}."
    else:
        winner = t1 if s1 > s2 else t2
        ex = f"{winner} won {max(s1,s2)}–{min(s1,s2)}."
    qs.append(mcq(f"Who came out on top in {t1} vs {t2}?",
                  winner, [t1, t2, "Draw"], ex, "easy"))
    # exact score
    real = f"{s1}–{s2}"
    fakes = [f"{s1+1}–{s2}", f"{s1}–{s2+1}", f"{max(s1-1,0)}–{s2}", "1–1", "2–1", "0–0"]
    qs.append(mcq(f"What was the final score in {t1} vs {t2}?",
                  real, fakes, f"It finished {real}.", "medium"))
    # total goals
    qs.append(mcq(f"How many goals were scored in total in {t1} vs {t2}?",
                  str(total), [str(total+1), str(max(total-1,0)), str(total+2)],
                  f"{total} goal(s) were scored in the {real} result.", "hard"))
    return qs

def fact_questions(matches):
    """Confirmed-fact questions, available even before kickoff."""
    qs = []
    for m in matches:
        t1, t2, grd, grp = m["team1"], m["team2"], m["ground"], m["group"]
        if grd:
            qs.append(mcq(f"In which host city did {t1} face {t2}?",
                          grd, random.sample([c for c in HOST_CITIES if c != grd], 3),
                          f"The match was played in {grd}.", "medium"))
        if grp:
            other_groups = [f"Group {g}" for g in "ABCDEFGHIJKL" if f"Group {g}" != grp]
            qs.append(mcq(f"{t1} and {t2} both play in which group?",
                          grp, random.sample(other_groups, 3),
                          f"Both teams are in {grp}.", "easy"))
    return qs

EVERGREEN = [
    {"q":"How many teams are competing at the 2026 World Cup?","options":["32","40","48","64"],
     "answer":2,"explain":"2026 is the first 48-team World Cup.","difficulty":"easy"},
    {"q":"Which three nations are co-hosting the 2026 World Cup?","options":
     ["USA, Canada & Mexico","USA & Mexico","Canada & USA","USA, Mexico & Guatemala"],
     "answer":0,"explain":"It is the first World Cup hosted by three countries.","difficulty":"easy"},
    {"q":"Where is the 2026 World Cup final being held (July 19)?","options":
     ["MetLife Stadium, NY/NJ","SoFi Stadium, LA","Estadio Azteca","AT&T Stadium"],
     "answer":0,"explain":"The final is at MetLife Stadium in East Rutherford, NJ.","difficulty":"medium"},
    {"q":"How many matches are played across the whole 2026 tournament?","options":
     ["64","80","104","128"],"answer":2,"explain":"The expanded format has 104 matches.","difficulty":"hard"},
]

# ----------------------------------------------------------------------
# 3. ASSEMBLE
# ----------------------------------------------------------------------
def build_quiz(date_str, matches):
    md = matches[0].get("round") if matches and matches[0].get("round") else None
    # derive a matchday label from data if available; else from date
    label = next((mm.get("round") for mm in [] if mm), None)
    pool = []
    for m in matches:
        pool += result_questions(m)
    pool += fact_questions(matches)
    random.shuffle(pool)
    pool += [dict(q) for q in EVERGREEN]            # guarantee fillers at the end

    # de-dupe by question text, take 10
    seen, qs = set(), []
    for q in pool:
        if q["q"] in seen: continue
        seen.add(q["q"]); qs.append(q)
        if len(qs) == 10: break

    teams = [t for m in matches for t in (m["team1"], m["team2"])]
    headline = ", ".join(dict.fromkeys(teams))[:80] if teams else "Today's matches"
    matchday = matchday_label(date_str)
    played = any(m["score1"] is not None for m in matches)
    return {
        "id": date_str, "matchday": matchday, "date": date_str,
        "title": f"{matchday} Recap" if played else f"{matchday} Preview",
        "subtitle": (f"Recap of {headline}" if played else f"Get ready: {headline}"),
        "generated": "auto",
        "questions": qs,
    }

def matchday_label(date_str):
    """Map a date to its 'Matchday N' number using the group-stage start (June 11)."""
    d = datetime.date.fromisoformat(date_str)
    start = datetime.date(2026, 6, 11)
    n = (d - start).days + 1
    if 1 <= n <= 17:
        return f"Matchday {n}"
    return d.strftime("%b %-d") if os.name != "nt" else d.strftime("%b %d")

# ----------------------------------------------------------------------
# 4. WRITE FILES
# ----------------------------------------------------------------------
def write_all(quiz):
    OUT.mkdir(exist_ok=True)
    fname = f"matchday-{quiz['id']}.json"
    (OUT / fname).write_text(json.dumps(quiz, indent=2, ensure_ascii=False))
    (OUT / "latest.json").write_text(json.dumps(quiz, indent=2, ensure_ascii=False))

    # update archive index (newest first, de-duped)
    idx_path = OUT / "index.json"
    idx = {"quizzes": []}
    if idx_path.exists():
        try: idx = json.loads(idx_path.read_text())
        except Exception: pass
    idx["quizzes"] = [q for q in idx.get("quizzes", []) if q.get("id") != quiz["id"]]
    idx["quizzes"].insert(0, {"id": quiz["id"], "date": quiz["date"],
        "matchday": quiz["matchday"], "title": quiz["title"], "file": fname})
    idx["quizzes"].sort(key=lambda q: q["date"], reverse=True)
    idx_path.write_text(json.dumps(idx, indent=2, ensure_ascii=False))
    return fname

# ----------------------------------------------------------------------
def main():
    args = [a for a in sys.argv[1:]]
    if "--today" in args:
        date_str = datetime.date.today().isoformat()
    elif args and args[0][0].isdigit():
        date_str = args[0]
    else:
        date_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    print(f"→ Building quiz for {date_str}")
    matches = fetch_matches(date_str)
    if not matches:
        print(f"  No matches found for {date_str}. Nothing to generate.")
        sys.exit(0)
    print(f"  Found {len(matches)} match(es): "
          + "; ".join(f"{m['team1']} v {m['team2']}" for m in matches))
    quiz = build_quiz(date_str, matches)
    fname = write_all(quiz)
    played = any(m["score1"] is not None for m in matches)
    print(f"  {'Results were in' if played else 'No results yet (preview mode)'} — "
          f"wrote {len(quiz['questions'])} questions.")
    print(f"✓ {OUT/fname}\n✓ {OUT/'latest.json'}\n✓ {OUT/'index.json'}")

if __name__ == "__main__":
    main()
