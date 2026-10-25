"""发布前检查：把结构校验之外、需要人看一眼的问题收集成 warnings。"""
from __future__ import annotations

import re

from .review import find_cross_overlaps, find_overlaps_resume, format_issue

_HONOR_STOP = ("全国", "高校", "大学生", "竞赛", "大赛", "奖学金", "国家级", "省级", "校级", "比赛")


def _norm(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", text or "", flags=re.UNICODE)


def _honor_candidates(title: str) -> list[str]:
    t = re.sub(r"[（(].*?[）)]", "", title or "")
    t = _norm(t)
    for w in _HONOR_STOP:
        t = t.replace(w, "")
    out = [t, t[:6], t[:4]]
    return [x for x in out if len(x) >= 2]


def _honors_text(resume: dict) -> str:
    for f in resume.get("education", {}).get("fields", []):
        if "荣誉" in f.get("label", ""):
            return f.get("text", "")
    return ""


_DEGREE_RANK = {"本科": 1, "学士": 1, "硕士": 2, "研究生": 2, "博士": 3}


def _highest_degree(kb: dict) -> tuple[int, str]:
    best, label = 0, ""
    for ed in kb.get("education", []):
        degree = ed.get("degree", "")
        for name, rank in _DEGREE_RANK.items():
            if name in degree and rank > best:
                best, label = rank, degree
    return best, label


def check_thresholds(jd: dict, kb: dict, task: dict) -> list[dict]:
    """核对门槛类要求（学历 / 语言 / 院校层次），给满足/不满足/未知。"""
    results: list[dict] = []
    highest, highest_label = _highest_degree(kb)
    english = [
        f"{e.get('name', '')} {e.get('score', '')}".strip()
        for ed in kb.get("education", [])
        for e in ed.get("english", [])
    ]

    for r in jd.get("requirements", []):
        if r.get("kind") != "门槛":
            continue
        text = f"{r.get('text', '')} {r.get('source_span', '')}"
        status, reason = "未知", "知识库没有可核对的信息"

        need = max((rank for name, rank in _DEGREE_RANK.items() if name in text), default=0)
        if need:
            if highest >= need:
                status, reason = "满足", f"最高学历 {highest_label}"
            else:
                status, reason = "不满足", f"要求更高学历，当前最高 {highest_label or '未记录'}"
        elif "CET-6" in text or "六级" in text:
            hit = next((x for x in english if "CET-6" in x), "")
            if hit:
                status, reason = "满足", hit
            else:
                status, reason = "未知", "知识库没有 CET-6 成绩"
        elif "985" in text or "211" in text or "QS" in text:
            status, reason = "未知", "知识库没有院校层次信息"

        results.append(
            {
                "requirement_id": r.get("id", ""),
                "text": r.get("text", ""),
                "status": status,
                "reason": reason,
            }
        )
    return results


def collect_warnings(resume: dict, kb: dict, task: dict) -> list[dict]:
    """返回 [{type, severity, message}]；severity=error 时 --strict 会阻止导出。"""
    warnings: list[dict] = []

    # 1) 同一段经历内的字条重合（会自动回修，修完还剩才报）
    for it in find_overlaps_resume(resume):
        warnings.append(
            {
                "type": "overlap_within",
                "severity": "error",
                "message": format_issue(it).replace("\n", " "),
            }
        )

    # 2) 跨经历重合：只提示
    name_by_id = {e.get("id"): (e.get("title") or "").split("·")[0].strip() for e in kb.get("experiences", [])}
    for it in find_cross_overlaps(resume, name_by_id):
        warnings.append(
            {
                "type": "overlap_cross",
                "severity": "warn",
                "message": (
                    f"「{it['project_a']}」的「{it['a']}」与「{it['project_b']}」的「{it['b']}」"
                    f"{it['detail']}，确认是否在说同一件事"
                ),
            }
        )

    # 3) 荣誉是否列全
    text = _norm(_honors_text(resume))
    if not text:
        warnings.append(
            {"type": "honors_missing", "severity": "error", "message": "教育背景里没有「荣誉奖项」字段"}
        )
    else:
        excluded = set(task.get("exclude_honors") or [])
        for h in kb.get("honors", []):
            title = h.get("title", "")
            if title in excluded:
                continue
            if not any(c in text for c in _honor_candidates(title)):
                warnings.append(
                    {
                        "type": "honors_missing",
                        "severity": "error",
                        "message": f"荣誉奖项里没有找到「{title}」",
                    }
                )

    # 3.5) 板块标题必须与经历 category 对应
    from .config import load_categories
    label_by_cat = {c["id"]: c["label"] for c in load_categories()}
    exp_cat = {e.get("id"): e.get("category") for e in kb.get("experiences", [])}
    for sec in resume.get("sections", []):
        for exp in sec.get("experiences", []):
            cat = exp_cat.get(exp.get("experience_id"))
            expected = label_by_cat.get(cat)
            if expected and sec.get("title") != expected:
                warnings.append(
                    {
                        "type": "section_mismatch",
                        "severity": "error",
                        "message": f"经历「{exp.get('experience_id')}」是 {cat}，应放在「{expected}」，现在在「{sec.get('title')}」",
                    }
                )

    # 4) 教育经历是否漏写
    schools = {s.get("school", "") for s in resume.get("education", {}).get("schools", [])}
    for ed in kb.get("education", []):
        if ed.get("school") and ed["school"] not in schools:
            warnings.append(
                {
                    "type": "education_missing",
                    "severity": "error",
                    "message": f"教育背景里没有找到「{ed['school']}」",
                }
            )

    # 5) 如果任务里已有 JD 解析结果，检查 P0 覆盖
    jd = task.get("jd_analysis") or {}
    if jd.get("requirements"):
        matched_ids = {
            m.get("requirement_id")
            for m in task.get("matches", [])
            if m.get("match_level") in ("强", "中")
        }
        matched_abilities = {
            m.get("ability_id")
            for m in task.get("matches", [])
            if m.get("match_level") in ("强", "中")
        }
        gap_text = " ".join(g.get("requirement", "") for g in task.get("gaps", []))
        for r in jd["requirements"]:
            if r.get("kind") != "能力" or r.get("priority") not in ("P0", "P1"):
                continue
            aid = r.get("ability_id")
            hit = r.get("id") in matched_ids or (aid and aid in matched_abilities)
            if not hit and r.get("text", "") not in gap_text:
                is_p0 = r.get("priority") == "P0"
                warnings.append(
                    {
                        "type": "p0_uncovered" if is_p0 else "p1_uncovered",
                        "severity": "error" if is_p0 else "warn",
                        "message": (
                            f"{r.get('priority')} 要求「{r.get('text', '')}」既没有匹配也没有进缺口"
                        ),
                    }
                )

    for t in check_thresholds(jd, kb, task):
        if t["status"] == "不满足":
            warnings.append(
                {
                    "type": "threshold_unmet",
                    "severity": "warn",
                    "message": f"门槛不满足：{t['text']}（{t['reason']}）",
                }
            )

    return warnings


def summarize(warnings: list[dict]) -> tuple[int, int]:
    errors = sum(1 for w in warnings if w.get("severity") == "error")
    warns = sum(1 for w in warnings if w.get("severity") == "warn")
    return errors, warns
