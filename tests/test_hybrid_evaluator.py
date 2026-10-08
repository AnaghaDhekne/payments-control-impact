import json
from scripts.evaluate_hybrid import evaluate_hybrid

def test_hybrid_evaluator_reports_preregistered_metrics():
    def empty_llm(_): return json.dumps({"recommendations":[]})
    out = evaluate_hybrid(empty_llm, runs=1, top_k=5)
    r = out["runs_detail"][0]
    assert out["level"] == 30 and out["mode"] == "correlated"
    assert r["baseline_key_misses"] > 0
    assert r["recovered_key_misses"] == 0
    assert r["key_miss_recovery_rate"] == 0
    assert r["workload_increase_rate"] == 0
    assert out["repeated_run_agreement"] == 1.0
