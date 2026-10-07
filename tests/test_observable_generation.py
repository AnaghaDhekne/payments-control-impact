from scripts.generate_observable import build_condition, degrade_edges
from scripts.generate_benchmark import build_graph, build_changes

def test_six_conditions_are_deterministic():
    g=build_graph(); cs=build_changes()
    for level in (0,30,60):
        for mode in ("random","correlated"):
            a=build_condition(g,cs,level,mode)
            b=build_condition(g,cs,level,mode)
            assert a==b
            assert len(a["cases"])==54

def test_zero_percent_removes_nothing():
    g=build_graph(); c=build_changes()[0]
    for mode in ("random","correlated"):
        visible,removed=degrade_edges(g,c,0,mode)
        assert removed==[]
        assert len(visible)==sum(e.get("metadata_exposable",True) for e in g["edges"])

def test_degradation_is_monotonic_in_count():
    g=build_graph(); c=build_changes()[0]
    for mode in ("random","correlated"):
        _,r30=degrade_edges(g,c,30,mode)
        _,r60=degrade_edges(g,c,60,mode)
        assert len(r60)>len(r30)>0

def test_correlated_damage_touches_changed_neighborhood():
    g=build_graph()
    c=next(x for x in build_changes() if x["changed_node_ids"]==["D03"])
    _,removed=degrade_edges(g,c,30,"correlated")
    incident={e["id"] for e in g["edges"] if "D03" in (e["source"],e["target"]) and e.get("metadata_exposable",True)}
    assert incident & set(removed)

def test_ground_truth_fields_are_not_embedded_in_observable_cases():
    g=build_graph(); cs=build_changes()
    payload=build_condition(g,cs,30,"correlated")
    forbidden={"affected","actions","supporting_paths","rule_ids"}
    def walk(x):
        if isinstance(x,dict):
            assert not (forbidden & set(x))
            for v in x.values(): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(payload)
