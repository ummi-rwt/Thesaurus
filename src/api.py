import sqlite3

from fastapi import FastAPI, HTTPException

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
    lemmas = con.execute(
        "SELECT DISTINCT lemma FROM forms WHERE lower(form) = ?", (word,)
    ).fetchall()
    forms_info = con.execute(
        "SELECT lemma, description FROM forms WHERE lower(form) = ? LIMIT 6", (word,)
    ).fetchall()
    candidates = [word] + [l[0] for l in lemmas]
    entries, seen = [], set()
    for cand in candidates:
        for wid, w, pos in con.execute(
            "SELECT id, word, pos FROM words WHERE lower(word) = ? ORDER BY id",
            (cand.lower(),),
        ).fetchall():
            if wid in seen:
                continue
            seen.add(wid)
            glosses = [
                g[0]
                for g in con.execute(
                    "SELECT gloss FROM translations WHERE word_id = ? ORDER BY rank",
                    (wid,),
                )
            ]
            entries.append({"word": w, "pos": pos, "translations": glosses})
    return entries, [
        {"lemma": l, "description": d} for l, d in forms_info
    ]


def english_entries(con, word):
    rows = con.execute(
        """SELECT w.word, w.pos, t.gloss FROM translations t
           JOIN words w ON w.id = t.word_id
           WHERE lower(t.gloss) = :w OR lower(t.gloss) = 'to ' || :w
              OR lower(t.gloss) LIKE :w || ', %'
              OR lower(t.gloss) LIKE '%, ' || :w
              OR lower(t.gloss) LIKE '%, ' || :w || ',%'
           ORDER BY
              CASE WHEN lower(t.gloss) IN (:w, 'to ' || :w) THEN 0 ELSE 1 END,
              t.rank, w.id
           LIMIT 30""",
        {"w": word},
    ).fetchall()
    return [{"word": w, "pos": pos, "gloss": g} for w, pos, g in rows]


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
