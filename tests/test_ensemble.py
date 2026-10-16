from scripts.ensemble import agreement, combine


def result(rec, unc, base=("B1",), undecided=()):
    return {
        "change_id": "CHG-X",
        "baseline": [{"control_id": b} for b in base],
        "recommended_control_ids": sorted(set(base) | set(rec)),
        "uncertain_control_ids": sorted(unc),
        "uninvestigated_control_ids": sorted(undecided),
        "findings": [{"control_id": c} for c in set(rec) | set(unc)],
        "trace": [{}],
    }


def test_majority_vote_recommends_reviews_and_drops():
    runs = [
        result(["C1", "C2"], ["C3"]),
        result(["C1"], ["C2", "C4"]),
        result(["C1", "C5"], ["C3"]),
    ]
    out = combine(runs)
    assert out["recommended_control_ids"] == ["B1", "C1"]  # C1 in 3 of 3
    # C2: AFFECTED once + UNCERTAIN once = flagged twice -> review
    # C3: UNCERTAIN twice -> review; C4, C5 flagged once -> dropped
    assert out["uncertain_control_ids"] == ["C2", "C3"]
    assert [q["control_id"] for q in out["ranked_review_queue"]] == ["C2", "C3"]
    assert len(out["trace"]) == 3


def test_agreement_counts_pairs_with_identical_decisions():
    a = {"CHG-X": {"K1": "REC", "K2": "NOT"}}
    b = {"CHG-X": {"K1": "REC", "K2": "REC"}}
    assert agreement([a, b]) == {"key_pairs": 2, "agreement": 0.5}
    assert agreement([a, a])["agreement"] == 1.0
