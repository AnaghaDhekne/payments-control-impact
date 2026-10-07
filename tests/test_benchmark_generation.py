from scripts.generate_benchmark import build_graph, build_changes
from scripts.ground_truth import Change, label_change

def test_benchmark_scale_and_reproducibility():
    a,b=build_graph(),build_graph()
    ca,cb=build_changes(),build_changes()
    assert a==b
    assert ca==cb
    controls=[n for n in a["nodes"] if n["type"]=="CONTROL"]
    assert 80 <= len(controls) <= 150
    assert 50 <= len(ca) <= 60
    assert len({c["change_id"] for c in ca})==len(ca)

def test_held_out_has_at_least_40_affected_key_control_pairs():
    graph=build_graph()
    changes=[c for c in build_changes() if c["split"]=="test"]
    count=0
    for c in changes:
        change=Change(
          c["change_id"],tuple(c["changed_node_ids"]),c["change_type"],
          c["implementation_date"],c["material"],c.get("rollback_date")
        )
        labels=label_change(graph,change,test_period_start="2026-10-01",test_period_end="2027-03-31")
        count += sum(x.affected and x.criticality=="KEY" for x in labels)
    assert count >= 40, f"only {count} affected held-out key-control pairs"

def test_every_change_has_a_known_changed_node():
    graph=build_graph()
    ids={n["id"] for n in graph["nodes"]}
    for c in build_changes():
        assert set(c["changed_node_ids"]) <= ids
