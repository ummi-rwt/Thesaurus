import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
DB = ROOT / "data" / "thesaurus.db"

from api import app  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module")
def con():
    assert DB.exists(), "base introuvable : lancer load_db.py puis load_wiktionary.py"
    c = sqlite3.connect(str(DB))
    yield c
    c.close()


def scalar(con, sql, params=()):
    return con.execute(sql, params).fetchone()[0]


# ---------- Phrases (Tatoeba) ----------

def test_enough_pairs(con):
    assert scalar(con, "SELECT count(*) FROM pairs") > 400_000


def test_no_empty_text(con):
    sql = "SELECT count(*) FROM pairs WHERE trim(fr_text) = '' OR trim(en_text) = ''"
    assert scalar(con, sql) == 0


def test_no_duplicate_pairs(con):
    sql = ("SELECT count(*) FROM (SELECT 1 FROM pairs "
           "GROUP BY fr_text, en_text HAVING count(*) > 1)")
    assert scalar(con, sql) == 0


def test_no_narrow_nbsp(con):
    sql = "SELECT count(*) FROM pairs WHERE fr_text LIKE '%' || char(8239) || '%'"
    assert scalar(con, sql) == 0


def test_text_length_limit(con):
    sql = "SELECT max(max(length(fr_text)), max(length(en_text))) FROM pairs"
    assert scalar(con, sql) <= 300


def test_lemmas_mostly_filled(con):
    total = scalar(con, "SELECT count(*) FROM pairs")
    empty = scalar(con, "SELECT count(*) FROM pairs WHERE trim(fr_lemmas) = '' OR trim(en_lemmas) = ''")
    assert empty / total < 0.01


def test_search_index_works(con):
    sql = "SELECT count(*) FROM pairs_fts WHERE pairs_fts MATCH ?"
    assert scalar(con, sql, ('{fr_text fr_lemmas} : "manger"',)) > 1000


# ---------- Dictionnaire (Wiktionary) ----------

def test_every_word_has_a_translation(con):
    sql = ("SELECT count(*) FROM words w WHERE NOT EXISTS "
           "(SELECT 1 FROM translations t WHERE t.word_id = w.id)")
    assert scalar(con, sql) == 0


def test_no_duplicate_glosses_per_word(con):
    sql = ("SELECT count(*) FROM (SELECT 1 FROM translations "
           "GROUP BY word_id, gloss HAVING count(*) > 1)")
    assert scalar(con, sql) == 0


def test_forms_have_a_lemma(con):
    sql = "SELECT count(*) FROM forms WHERE trim(form) = '' OR trim(lemma) = ''"
    assert scalar(con, sql) == 0


def test_frequency_is_sensible(con):
    manger = scalar(con, "SELECT n FROM word_freq WHERE word = 'manger'")
    bouffer = scalar(con, "SELECT n FROM word_freq WHERE word = 'bouffer'")
    assert manger > 1000
    assert manger > bouffer > 0


# ---------- API ----------

def test_form_resolves_to_lemma():
    data = client.get("/lookup", params={"word": "mangeons", "lang": "fr"}).json()
    assert data["entries"][0]["word"] == "manger"
    assert all(e["pos"] == "verb" for e in data["entries"])


def test_english_lookup_puts_common_word_first():
    data = client.get("/lookup", params={"word": "eat", "lang": "en"}).json()
    assert data["translations"][0]["word"] == "manger"


def test_blank_word_is_rejected():
    assert client.get("/lookup", params={"word": "   "}).status_code == 400


def test_bad_language_is_rejected():
    assert client.get("/lookup", params={"word": "chat", "lang": "xx"}).status_code == 400
