import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from resume_system.keyword_check import check_keyword_coverage


def test_keyword_coverage_missing():
    resume = {"education": {"fields": []}, "sections": [], "abilities": [], "skills": []}
    jd = "负责数据分析、竞品分析、市场调研"
    names = {m["name"] for m in check_keyword_coverage(resume, jd)}
    assert "数据分析" in names


def test_keyword_coverage_covered():
    resume = {
        "education": {"fields": []},
        "sections": [
            {"title": "实习", "experiences": [
                {"experience_id": "e1", "bullets": [{"label": "数据分析", "desc": "使用 Excel 做数据分析"}]}
            ]}
        ],
        "abilities": [],
        "skills": ["数据分析"],
    }
    jd = "负责数据分析、竞品分析"
    names = {m["name"] for m in check_keyword_coverage(resume, jd)}
    assert "数据分析" not in names


def test_validate_consistency_checks(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import validate

    kb = {
        "version": "0.1.0",
        "experiences": [
            {"id": "dup", "title": "A", "category": "internship", "facts": [], "verification_status": "verified", "source_refs": [], "start_date": "2025-13", "end_date": "bad-date"},
            {"id": "dup", "title": "B", "category": "internship", "facts": [], "verification_status": "verified", "source_refs": []},
        ],
        "star_statements": [],
        "abilities": [],
        "education": [{"school": "X", "major": "Y", "degree": "本科", "gpa": 99, "gpa_scale": 5}],
        "honors": [],
        "skills": [],
        "profile": {"name": "测试"},
    }
    p = tmp_path / "kb.json"
    p.write_text(json.dumps(kb, ensure_ascii=False), encoding="utf-8")
    old = validate.KB_PATH
    try:
        validate.KB_PATH = p
        errors = validate.check_kb()
    finally:
        validate.KB_PATH = old

    joined = "\n".join(errors)
    assert "id 有重复" in joined
    assert "YYYY-MM" in joined
    assert "GPA" in joined
