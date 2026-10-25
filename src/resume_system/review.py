"""简历字条自检：检查同一段经历内的字条是否能力/措辞重合。

只做确定性检查，不调用模型：
- 同一经历里两条字条的维度标签完全相同
- 两条字条的描述句有较长的相同片段（≥ 8 个汉字）
- 两条字条的字符二元组重合度 ≥ 0.35
- 两条字条的价值收尾句相同（末尾 8 个字）

用法：
    from resume_system.review import review_resume
    warnings = review_resume(resume_text)

或命令行：
    python -m resume_system.review --task <任务id>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BULLET_RE = re.compile(r"^\s*[-*]?\s*\*\*(.+?)\*\*\s*[：:]\s*(.+)$")
PROJECT_RE = re.compile(r"^\s*\d{4}[.\-/年]\d{1,2}.*｜")
HEADING_RE = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
PUNCT_RE = re.compile(r"[\s\*，。；：、,.;:（）()「」『』/“”\"'—\-–·…]")

MIN_LCS = 8          # 两条字条共有的连续汉字数达到这个值就提示
MIN_JACCARD = 0.35   # 字符二元组重合度阈值
TAIL_LEN = 8         # 价值收尾比对长度


def _norm(s: str) -> str:
    return PUNCT_RE.sub("", s)


def _lcs_len(a: str, b: str) -> int:
    """最长公共子串长度（汉字串，短字符串够用）。"""
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best



def _lcs_str(a: str, b: str) -> str:
    """最长公共子串（返回内容，用于提示具体重复片段）。"""
    if not a or not b:
        return ""
    best_len = 0
    best_end = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best_len:
                    best_len = cur[j]
                    best_end = i
        prev = cur
    return a[best_end - best_len : best_end]


def _bigrams(s: str) -> set[str]:
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _jaccard(a: str, b: str) -> float:
    A, B = _bigrams(a), _bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def _parse(text: str) -> list[dict]:
    """把简历正文解析成 [{section, project, bullets:[{label, desc}]}]。"""
    experiences: list[dict] = []
    section = ""
    current = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = HEADING_RE.match(line)
        if m:
            section = m.group(1).strip()
            current = None
            continue
        if PROJECT_RE.match(line):
            if "教育" in section:  # 教育背景行也是「时间｜学校｜专业」，不算经历
                current = None
                continue
            current = {"section": section, "project": line.strip(), "bullets": []}
            experiences.append(current)
            continue
        m = BULLET_RE.match(line)
        if m and current is not None:
            current["bullets"].append({"label": m.group(1).strip(), "desc": m.group(2).strip()})
    return experiences


def _issues_for_bullets(project: str, bullets: list[dict], seen_labels: dict[str, str]) -> list[dict]:
    issues: list[dict] = []

    for b in bullets:
        key = b["label"]
        if key in seen_labels and seen_labels[key] != project:
            issues.append(
                {
                    "kind": "标签重复",
                    "project": project,
                    "a": key,
                    "b": key,
                    "a_desc": b["desc"],
                    "b_desc": "",
                    "detail": f"与「{seen_labels[key]}」里的同名标签重复",
                }
            )
        else:
            seen_labels.setdefault(key, project)

    for i in range(len(bullets)):
        for j in range(i + 1, len(bullets)):
            a, b = bullets[i], bullets[j]
            na, nb = _norm(a["desc"]), _norm(b["desc"])
            base = {
                "project": project,
                "a": a["label"],
                "b": b["label"],
                "a_desc": a["desc"],
                "b_desc": b["desc"],
                "index_a": i + 1,
                "index_b": j + 1,
            }

            if a["label"] == b["label"]:
                issues.append({**base, "kind": "标签重复", "detail": "同一段经历里维度标签相同"})
                continue

            lcs = _lcs_len(na, nb)
            if lcs >= MIN_LCS:
                issues.append({**base, "kind": "措辞重合", "detail": f"{lcs} 字连续相同"})
                continue

            jac = _jaccard(na, nb)
            if jac >= MIN_JACCARD:
                issues.append({**base, "kind": "内容重合", "detail": f"字符重合度 {jac:.0%}"})
                continue

            if na[-TAIL_LEN:] == nb[-TAIL_LEN:]:
                issues.append({**base, "kind": "收尾重复", "detail": f"价值收尾相同：…{na[-TAIL_LEN:]}"})

    return issues


def find_overlaps(text: str) -> list[dict]:
    """从 markdown 正文里找重合（旧任务 / 兼容用）。"""
    issues: list[dict] = []
    seen_labels: dict[str, str] = {}
    for exp in _parse(text):
        issues.extend(_issues_for_bullets(exp["project"], exp["bullets"], seen_labels))
    return issues


def find_overlaps_resume(resume: dict) -> list[dict]:
    """从结构化正文里找重合（新链路）。"""
    issues: list[dict] = []
    seen_labels: dict[str, str] = {}
    for sec in resume.get("sections", []):
        for exp in sec.get("experiences", []):
            eid = exp.get("experience_id") or ""
            project = f"{sec.get('title', '')}｜{eid[:8] or '?'}"
            bullets = [
                {"label": b.get("label", ""), "desc": b.get("desc", "")}
                for b in exp.get("bullets", [])
            ]
            issues.extend(_issues_for_bullets(project, bullets, seen_labels))
    return issues


def format_issue(issue: dict) -> str:
    """把一条问题格式化成给人看的一行块。"""
    kind = issue["kind"]
    project = issue["project"]
    if issue["a"] == issue["b"]:
        return f"[{kind}] {project}\n  维度标签重复：{issue['a']}"
    return (
        f"[{kind}] {project}\n"
        f"  第 {issue.get('index_a', '?')}「{issue['a']}」与第 {issue.get('index_b', '?')}「{issue['b']}」：{issue['detail']}\n"
        f"  → 这两条大概率在说同一个能力点，删一条或换维度"
    )


def review_resume(text: str) -> list[str]:
    """返回问题列表（空列表 = 没查出重合）。"""
    return [format_issue(i) for i in find_overlaps(text)]


def _latest_task() -> dict:
    from .config import DATA_DIR
    jobs = sorted((DATA_DIR / "jobs").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jobs:
        raise FileNotFoundError("data/jobs 下没有任务")
    return json.loads(jobs[0].read_text(encoding="utf-8"))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="检查简历字条是否重合（不调用模型）")
    parser.add_argument("--task", help="任务 id（默认最新任务）")
    args = parser.parse_args()

    if args.task:
        from .config import DATA_DIR
        path = DATA_DIR / "jobs" / f"{args.task}.json"
        task = json.loads(path.read_text(encoding="utf-8"))
    else:
        task = _latest_task()

    version = task["versions"][-1]
    if "resume_json" in version:
        problems = [format_issue(i) for i in find_overlaps_resume(version["resume_json"])]
    else:
        problems = review_resume(version.get("resume_text", ""))
    print(f"任务：{task['job_title']}（{task['id'][:8]}）")
    if not problems:
        print("未发现字条重合")
        return 0
    for p in problems:
        print(f"\n{p}")
    print(f"\n共 {len(problems)} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())

def _all_bullets(resume: dict) -> list[dict]:
    items = []
    for sec in resume.get("sections", []):
        for exp in sec.get("experiences", []):
            eid = exp.get("experience_id", "")
            project = f"{sec.get('title', '')}｜{eid[:8] or '?'}"
            for i, b in enumerate(exp.get("bullets", []), 1):
                items.append(
                    {
                        "project": project,
                        "experience_id": eid,
                        "index": i,
                        "label": b.get("label", ""),
                        "desc": b.get("desc", ""),
                    }
                )
    return items


def find_cross_overlaps(resume: dict, name_by_id: dict[str, str] | None = None) -> list[dict]:
    """跨经历查重：只报警，不自动合并。阈值比同段略宽。"""
    name_by_id = name_by_id or {}
    issues: list[dict] = []
    bullets = _all_bullets(resume)
    for i in range(len(bullets)):
        for j in range(i + 1, len(bullets)):
            a, b = bullets[i], bullets[j]
            if not a["experience_id"] or a["experience_id"] == b["experience_id"]:
                continue
            na, nb = _norm(a["desc"]), _norm(b["desc"])
            common = _lcs_str(na, nb)
            jac = _jaccard(na, nb)
            if len(common) < 10 and jac < 0.5:
                continue
            pa = name_by_id.get(a["experience_id"], a["project"])
            pb = name_by_id.get(b["experience_id"], b["project"])
            detail = f"共同片段「{common}」" if len(common) >= 10 else f"字符重合度 {jac:.0%}"
            issues.append(
                {
                    "scope": "cross",
                    "kind": "跨经历重合",
                    "project_a": pa,
                    "project_b": pb,
                    "a": a["label"],
                    "b": b["label"],
                    "a_desc": a["desc"],
                    "b_desc": b["desc"],
                    "index_a": a["index"],
                    "index_b": b["index"],
                    "detail": detail,
                }
            )
    return issues
