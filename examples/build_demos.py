"""生成 examples/ 下的虚构行业 demo。

人物、学校、公司、数字全部虚构；岗位要求参考公开 JD（见各目录 sources.md）。
运行：python examples/build_demos.py
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
LABELS = {
    "internship": "实习经历",
    "project": "项目经历",
    "competition": "竞赛经历",
    "research": "科研经历",
    "campus": "校园经历",
}


def _kb(spec: dict) -> dict:
    return {
        "version": "0.1.0",
        "profile": {"name": spec["name"], "phone": "138-0000-0000", "email": "demo@example.com"},
        "experiences": spec["experiences"],
        "star_statements": spec["stars"],
        "abilities": spec["abilities"],
        "education": [spec["education"]],
        "honors": spec["honors"],
        "skills": spec["skills"],
    }


def _resume(spec: dict) -> dict:
    edu = spec["education"]
    honors = "；".join(f"{h['title']}（{h['detail']}）" if h.get("detail") else h["title"] for h in spec["honors"])
    sections = []
    for sec_title, exps in spec["resume"].items():
        sections.append(
            {
                "title": sec_title,
                "experiences": [{"experience_id": eid, "bullets": bullets} for eid, bullets in exps],
            }
        )
    return {
        "header": {"job_title": spec["job"]["title"], "availability": spec["job"]["availability"]},
        "education": {
            "schools": [
                {
                    "start": edu["start_date"],
                    "end": edu.get("end_date", ""),
                    "school": edu["school"],
                    "college": edu["major"],
                    "degree": edu["degree"],
                    "note": edu.get("note", ""),
                }
            ],
            "fields": [
                {"label": "专业成绩", "text": f"GPA {edu['gpa']}/{edu['gpa_scale']}，{edu['rank']}"},
                {"label": "主修课程", "text": "、".join(f"{c['name']}（{c['grade']}）" for c in edu["courses"])},
                {"label": "荣誉奖项", "text": honors},
            ],
        },
        "sections": sections,
        "abilities": spec["profile_blocks"],
    }


def _task(spec: dict, resume: dict) -> dict:
    rid = spec["id"] + "-render"
    matches = []
    for m in spec["job"]["matches"]:
        matches.append(
            {
                "requirement": m["requirement"],
                "ability_id": m["ability_id"],
                "ability_label": m["ability_label"],
                "star_statement_ids": m["star_statement_ids"],
                "match_level": m["match_level"],
                "reason": m["reason"],
            }
        )
    return {
        "id": rid,
        "job_title": spec["job"]["title"],
        "company": spec["job"]["company"],
        "availability": spec["job"]["availability"],
        "jd_text": spec["job"]["jd"],
        "requirements": [{"requirement": m["requirement"], "category": "必备"} for m in spec["job"]["matches"]],
        "matches": matches,
        "selected_experience_ids": [e["id"] for e in spec["experiences"]],
        "experience_rank": [{"experience_id": e["id"], "rank": i + 1} for i, e in enumerate(spec["experiences"])],
        "gaps": [],
        "preferences": {},
        "status": "draft",
        "versions": [
            {
                "version": 1,
                "created_at": "2026-01-01T00:00:00+08:00",
                "changes": "demo",
                "resume_json": resume,
                "analysis_md": f"# {spec['job']['title']} · demo\n",
            }
        ],
        "created_at": "2026-01-01T00:00:00+08:00",
        "updated_at": "2026-01-01T00:00:00+08:00",
    }


def write_demo(spec: dict) -> None:
    base = EXAMPLES / f"demo-{spec['id']}" / "data"
    (base / "knowledge_base").mkdir(parents=True, exist_ok=True)
    (base / "jobs").mkdir(parents=True, exist_ok=True)

    (base / "knowledge_base" / "knowledge_base.json").write_text(
        json.dumps(_kb(spec), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (base / "profile_blocks.yaml").write_text(
        yaml.safe_dump({"abilities": spec["profile_blocks"]}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (base / "preferences.json").write_text(
        json.dumps({"version": "0.1.0", "description": "demo", "rules": ["课程只展示与岗位相关的"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    resume = _resume(spec)
    task = _task(spec, resume)
    (base / "jobs" / f"{task['id']}.json").write_text(
        json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    out = EXAMPLES / f"demo-{spec['id']}"
    (out / "jd.md").write_text(spec["job"]["jd"], encoding="utf-8")
    (out / "sources.md").write_text(spec["sources"], encoding="utf-8")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    from demo_specs import SPECS

    for s in SPECS:
        write_demo(s)
