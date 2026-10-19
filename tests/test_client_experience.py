"""Regression checks for the client-facing product, independent of Streamlit runtime."""
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"
PRODUCT = ROOT / "app" / "client_experience.py"

def test_app_is_valid_python():
    ast.parse(APP.read_text(encoding="utf-8"))
    ast.parse(PRODUCT.read_text(encoding="utf-8"))

def test_client_pages_use_one_product():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for page in ("page_overview", "page_case", "page_results", "page_decision"):
        assert page in funcs
        source = ast.get_source_segment(APP.read_text(encoding="utf-8"), funcs[page])
        assert "client_product(" in source
    assert "page_case_detail" in funcs
    assert "page_synthetic" in funcs
    assert "page_evidence" in funcs

def test_four_interactive_rooms():
    source = PRODUCT.read_text(encoding="utf-8")
    for room in ("investigate", "evaluate", "decide", "method"):
        assert f'id="scene-{room}"' in source
        assert f'data-view="{room}"' in source
    for question in ("coverage", "review", "miss", "repeat"):
        assert f'data-question="{question}"' in source
    for gate in range(3):
        assert f'data-gate="{gate}"' in source
    assert 'render(\'broken\')' in source
    assert 'openScene(\'__INITIAL__\')' in source
    assert 'aria-live="polite"' in source
    assert 'prefers-reduced-motion' in source

def test_recorded_evidence_not_fabricated():
    source = PRODUCT.read_text(encoding="utf-8")
    assert 'bool(control)' in source
    assert 'Recorded ticket quote unavailable' in source
    assert 'Recorded procedure quote unavailable' in source
    assert 'human review' in source.lower()
    assert 'one affected key control' in source.lower()
    assert '262 / 280' in source
    assert '331' in source and '75' in source

def test_no_accidental_duplicate_function_names():
    tree = ast.parse(APP.read_text(encoding="utf-8"))
    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    assert len(names) == len(set(names))
