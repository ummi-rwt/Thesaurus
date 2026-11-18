from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from srs import START_EASE, next_state
from usage import connect, now

router = APIRouter(prefix="/usage", tags=["review"])

SETUP = """
CREATE TABLE IF NOT EXISTS card_state (
    saved_word_id INTEGER PRIMARY KEY REFERENCES saved_words(id),
    repetitions INTEGER NOT NULL, ease REAL NOT NULL,
    interval_days INTEGER NOT NULL, due_date TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS card_cleanup AFTER DELETE ON saved_words
BEGIN
    DELETE FROM card_state WHERE saved_word_id = OLD.id;
END;
"""


def connect_review():
    con = connect()
    con.executescript(SETUP)
    cols = [r[1] for r in con.execute("PRAGMA table_info(reviews)")]
    if "quality" not in cols:
        con.execute("ALTER TABLE reviews ADD COLUMN quality INTEGER")
        con.commit()
    return con


connect_review().close()


def today():
    return datetime.now(timezone.utc).date()


class Review(BaseModel):
    user: str = Field(min_length=1, max_length=64)
    saved_word_id: int
    quality: int = Field(ge=0, le=5)


DUE = "(c.due_date IS NULL OR c.due_date <= ?)"
FROM = "FROM saved_words s LEFT JOIN card_state c ON c.saved_word_id = s.id"


@router.get("/review")
def due_cards(user: str, limit: int = 20):
    limit = max(1, min(limit, 50))
    day = today().isoformat()
    con = connect_review()
    try:
        total = con.execute(
            "SELECT count(*) FROM saved_words WHERE user_id = ?", (user,)
        ).fetchone()[0]
        due = con.execute(
            f"SELECT count(*) {FROM} WHERE s.user_id = ? AND {DUE}", (user, day)
        ).fetchone()[0]
        rows = con.execute(
            f"""SELECT s.id, s.word, s.lang, s.translation, c.repetitions, c.due_date
                {FROM} WHERE s.user_id = ? AND {DUE}
                ORDER BY c.due_date IS NULL, c.due_date, s.id LIMIT ?""",
            (user, day, limit),
        ).fetchall()
    finally:
        con.close()
    return {
        "total": total,
        "due": due,
        "cards": [
            {"id": i, "word": w, "lang": lg, "translation": t,
             "repetitions": r or 0, "due_date": d}
            for i, w, lg, t, r, d in rows
        ],
    }


@router.post("/review")
def submit_review(body: Review):
    con = connect_review()
    try:
        owned = con.execute(
            "SELECT 1 FROM saved_words WHERE id = ? AND user_id = ?",
            (body.saved_word_id, body.user),
        ).fetchone()
        if not owned:
            raise HTTPException(status_code=404, detail="mot introuvable")
        row = con.execute(
            "SELECT repetitions, ease, interval_days FROM card_state WHERE saved_word_id = ?",
            (body.saved_word_id,),
        ).fetchone()
        reps, ease, interval = row if row else (0, START_EASE, 0)
        reps, ease, interval, due = next_state(reps, ease, interval, body.quality, today())
        con.execute(
            """INSERT INTO card_state
                   (saved_word_id, repetitions, ease, interval_days, due_date)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(saved_word_id) DO UPDATE SET
                   repetitions = excluded.repetitions, ease = excluded.ease,
                   interval_days = excluded.interval_days, due_date = excluded.due_date""",
            (body.saved_word_id, reps, ease, interval, due.isoformat()),
        )
        con.execute(
            "INSERT INTO reviews (saved_word_id, known, ts, quality) VALUES (?, ?, ?, ?)",
            (body.saved_word_id, int(body.quality >= 3), now(), body.quality),
        )
        con.commit()
    finally:
        con.close()
    return {
        "saved_word_id": body.saved_word_id,
        "repetitions": reps,
        "ease": round(ease, 2),
        "interval_days": interval,
        "due_date": due.isoformat(),
    }
