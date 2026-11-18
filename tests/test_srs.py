import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from srs import MIN_EASE, START_EASE, next_state  # noqa: E402

TODAY = date(2026, 11, 18)


def test_successful_reviews_grow_interval():
    reps, ease, interval = 0, START_EASE, 0
    seen = []
    for _ in range(3):
        reps, ease, interval, _due = next_state(reps, ease, interval, 5, TODAY)
        seen.append(interval)
    assert seen == [1, 6, 16]


def test_failure_resets_and_keeps_ease():
    reps, ease, interval, due = next_state(3, 2.5, 16, 1, TODAY)
    assert (reps, interval, due) == (0, 0, TODAY)
    assert ease == pytest.approx(2.5)


def test_ease_never_below_floor():
    reps, ease, interval = 0, START_EASE, 0
    for _ in range(30):
        reps, ease, interval, _due = next_state(reps, ease, interval, 3, TODAY)
    assert ease == pytest.approx(MIN_EASE)


def test_invalid_quality_rejected():
    with pytest.raises(ValueError):
        next_state(0, 2.5, 0, 6, TODAY)
    with pytest.raises(ValueError):
        next_state(0, 2.5, 0, -1, TODAY)


def test_due_date_matches_interval():
    _reps, _ease, interval, due = next_state(1, 2.5, 1, 4, TODAY)
    assert interval == 6
    assert due == TODAY + timedelta(days=interval)
