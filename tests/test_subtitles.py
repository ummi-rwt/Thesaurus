import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from subtitles import parse_srt, read_srt  # noqa: E402

SAMPLE = """1
00:00:01,000 --> 00:00:03,500
<i>Tu viens manger ?</i>

2
00:00:04,000 --> 00:00:06,000
Oui, j'arrive.
Attends-moi !

3
00:00:07,000 --> 00:00:07,000
Duree nulle

4
00:01:02,250 --> 00:01:04,000
{\\an8}Bonne nuit.
"""


def test_parses_valid_cues_only():
    cues = parse_srt(SAMPLE)
    assert len(cues) == 3
    assert cues[0] == {"start_ms": 1000, "end_ms": 3500, "text": "Tu viens manger ?"}


def test_multiline_cue_is_joined():
    assert parse_srt(SAMPLE)[1]["text"] == "Oui, j'arrive. Attends-moi !"


def test_style_tags_are_removed():
    cues = parse_srt(SAMPLE)
    assert cues[2]["text"] == "Bonne nuit."
    assert cues[2]["start_ms"] == 62250


def test_bom_and_windows_newlines():
    messy = "\ufeff" + SAMPLE.replace("\n", "\r\n")
    assert parse_srt(messy) == parse_srt(SAMPLE)


def test_read_srt_falls_back_to_cp1252(tmp_path):
    content = "1\n00:00:01,000 --> 00:00:02,000\n\u00c9t\u00e9\n"
    path = tmp_path / "a.srt"
    path.write_bytes(content.encode("cp1252"))
    assert read_srt(path)[0]["text"] == "\u00c9t\u00e9"
