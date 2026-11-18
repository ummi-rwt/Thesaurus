import sqlite3

from fastapi import FastAPI, HTTPException

DB = "data/thesaurus.db"
app = FastAPI(title="Thesaurus")


@app.get("/search")
def search(word: str, lang: str = "fr", limit: int = 5):
    if lang not in ("fr", "en"):
        raise HTTPException(status_code=400, detail="lang doit valoir fr ou en")
    word = word.lower().replace('"', "").strip()
    if not word:
        raise HTTPException(status_code=400, detail="mot vide")
    limit = max(1, min(limit, 20))

    text_col = "fr_text" if lang == "fr" else "en_text"
    cols = "{fr_text fr_lemmas}" if lang == "fr" else "{en_text en_lemmas}"
    query = f'{cols} : "{word}"'

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
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
    finally:
        con.close()

    return {
        "word": word,
        "lang": lang,
        "total": total,
        "examples": [{"fr": fr, "en": en} for fr, en in rows],
    }
