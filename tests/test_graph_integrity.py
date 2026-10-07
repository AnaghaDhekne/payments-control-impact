from scripts.validate_graph import validate

def test_hidden_graph_is_structurally_valid():
    result = validate()
    assert result["valid"], result["errors"]
    assert result["control_count"] >= 10
    assert result["key_control_count"] >= 5
