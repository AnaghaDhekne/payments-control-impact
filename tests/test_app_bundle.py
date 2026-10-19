"""The dashboard falls back to the bundled run files when the volume is absent."""

from app import data


def test_bundled_runs_load(monkeypatch, tmp_path):
    monkeypatch.setattr(data, "RESULTS_ROOT", str(tmp_path / "missing"))
    data.root_for.cache_clear()
    runs = {r["kind"]: r for r in data.available_runs()}
    assert len(runs["heldout"]["cases"]) == 18
    summary = runs["heldout"]["metrics"][0]["summary"]
    assert (summary["key_recovered"], summary["key_misses"]) == (113, 144)
    res = data.case_result("heldout-final", "run1", "CHG-015")
    rows = data.decisions_table(res)
    assert sum(r["outcome"].startswith("Sent to review") for r in rows) == 10
    assert data.step_rows(res)
    data.root_for.cache_clear()
