from resume_system.checks import check_thresholds, collect_warnings


def _kb(degree="本科"):
    return {"experiences": [], "honors": [], "education": [{"school": "示例大学", "degree": degree}]}


def _jd(text):
    return {"requirements": [{"id": "R1", "kind": "门槛", "text": text, "source_span": text}]}


def test_degree_unmet():
    r = check_thresholds(_jd("硕士及以上学历"), _kb("本科"), {})
    assert r[0]["status"] == "不满足"


def test_school_tier_unknown():
    r = check_thresholds(_jd("985/211 或 QS 前 100，本科及以上"), _kb("硕士"), {})
    assert r[0]["status"] == "未知"
    assert "院校层次" in r[0]["reason"]


def test_duration_satisfied():
    task = {"availability": "每周到岗 4 天，可连续实习 3 个月以上"}
    r = check_thresholds(_jd("每周4天，实习3个月"), _kb(), task)
    assert r[0]["status"] == "满足"


def test_p1_uncovered_warning():
    jd = {
        "requirements": [
            {"id": "R1", "kind": "能力", "priority": "P1", "text": "数据分析", "ability_id": "data_analysis"}
        ]
    }
    kb = {"experiences": [], "honors": [], "education": []}
    resume = {
        "education": {"schools": [], "fields": [{"label": "荣誉奖项", "text": "示例"}]},
        "sections": [],
        "abilities": [],
    }
    warnings = collect_warnings(resume, kb, {"jd_analysis": jd, "matches": [], "gaps": []})
    assert any(w["type"] == "p1_uncovered" for w in warnings)
