from resume_system.checks import collect_warnings


def test_missing_honor_and_section_mismatch():
    kb = {
        "experiences": [{"id": "e1", "category": "internship", "title": "某实习"}],
        "honors": [{"title": "文体之星"}],
        "education": [{"school": "示例大学"}],
    }
    resume = {
        "education": {"schools": [], "fields": []},
        "sections": [{"title": "项目经历", "experiences": [{"experience_id": "e1", "bullets": [{"label": "A", "desc": "做了某件事"}]}]}],
    }
    warnings = collect_warnings(resume, kb, {})
    types = {w["type"] for w in warnings}
    assert "honors_missing" in types
    assert "education_missing" in types
    assert "section_mismatch" in types
