import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
VIDEO = ROOT / "data" / "video" / "tears_of_steel_720p.mov"

from api import app  # noqa: E402

client = TestClient(app)


def test_unknown_film_is_404():
    assert client.get("/video/inconnu").status_code == 404


@pytest.mark.skipif(not VIDEO.exists(), reason="video non telechargee")
def test_video_supports_range_requests():
    r = client.get("/video/tears-of-steel", headers={"Range": "bytes=0-99"})
    assert r.status_code == 206
    assert len(r.content) == 100
    assert r.headers["content-range"].startswith("bytes 0-99/")
