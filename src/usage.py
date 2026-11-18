import sqlite3
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

USAGE_DB = "data/usage.db"
router = APIRouter(prefix="/usage", tags=["usage"])

SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL, word TEXT NOT NULL, lang TEXT NOT NULL,
    found INTEGER NOT NULL, ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS saved_words (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL, word TEXT NOT NULL, lang TEXT NOT NULL,
    translation TEXT NOT NULL, saved_at TEXT NOT NULL,
    UNIQUE (user_id, word, lang)
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    saved_word_id INTEGER NOT NULL REFERENCES saved_words(id),
    known INTEGER NOT NULL, ts TEXT NOT NULL
);
"""


def connect():
    con = sqlite3.connect(USAGE_DB)
    con.executescript(SCHEMA)
    return con


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SaveWord(BaseModel):
    user: str = Field(min_length=1, max_length=64)
    word: str = Field(min_length=1, max_length=100)
    lang: Literal["fr", "en"]
    translation: str = Field(min_length=1, max_length=300)


class SearchEvent(BaseModel):
    user: str = Field(min_length=1, max_length=64)
    word: str = Field(min_length=1, max_length=100)
    lang: Literal["fr", "en"]
    found: bool


@router.post("/words")
def save_word(body: SaveWord):
    word = body.word.strip().lower()
    translation = body.translation.strip()
    if not word or not translation:
        raise HTTPException(status_code=400, detail="mot ou traduction vide")
    con = connect()
    try:
        cur = con.execute(
            "INSERT OR IGNORE INTO saved_words "
            "(user_id, word, lang, translation, saved_at) VALUES (?, ?, ?, ?, ?)",
            (body.user, word, body.lang, translation, now()),
        )
        con.commit()
        if cur.rowcount == 0:
            row = con.execute(
                "SELECT id FROM saved_words WHERE user_id = ? AND word = ? AND lang = ?",
                (body.user, word, body.lang),
            ).fetchone()
            return {"saved": False, "id": row[0], "detail": "deja dans le carnet"}
        return {"saved": True, "id": cur.lastrowid}
    finally:
        con.close()


@router.get("/words")
def list_words(user: str, day: str | None = None):
    sql = ("SELECT id, word, lang, translation, saved_at "
           "FROM saved_words WHERE user_id = ?")
    params = [user]
    if day:
        sql += " AND substr(saved_at, 1, 10) = ?"
        params.append(day)
    sql += " ORDER BY id DESC"
    con = connect()
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    return {
        "count": len(rows),
        "words": [
            {"id": i, "word": w, "lang": lg, "translation": t, "saved_at": s}
            for i, w, lg, t, s in rows
        ],
    }


@router.delete("/words/{word_id}")
def delete_word(word_id: int, user: str):
    con = connect()
    try:
        owned = con.execute(
            "SELECT 1 FROM saved_words WHERE id = ? AND user_id = ?", (word_id, user)
        ).fetchone()
        if not owned:
            raise HTTPException(status_code=404, detail="mot introuvable")
        con.execute("DELETE FROM reviews WHERE saved_word_id = ?", (word_id,))
        con.execute("DELETE FROM saved_words WHERE id = ?", (word_id,))
        con.commit()
    finally:
        con.close()
    return {"deleted": word_id}


@router.post("/searches")
def log_search(body: SearchEvent):
    word = body.word.strip().lower()
    if not word:
        raise HTTPException(status_code=400, detail="mot vide")
    con = connect()
    try:
        con.execute(
            "INSERT INTO searches (user_id, word, lang, found, ts) VALUES (?, ?, ?, ?, ?)",
            (body.user, word, body.lang, int(body.found), now()),
        )
        con.commit()
    finally:
        con.close()
    return {"logged": True}
