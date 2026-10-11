import pytest
from scripts.export_case import export_case


def test_export_removes_evaluation_metadata():
    case = export_case("CHG-001")
    assert set(case) == {
        "change_id",
        "change_ticket",
        "visible_metadata",
        "control_documents",
    }
    assert case["change_id"] == "CHG-001"


def test_export_refuses_historical_test_case():
    with pytest.raises(ValueError, match="development"):
        export_case("CHG-003")
