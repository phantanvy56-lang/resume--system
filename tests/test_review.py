from resume_system.review import find_cross_overlaps, find_overlaps_resume


def _resume(bullets_a, bullets_b=None):
    sections = [{"title": "实习经历", "experiences": [{"experience_id": "e1", "bullets": bullets_a}]}]
    if bullets_b:
        sections.append({"title": "竞赛经历", "experiences": [{"experience_id": "e2", "bullets": bullets_b}]})
    return {"sections": sections}


def test_within_experience_overlap():
    resume = _resume([
        {"label": "数据核对", "desc": "比对订单轨迹与申报信息的一致性并统计基础报表"},
        {"label": "单据核对", "desc": "比对订单轨迹与申报信息的一致性并记录差异"},
    ])
    assert find_overlaps_resume(resume)


def test_cross_experience_overlap():
    text = "负责校园招聘宣讲会的全流程策划执行并完成复盘报告"
    resume = _resume(
        [{"label": "活动统筹", "desc": text}],
        [{"label": "活动执行", "desc": text}],
    )
    assert not find_overlaps_resume(resume)  # 不同经历，不算同段重合
    issues = find_cross_overlaps(resume)
    assert issues and "共同片段" in issues[0]["detail"]
