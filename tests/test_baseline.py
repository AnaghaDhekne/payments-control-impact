from scripts.baseline import rank_controls
from scripts.evaluate_baseline import evaluate_condition
from scripts.generate_benchmark import build_graph,build_changes
from scripts.generate_observable import build_condition

def _case(change_id,level=0,mode="random"):
    g=build_graph(); cs=build_changes()
    p=build_condition(g,cs,level,mode)
    return next(x for x in p["cases"] if x["change_id"]==change_id)

def test_baseline_has_no_ground_truth_fields():
    ranked=rank_controls(_case("CHG-001"))
    assert ranked
    forbidden={"affected","actions","rule_ids","supporting_paths"}
    for row in ranked: assert not(forbidden & set(row))

def test_ranking_is_distance_then_criticality_then_id():
    ranked=rank_controls(_case("CHG-001"))
    keys=[(x["distance"],0 if x["criticality"]=="KEY" else 1,x["control_id"]) for x in ranked]
    assert keys==sorted(keys)

def test_zero_degradation_reaches_all_key_controls_for_seeded_metadata():
    r=evaluate_condition(0,"random")
    assert r["key_control_recall"]==1.0
    assert r["unreachable_key_control_pairs"]==0

def test_correlated_degradation_can_reduce_reachability():
    r0=evaluate_condition(0,"correlated")
    r60=evaluate_condition(60,"correlated")
    assert r60["reachable_key_control_pairs"] <= r0["reachable_key_control_pairs"]
