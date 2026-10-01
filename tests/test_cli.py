from __future__ import annotations

import csv

from sky_sql import cli
from sky_sql.__main__ import main as entry_main


def feed(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(it))


def test_flight_by_id_retries_until_valid(repo, monkeypatch, capsys):
    feed(monkeypatch, "abc", "1")
    flights = cli.flight_by_id(repo)
    assert [f.flight_id for f in flights] == [1]
    assert "Try again" in capsys.readouterr().out


def test_airport_prompt_rejects_bad_codes(repo, monkeypatch):
    feed(monkeypatch, "LA", "sfo")
    assert [f.flight_id for f in cli.delayed_flights_by_airport(repo)] == [4]


def test_print_results(capsys):
    from sky_sql.repository import Flight

    cli.print_results([Flight(1, "X", "A", "B", 5), Flight(2, "Y", "C", "D", 0)])
    out = capsys.readouterr().out
    assert "1. A -> B by X, Delay: 5 Minutes" in out
    assert "2. C -> D by Y\n" in out


def test_full_session_with_export(repo, monkeypatch, tmp_path, capsys):
    target = tmp_path / "out.csv"
    feed(monkeypatch, "2", "01/01/2015", "y", str(target), "5")
    assert cli.main(repo) == 0
    rows = list(csv.reader(target.open()))
    assert len(rows) == 3
    assert "Got 2 results." in capsys.readouterr().out


def test_version_flag(capsys):
    try:
        entry_main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "sky-sql" in capsys.readouterr().out
