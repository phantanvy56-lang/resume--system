from resume_system.config import load_categories, load_style


def test_style_has_defaults():
    style = load_style()
    assert style["sizes"]["body"] == 12
    assert style["fonts"]["header"]
    assert style["tabs"]["center_cm"] < style["tabs"]["right_cm"]


def test_categories_include_project_and_order():
    cats = load_categories()
    ids = [c["id"] for c in cats]
    assert "internship" in ids and "project" in ids
    orders = [c["order"] for c in cats]
    assert orders == sorted(orders)
