import re
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
    c = sqlite3.connect(str(DB))
    yield c
    c.close()


def test_excerpts_loaded(con):
    assert con.execute("SELECT count(*) FROM excerpts").fetchone()[0] >= 50


def test_every_excerpt_has_valid_timing_and_text(con):
    bad = con.execute(
        "SELECT count(*) FROM excerpts WHERE end_ms <= start_ms "
        "OR trim(fr_text) = '' OR trim(en_text) = ''"
    ).fetchone()[0]
    assert bad == 0


def test_french_word_finds_scenes():
    data = client.get("/excerpts", params={"word": "peur", "lang": "fr"}).json()
    assert data["total"] >= 2
    assert all(x["end_ms"] > x["start_ms"] for x in data["excerpts"])
    assert data["credits"]


def test_excerpts_are_not_repeated():
    data = client.get("/excerpts", params={"word": "espace", "lang": "fr", "limit": 10}).json()
    keys = [re.sub(r"[^\w]+", " ", x["fr"].lower()).strip() for x in data["excerpts"]]
    assert len(keys) == len(set(keys))


def test_unknown_word_returns_nothing():
    data = client.get("/excerpts", params={"word": "zzzqqqxx", "lang": "fr"}).json()
    assert data["excerpts"] == []


def test_bad_language_is_rejected():
    assert client.get("/excerpts", params={"word": "peur", "lang": "xx"}).status_code == 400
