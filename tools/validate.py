#!/usr/bin/env python3
"""统一校验：schema + 交叉引用 + 任务正文结构。

用法：python tools/validate.py
改完 data/ 里任何文件都应该跑这一条（替代原来的 validate_kb / validate_jobs 两条）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from resume_system.config import DATA_DIR, load_categories

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = DATA_DIR / "knowledge_base" / "knowledge_base.json"
KB_SCHEMA = ROOT / "schemas" / "knowledge_base.schema.json"
JOBS_DIR = DATA_DIR / "jobs"
JOB_SCHEMA = ROOT / "schemas" / "job_task.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_kb() -> list[str]:
    errors: list[str] = []
    kb = _load(KB_PATH)
    schema = _load(KB_SCHEMA)

    try:
        jsonschema_validate(kb, schema)
    except ValidationError as e:
        location = "/".join(str(p) for p in e.absolute_path) or "(根)"
        return [f"知识库 schema 校验失败：{e.message} @{location}"]

    experience_ids = {e.get("id") for e in kb.get("experiences", [])}
    category_ids = {c.get("id") for c in load_categories()}
    for e in kb.get("experiences", []):
        if e.get("category") not in category_ids:
            errors.append(f"经历「{e.get('title')}」的 category「{e.get('category')}」不在 config/categories.yaml 里")
    star_ids = {s.get("id") for s in kb.get("star_statements", [])}

    for s in kb.get("star_statements", []):
        eid = s.get("experience_id")
        if eid and eid not in experience_ids:
            errors.append(f"STAR {s.get('id')} 指向不存在的经历 {eid}")

    for a in kb.get("abilities", []):
        for ref in a.get("star_statement_refs", []):
            if ref not in star_ids:
                errors.append(f"能力「{a.get('label')}」指向不存在的 STAR {ref}")

    # —— 数据一致性 ——
    # id 唯一
    exp_list = [e.get("id") for e in kb.get("experiences", [])]
    if len(exp_list) != len(set(exp_list)):
        errors.append("experiences 的 id 有重复")
    star_list = [s.get("id") for s in kb.get("star_statements", [])]
    if len(star_list) != len(set(star_list)):
        errors.append("star_statements 的 id 有重复")
    ab_list = [a.get("id") for a in kb.get("abilities", [])]
    if len(ab_list) != len(set(ab_list)):
        errors.append("abilities 的 id 有重复")

    # 日期格式（YYYY-MM）
    for e in kb.get("experiences", []):
        for k in ("start_date", "end_date"):
            v = e.get(k)
            if v and not re.match(r"^\d{4}-\d{2}$", str(v)):
                errors.append(f"经历「{e.get('title')}」的 {k}「{v}」不是 YYYY-MM 格式")

    # GPA 范围
    for ed in kb.get("education", []):
        gpa = ed.get("gpa")
        if gpa is not None:
            scale = ed.get("gpa_scale") or 5
            if not (0 <= gpa <= scale):
                errors.append(f"教育「{ed.get('school')}」的 GPA {gpa} 超出 0–{scale} 范围")

    orphan = [s.get("id") for s in kb.get("star_statements", []) if not s.get("experience_id")]
    if orphan:
        print(f"[提示] {len(orphan)} 条 STAR 未挂到任何经历（不会进正文板块）：{', '.join(x[:8] for x in orphan)}")

    print(
        f"[OK] 知识库：{len(kb.get('experiences', []))} 条经历，"
        f"{len(star_ids)} 条 STAR，{len(kb.get('abilities', []))} 项能力"
    )
    return errors


def check_jobs() -> list[str]:
    errors: list[str] = []
    if not JOBS_DIR.exists():
        return errors

    kb = _load(KB_PATH)
    experience_ids = {e.get("id") for e in kb.get("experiences", [])}
    star_ids = {s.get("id") for s in kb.get("star_statements", [])}
    ability_ids = {a.get("id") for a in kb.get("abilities", [])}

    schema = _load(JOB_SCHEMA)
    resume_schema = _load(ROOT / "schemas" / "resume.schema.json")
    files = sorted(JOBS_DIR.glob("*.json"))
    for p in files:
        try:
            task = _load(p)
            jsonschema_validate(task, schema)
        except (json.JSONDecodeError, ValidationError) as e:
            location = "/".join(str(x) for x in getattr(e, "absolute_path", []) or []) or "根"
            errors.append(f"{p.name}: {getattr(e, 'message', str(e))} @{location}")
            continue

        for eid in task.get("selected_experience_ids", []):
            if eid not in experience_ids:
                errors.append(f"{p.name}: selected_experience_ids 含未知经历 {eid}")
        for m in task.get("matches", []):
            if m.get("ability_id") and m["ability_id"] not in ability_ids:
                errors.append(f"{p.name}: match 指向未知能力 {m['ability_id']}")
            for sid in m.get("star_statement_ids", []):
                if sid not in star_ids:
                    errors.append(f"{p.name}: match 指向未知 STAR {sid}")

        for v in task.get("versions", [])[-1:]:
            if "resume_json" not in v:
                continue
            try:
                jsonschema_validate(v["resume_json"], resume_schema)
            except ValidationError as e:
                location = "/".join(str(x) for x in e.absolute_path) or "根"
                errors.append(f"{p.name} v{v.get('version')}: resume_json {e.message} @{location}")
                continue
            labels = {c.get("id"): c.get("label") for c in load_categories()}
            cats = {e.get("id"): e.get("category") for e in kb.get("experiences", [])}
            for sec in v["resume_json"].get("sections", []):
                for exp in sec.get("experiences", []):
                    expected = labels.get(cats.get(exp.get("experience_id")))
                    if expected and sec.get("title") != expected:
                        errors.append(
                            f"{p.name} v{v.get('version')}: 经历 {exp.get('experience_id')} 应放在「{expected}」，现在在「{sec.get('title')}」"
                        )
                    if exp.get("experience_id") not in experience_ids:
                        errors.append(
                            f"{p.name} v{v.get('version')}: resume 引用未知经历 {exp.get('experience_id')}"
                        )
                    for b in exp.get("bullets", []):
                        for term in b.get("bold", []):
                            if term and term not in b.get("desc", ""):
                                errors.append(
                                    f"{p.name} v{v.get('version')}: bold「{term}」不在 desc 里"
                                )

    print(f"[OK] 任务：{len(files)} 份，全部通过 schema 与引用检查")
    return errors


def main() -> int:
    errors = check_kb() + check_jobs()
    if errors:
        print()
        for e in errors:
            print(f"[FAIL] {e}")
        print(f"\n共 {len(errors)} 处问题")
        return 1
    print("\n全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
