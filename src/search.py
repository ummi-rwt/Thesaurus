import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
DB = "data/thesaurus.db"


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ("fr", "en"):
        print("Usage : python src/search.py MOT fr|en")
        return
    word = sys.argv[1].lower().replace('"', "")
    lang = sys.argv[2]
    text_col = "fr_text" if lang == "fr" else "en_text"
    cols = "{fr_text fr_lemmas}" if lang == "fr" else "{en_text en_lemmas}"
    query = f'{cols} : "{word}"'

    con = sqlite3.connect(DB)
    total = con.execute(
        "SELECT count(*) FROM pairs_fts WHERE pairs_fts MATCH ?", (query,)
    ).fetchone()[0]
    rows = con.execute(
        f"""SELECT p.fr_text, p.en_text FROM pairs_fts
            JOIN pairs p ON p.id = pairs_fts.rowid
            WHERE pairs_fts MATCH ?
            ORDER BY length(p.{text_col}) LIMIT 5""",
        (query,),
    ).fetchall()

    print(f"\n{total:,} phrases contiennent '{word}'. Les 5 plus courtes :\n")
    for fr, en in rows:
        print(f"  FR : {fr}\n  EN : {en}\n")


if __name__ == "__main__":
    main()
