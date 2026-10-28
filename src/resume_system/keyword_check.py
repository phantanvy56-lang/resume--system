"""JD 关键词覆盖检查：JD 里出现的能力关键词，简历正文是否都覆盖到。零 key，不调模型。

用法：
    python -m resume_system.keyword_check --task <任务id>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .config import DATA_DIR, load_abilities

JOBS_DIR = DATA_DIR / "jobs"


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _resume_text(resume: dict) -> str:
    """把简历正文压成一段归一化纯文本（用于关键词匹配）。"""
    parts: list[str] = []
    for f in resume.get("education", {}).get("fields", []):
        parts += [f.get("label", ""), f.get("text", "")]
    for sec in resume.get("sections", []):
        for exp in sec.get("experiences", []):
            for b in exp.get("bullets", []):
                parts += [b.get("label", ""), b.get("desc", "")]
    for ab in resume.get("abilities", []):
        parts += [ab.get("label", ""), ab.get("text", "")]
    parts += list(resume.get("skills", []))
    return _norm(" ".join(x for x in parts if x))


def check_keyword_coverage(resume: dict, jd_text: str) -> list[dict]:
    """JD 提到（能力名或别名）、但简历正文没覆盖到的能力。返回 [{name, category}]。"""
    abilities = load_abilities()
    jd_norm = _norm(jd_text)
    resume_norm = _resume_text(resume)

    missing: list[dict] = []
    for ab in abilities:
        keywords = [k for k in [ab.get("name", "")] + list(ab.get("aliases", [])) if k]
        if not any(_norm(kw) in jd_norm for kw in keywords):
            continue  # JD 没提这个能力，跳过
        if not any(_norm(kw) in resume_norm for kw in keywords):
            missing.append({"name": ab.get("name", ""), "category": ab.get("category", "")})
    return missing


def _latest_task() -> dict:
    jobs = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jobs:
        raise FileNotFoundError("data/jobs 下没有任务")
    return json.loads(jobs[0].read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="JD 关键词覆盖检查（零 key，不调模型）")
    parser.add_argument("--task", help="任务 id（默认最新任务）")
    args = parser.parse_args()

    if args.task:
        path = JOBS_DIR / f"{args.task}.json"
        task = json.loads(path.read_text(encoding="utf-8"))
    else:
        task = _latest_task()

    version = task["versions"][-1]
    if "resume_json" not in version:
        print("该任务是旧格式（markdown），无 resume_json，跳过。", file=sys.stderr)
        return 1
    resume = version["resume_json"]
    jd_text = task.get("jd_text", "")

    missing = check_keyword_coverage(resume, jd_text)
    print(f"任务：{task.get('job_title', '')}（{task['id'][:8]}）")
    if not missing:
        print("JD 里的能力关键词都已覆盖到简历正文。")
        return 0
    print(f"\nJD 提到、但简历正文里没出现的能力（{len(missing)} 项）：")
    for m in missing:
        print(f"  - [{m['category']}] {m['name']}")
    print("\n提示：以上是「字面未出现」，可能用了同义表述；请人工确认是否真的缺证据。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
