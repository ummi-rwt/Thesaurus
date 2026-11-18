import re
import sqlite3

from fastapi import APIRouter, HTTPException

DB = "data/thesaurus.db"
router = APIRouter(tags=["excerpts"])

FILMS = {
    "tears-of-steel": {
        "title": "Tears of Steel",
        "credit": "Tears of Steel (CC BY 3.0), Blender Foundation",
    }
}


def norm(text):
    return re.sub(r"[^\w]+", " ", text.lower()).strip()


@router.get("/excerpts")
def excerpts(word: str, lang: str = "fr", limit: int = 2):
    if lang not in ("fr", "en"):
        raise HTTPException(status_code=400, detail="lang doit valoir fr ou en")
    word = word.lower().replace('"', "").strip()
    if not word:
        raise HTTPException(status_code=400, detail="mot vide")
    limit = max(1, min(limit, 10))

    text_col = "fr_text" if lang == "fr" else "en_text"
    cols = "{fr_text fr_lemmas}" if lang == "fr" else "{en_text en_lemmas}"
    query = f'{cols} : "{word}"'

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        rows = con.execute(
            f"""SELECT e.id, e.film, e.start_ms, e.end_ms, e.fr_text, e.en_text
                FROM excerpts_fts JOIN excerpts e ON e.id = excerpts_fts.rowid
                WHERE excerpts_fts MATCH ?
                ORDER BY length(e.{text_col}), e.start_ms LIMIT 100""",
            (query,),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        con.close()

    seen, unique = set(), []
    for id_, film, start, end, fr, en in rows:
        key = norm(fr if lang == "fr" else en)
        if key in seen:
            continue
        seen.add(key)
        unique.append({
            "id": id_,
            "film": FILMS.get(film, {}).get("title", film),
            "film_id": film,
            "start_ms": start,
            "end_ms": end,
            "fr": fr,
            "en": en,
        })
    shown = unique[:limit]
    credits = sorted({FILMS[x["film_id"]]["credit"] for x in shown if x["film_id"] in FILMS})
    return {
        "word": word, "lang": lang,
        "total": len(unique), "credits": credits, "excerpts": shown,
    }
