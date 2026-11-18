import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

DB = "data/thesaurus.db"
app = FastAPI(title="Thesaurus")


def connect():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def clean_word(word):
    word = word.lower().replace('"', "").strip()
    if not word:
        raise HTTPException(status_code=400, detail="mot vide")
    return word


def check_lang(lang):
    if lang not in ("fr", "en"):
        raise HTTPException(status_code=400, detail="lang doit valoir fr ou en")


def get_freq(con, word):
    row = con.execute("SELECT n FROM word_freq WHERE word = ?", (word.lower(),)).fetchone()
    return row[0] if row else 0


def get_examples(con, word, lang, limit):
    text_col = "fr_text" if lang == "fr" else "en_text"
    cols = "{fr_text fr_lemmas}" if lang == "fr" else "{en_text en_lemmas}"
    query = f'{cols} : "{word}"'
    total = con.execute(
        "SELECT count(*) FROM pairs_fts WHERE pairs_fts MATCH ?", (query,)
    ).fetchone()[0]
    rows = con.execute(
        f"""SELECT p.fr_text, p.en_text FROM pairs_fts
            JOIN pairs p ON p.id = pairs_fts.rowid
            WHERE pairs_fts MATCH ?
            ORDER BY length(p.{text_col}) LIMIT ?""",
        (query, limit),
    ).fetchall()
    return total, [{"fr": fr, "en": en} for fr, en in rows]


def french_entries(con, word):
    forms_rows = con.execute(
        "SELECT lemma, pos, description FROM forms WHERE lower(form) = ?", (word,)
    ).fetchall()
    forms_info = [{"lemma": l, "description": d} for l, _, d in forms_rows[:6]]
    lemma_pos = sorted({(l.lower(), p) for l, p, _ in forms_rows})

    entries, seen = [], set()

    def add(wid, w, pos):
        if wid in seen:
            return
        seen.add(wid)
        glosses = [
            g[0]
            for g in con.execute(
                "SELECT gloss FROM translations WHERE word_id = ? ORDER BY rank", (wid,)
            )
        ]
        entries.append(
            {"word": w, "pos": pos, "freq": get_freq(con, w), "translations": glosses}
        )

    for wid, w, pos in con.execute(
        "SELECT id, word, pos FROM words WHERE lower(word) = ? ORDER BY id", (word,)
    ).fetchall():
        add(wid, w, pos)
    for lemma, lpos in lemma_pos:
        for wid, w, pos in con.execute(
            "SELECT id, word, pos FROM words WHERE lower(word) = ? AND pos = ? ORDER BY id",
            (lemma, lpos),
        ).fetchall():
            add(wid, w, pos)
    return entries, forms_info


def english_entries(con, word):
    rows = con.execute(
        """SELECT w.word, w.pos, t.gloss, COALESCE(f.n, 0) AS freq
           FROM translations t
           JOIN words w ON w.id = t.word_id
           LEFT JOIN word_freq f ON f.word = lower(w.word)
           WHERE lower(t.gloss) = :w OR lower(t.gloss) = 'to ' || :w
              OR lower(t.gloss) LIKE :w || ', %'
              OR lower(t.gloss) LIKE '%, ' || :w
              OR lower(t.gloss) LIKE '%, ' || :w || ',%'
           ORDER BY
              CASE WHEN lower(t.gloss) IN (:w, 'to ' || :w) THEN 0 ELSE 1 END,
              freq DESC, t.rank, w.id
           LIMIT 30""",
        {"w": word},
    ).fetchall()
    return [{"word": w, "pos": p, "gloss": g, "freq": n} for w, p, g, n in rows]


@app.get("/lookup")
def lookup(word: str, lang: str = "fr", limit: int = 3):
    check_lang(lang)
    word = clean_word(word)
    limit = max(1, min(limit, 10))
    con = connect()
    try:
        total, examples = get_examples(con, word, lang, limit)
        if lang == "fr":
            entries, forms_info = french_entries(con, word)
            return {
                "word": word, "lang": lang,
                "forms": forms_info, "entries": entries,
                "total_examples": total, "examples": examples,
            }
        return {
            "word": word, "lang": lang,
            "translations": english_entries(con, word),
            "total_examples": total, "examples": examples,
        }
    finally:
        con.close()


@app.get("/search")
def search(word: str, lang: str = "fr", limit: int = 5):
    check_lang(lang)
    word = clean_word(word)
    limit = max(1, min(limit, 20))
    con = connect()
    try:
        total, examples = get_examples(con, word, lang, limit)
    finally:
        con.close()
    return {"word": word, "lang": lang, "total": total, "examples": examples}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("web/index.html")

from usage import router as usage_router  # noqa: E402

app.include_router(usage_router)

from review import router as review_router  # noqa: E402

app.include_router(review_router)


@app.get("/review", include_in_schema=False)
def review_page():
    return FileResponse("web/review.html")
