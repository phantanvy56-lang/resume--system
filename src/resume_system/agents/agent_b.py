from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from jsonschema import validate as jsonschema_validate

from ..config import DATA_DIR, OUTPUT_DIR, ROOT, load_categories, load_optional_text, load_profile_blocks
from ..llm.factory import get_llm
from ..naming import output_dir, output_stem
from ..checks import check_thresholds, collect_warnings, summarize
from ..jd_parse import parse_jd
from ..review import find_overlaps_resume
from ..storage.kb_store import KBStore
from ..storage.task_store import TaskStore

PROMPT_FLOW = ROOT / "src" / "resume_system" / "prompts" / "b_resume.md"
PROMPT_STYLE = ROOT / "src" / "resume_system" / "prompts" / "b_style.md"
KB_PATH = DATA_DIR / "knowledge_base" / "knowledge_base.json"
KB_SCHEMA_PATH = ROOT / "schemas" / "knowledge_base.schema.json"
JOBS_DIR = DATA_DIR / "jobs"
TASK_SCHEMA_PATH = ROOT / "schemas" / "job_task.schema.json"
RESUME_SCHEMA_PATH = ROOT / "schemas" / "resume.schema.json"
PREF_PATH = DATA_DIR / "preferences.json"

_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)```", re.DOTALL)


def _build_system_prompt() -> str:
    """拼接公开提示词 + 本地私有覆盖（固定文案 / few-shot / 打招呼句式）。"""
    parts = [
        PROMPT_FLOW.read_text(encoding="utf-8"),
        "\n\n---\n\n",
        PROMPT_STYLE.read_text(encoding="utf-8"),
    ]
    blocks = load_profile_blocks()
    if blocks:
        lines = ["", "", "## 固定能力文案（照抄 text 和 bold，不要改写）", ""]
        for b in blocks:
            lines.append(f"- {b.get('label', '')}：{b.get('text', '')}")
            lines.append(f"  bold: {json.dumps(b.get('bold', []), ensure_ascii=False)}")
        parts.append("\n".join(lines))
    few = load_optional_text("few_shot.md")
    if few:
        parts.append("\n\n## 补充 few-shot（私有样例）\n" + few)
    cats = load_categories()
    if cats:
        lines = ["", "", "## 板块映射（category → 板块标题 / order）", ""]
        for c in cats:
            lines.append(f"- {c['id']} → {c['label']}（order {c.get('order', 99)}）")
        lines.append("- 教育背景固定最前，个人能力固定最后。")
        parts.append("\n".join(lines))
    greeting = load_optional_text("greeting.md")
    if greeting:
        parts.append("\n\n## 打招呼固定句式（优先使用）\n" + greeting)
    return "".join(parts)


def _kb_to_context(store: KBStore) -> str:
    """把知识库转成给 B 的上下文（能力 -> 证据 -> 经历）。"""
    kb = store.load()
    lines = []

    lines.append("## 规范能力（abilities）")
    for ab in kb.get("abilities", []):
        lines.append(
            f"- id={ab['id']} | [{ab['label']}] {ab.get('description', '')}（证据 {len(ab.get('star_statement_refs', []))} 条）"
        )

    lines.append("\n## 证据（star_statements）")
    for st in kb.get("star_statements", []):
        lines.append(
            f"- id={st['id']} | 经历id={st.get('experience_id', '')} | 能力={st['ability']} | 情境={st.get('situation', '')} | "
            f"任务={st.get('task', '')} | 行动={st.get('action', '')} | 结果={st.get('result', '')}"
        )

    lines.append("\n## 经历（experiences）")
    for ex in kb.get("experiences", []):
        time_str = ""
        if ex.get("start_date"):
            time_str = f"[{ex['start_date']}–{ex.get('end_date') or '至今'}] "
        role_str = f" 角色={ex['role']} |" if ex.get("role") else ""
        lines.append(
            f"- id={ex['id']} | 板块={ex.get('category', '')} |{role_str} {time_str}{ex['title']}"
            f"（{ex['verification_status']}）：" + "；".join(ex.get("facts", []))
        )

    lines.append("\n## 教育背景（education）")
    for ed in kb.get("education", []):
        if ed.get("end_date"):
            time_str = f"{ed.get('start_date', '')}–{ed.get('end_date', '')}"
        elif ed.get("start_date"):
            time_str = f"{ed.get('start_date', '')} 入学"
        else:
            time_str = ""
        lines.append(f"- {time_str}｜{ed['school']}｜{ed['major']}（{ed['degree']}）")
        if ed.get("note"):
            lines.append(f"  备注：{ed['note']}")
        if ed.get("gpa"):
            lines.append(f"  GPA {ed['gpa']}/{ed.get('gpa_scale', '')} | 排名 {ed.get('rank', '')}")
        for c in ed.get("courses", []):
            score = f" / {c['score']}" if c.get("score") else ""
            lines.append(f"  课程：{c['name']}（{c.get('grade', '')}{score}）")
        for e in ed.get("english", []):
            lines.append(f"  英语：{e['name']} {e.get('score', '')}")

    lines.append("\n## 荣誉奖项（honors）")
    for h in kb.get("honors", []):
        lines.append(f"- {h['title']}（{h.get('year', '')}，{h.get('level', '')}，{h.get('detail', '')}）")

    lines.append("\n## 技能（skills）")
    for s in kb.get("skills", []):
        lines.append(f"- {s['category']}：{'、'.join(s.get('items', []))}")

    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """从模型输出里抠出 JSON 对象；容忍代码块和前后废话。"""
    m = _JSON_BLOCK_RE.search(text)
    raw = m.group(1) if m else text
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("输出里没有找到 JSON 对象")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("顶层不是 JSON 对象")
    return data


def _validate_resume(resume: dict) -> None:
    schema = json.loads(RESUME_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema_validate(resume, schema)


def _parse_with_retry(llm, messages: list[dict], text: str) -> tuple[dict, str]:
    """解析 JSON；失败一次就让模型只重发 JSON。"""
    try:
        return _extract_json(text), text
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[解析] 输出不是合法 JSON（{e}），让模型重发一次")
        fix_messages = messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    f"上面的输出不是合法 JSON：{e}。\n"
                    "请只输出一个完整的 JSON 对象（不要 markdown 代码块、不要解释、不要省略字段）。"
                ),
            },
        ]
        resp = llm.chat(fix_messages)
        return _extract_json(resp.text), resp.text


def _normalize_sections(resume: dict, kb: dict) -> dict:
    """按知识库 category 把经历放回对应板块，并统一板块顺序（防止模型放错板块）。"""
    cats = load_categories()
    label_by_cat = {c["id"]: c["label"] for c in cats}
    order_by_label = {c["label"]: c.get("order", 99) for c in cats}
    exp_cat = {e.get("id"): e.get("category") for e in kb.get("experiences", [])}

    buckets: dict[str, list] = {}
    for sec in resume.get("sections", []):
        for exp in sec.get("experiences", []):
            cat = exp_cat.get(exp.get("experience_id"))
            label = label_by_cat.get(cat) or sec.get("title", "")
            buckets.setdefault(label, []).append(exp)

    ordered = sorted(buckets, key=lambda t: order_by_label.get(t, 99))
    out = dict(resume)
    out["sections"] = [{"title": t, "experiences": buckets[t]} for t in ordered]
    return out


def _apply_payload(task_store: TaskStore, task: dict, payload: dict) -> dict:
    """把结构化字段写进任务（只更新 payload 里出现的字段）。"""
    fields = {}
    for key in (
        "requirements",
        "matches",
        "selected_experience_ids",
        "experience_rank",
        "gaps",
        "greeting",
    ):
        if key in payload:
            fields[key] = payload[key]
    if not fields:
        return task
    return task_store.update_task(task["id"], **fields)


def _load_preferences() -> str:
    """读取通用表达偏好，转成给 B 的规则列表。"""
    if not PREF_PATH.exists():
        return "（无表达偏好）"
    data = json.loads(PREF_PATH.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    return "\n".join(f"- {r}" for r in rules)


def _overlap_repair_prompt(issues: list[dict]) -> str:
    """把自检出的重合翻译成给模型的 JSON 修订指令。"""
    lines = [
        "你上一次输出的 resume 里有字条重合。请只修改 resume.sections 里涉及的字条，其他字段逐字保留：",
        "1. 同一段经历内：合并成一条 bullet，label 取更概括的一个，保留两条里的全部事实/数字/工具，不新增内容；",
        "2. 不同经历之间：保留 experience_rank 更靠前那段里的 bullet，删掉另一条；",
        "3. 改完后每条 bullet 的 bold 词必须仍原样出现在 desc 里。",
        "",
        "需要处理的重合：",
    ]
    for it in issues:
        lines.append(
            f"- 经历「{it['project']}」第 {it.get('index_a', '?')} 条「{it['a']}」与"
            f"第 {it.get('index_b', '?')} 条「{it['b']}」：{it['detail']}"
        )
        if it.get("a_desc"):
            lines.append(f"    A：{it['a_desc']}")
        if it.get("b_desc"):
            lines.append(f"    B：{it['b_desc']}")
    lines += ["", "输出要求：完整 JSON（与上次结构相同），不要解释、不要 markdown。"]
    return "\n".join(lines)


def _autofix_overlaps(llm, messages: list[dict], payload: dict, raw: str, enabled: bool = True):
    """有重合就带着具体问题回喂模型改一轮；改得更好才采用。"""
    if not enabled:
        return payload, raw
    issues = find_overlaps_resume(payload.get("resume", {}))
    if not issues:
        return payload, raw
    fix_messages = messages + [
        {"role": "assistant", "content": raw},
        {"role": "user", "content": _overlap_repair_prompt(issues)},
    ]
    resp = llm.chat(fix_messages)
    try:
        fixed = _extract_json(resp.text)
        _validate_resume(fixed["resume"])
    except Exception as e:  # noqa: BLE001
        print(f"[自检] 模型修订结果不可用（{e}），保留原稿")
        return payload, raw
    after = find_overlaps_resume(fixed.get("resume", {}))
    print(f"[自检] 发现 {len(issues)} 处重合，已请模型修订（修订后 {len(after)} 处）")
    if len(after) < len(issues):
        return fixed, resp.text
    return payload, raw


def _md_escape(text: str) -> str:
    return (text or "").replace("|", "／").replace("\n", " ")


def _project_line(exp: dict, kb_index: dict) -> str:
    """项目行：时间｜名称｜角色，全部从知识库取。"""
    src = kb_index.get(exp.get("experience_id"), {})
    name = (src.get("title") or exp.get("experience_id", "")).split("·")[0].strip()
    role = src.get("role") or ""
    start, end = src.get("start_date", ""), src.get("end_date", "")
    time_str = f"{start}–{end}" if start and end else (start or "")
    parts = [p for p in (time_str, name, role) if p]
    return "｜".join(parts)


def _analysis_markdown(task: dict, payload: dict, warnings: list[dict] | None = None) -> str:
    """从结构化数据生成人看的 markdown（匹配表 / 正文 / 打招呼 / 缺口）。"""
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    kb_index = {e["id"]: e for e in kb.get("experiences", [])}
    resume = payload.get("resume", {})
    header = resume.get("header", {})

    lines: list[str] = [
        f"# {task['job_title']} · 简历分析",
        "",
        f"- 公司：{task.get('company') or '—'}",
        f"- 求职意向：{header.get('job_title') or task['job_title']}",
        f"- 到岗时间：{header.get('availability') or task.get('availability') or '—'}",
        f"- 更新：{task.get('updated_at', '')}",
        "",
        "---",
        "",
    ]
    lines += ["## 发布前检查", ""]
    if warnings:
        for w in warnings:
            lines.append(f"- **[{w.get('severity', 'warn')}]** {w.get('message', '')}")
    else:
        lines.append("未发现问题。")
    lines.append("")
    jd = task.get("jd_analysis") or {}
    if jd:
        lines += ["## 岗位理解（JD 解析）", ""]
        goal = jd.get("job_goal", {})
        if goal.get("mission"):
            lines.append(f"- 目标：{goal['mission']}")
        if jd.get("core_abilities"):
            lines.append(
                "- 核心能力：" + "；".join(
                    f"{a.get('priority', '')} {a.get('name', '')}"
                    for a in jd["core_abilities"]
                )
            )
        if jd.get("open_questions"):
            lines.append("- 待核实：" + "；".join(jd["open_questions"]))
        if task.get("threshold_checks"):
            lines.append(
                "- 门槛核对：" + "；".join(
                    f"{t.get('text', '')[:22]}：{t.get('status', '')}"
                    for t in task["threshold_checks"]
                )
            )
        lines += ["", "---", ""]
    lines += ["## 一、能力匹配表",
        "",
        "| # | JD 要求 | 命中能力 | 匹配理由 | 匹配度 |",
        "|---|---|---|---|---|",
    ]
    for i, m in enumerate(payload.get("matches", []), 1):
        lines.append(
            f"| {i} | {_md_escape(m.get('requirement', ''))} | {_md_escape(m.get('ability_label', ''))} | "
            f"{_md_escape(m.get('reason', ''))} | {m.get('match_level', '')} |"
        )

    lines += ["", "## 二、简历正文", ""]
    if header.get("job_title"):
        lines.append(f"求职意向：{header['job_title']}")
    if header.get("availability"):
        lines.append(f"到岗时间：{header['availability']}")
    if header.get("job_title") or header.get("availability"):
        lines.append("")

    edu = resume.get("education", {})
    lines += ["### 教育背景", ""]
    for s in edu.get("schools", []):
        time_str = f"{s.get('start', '')}–{s.get('end', '')}" if s.get("end") else (s.get("start") or "")
        if s.get("note"):
            time_str = f"{time_str}（{s['note']}）"
        degree = f"（{s['degree']}）" if s.get("degree") else ""
        lines.append(f"{time_str}｜{s.get('school', '')}｜{s.get('college', '')}{degree}")
    for f in edu.get("fields", []):
        lines.append(f"{f.get('label', '')}：{f.get('text', '')}")
    lines.append("")

    for sec in resume.get("sections", []):
        lines += [f"### {sec.get('title', '')}", ""]
        for exp in sec.get("experiences", []):
            lines.append(_project_line(exp, kb_index))
            for b in exp.get("bullets", []):
                lines.append(f"- **{b.get('label', '')}**：{b.get('desc', '')}")
            lines.append("")

    lines += ["### 个人能力", ""]
    for ab in resume.get("abilities", []):
        lines.append(f"- **{ab.get('label', '')}**：{ab.get('text', '')}")
    lines.append("")

    greeting = payload.get("greeting", "")
    if greeting:
        lines += ["---", "", "## 三、打招呼（BOSS / 邮件首条）", "", greeting, ""]

    gaps = payload.get("gaps", [])
    if gaps:
        lines += ["---", "", "## 四、缺口清单", "", "| JD 要求 | 缺失能力 | 转 A 的追问 |", "|---|---|---|"]
        for g in gaps:
            lines.append(
                f"| {_md_escape(g.get('requirement', ''))} | {_md_escape(g.get('missing_ability', ''))} | "
                f"{_md_escape(g.get('question', ''))} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _write_analysis_md(task: dict, payload: dict, warnings: list[dict] | None = None) -> Path:
    md_dir = output_dir(task, OUTPUT_DIR)
    md_dir.mkdir(parents=True, exist_ok=True)
    path = md_dir / f"{output_stem(task)}_分析.md"
    path.write_text(_analysis_markdown(task, payload, warnings), encoding="utf-8")
    return path


def generate(
    interactive: bool = True,
    jd_text: str | None = None,
    job_title: str | None = None,
    company: str | None = None,
    availability: str | None = None,
    export_docx: bool = False,
    export_png: bool = False,
    task_id: str | None = None,
    autofix: bool = True,
    strict: bool = False,
    use_jd_parse: bool = True,
) -> None:
    """B：岗位分析 + 简历生成。输出结构化 JSON，落盘到任务工作区。"""
    kb_store = KBStore(KB_PATH, KB_SCHEMA_PATH)
    task_store = TaskStore(JOBS_DIR, TASK_SCHEMA_PATH)
    llm = get_llm()

    system_prompt = _build_system_prompt()
    kb_context = _kb_to_context(kb_store)

    if task_id:
        task = task_store.load(task_id)
        title = task["job_title"]
        jd = task.get("jd_text") or jd_text
        if not jd:
            print("该任务没有 JD 文本，无法续跑。")
            return
        if availability or company:
            task = task_store.update_task(
                task["id"],
                **({"availability": availability} if availability else {}),
                **({"company": company} if company else {}),
            )
        print(f"[任务] 续用 {task['id']}（{title}），本次结果作为新版本追加")
    else:
        if job_title:
            title = job_title
        elif interactive:
            title = input("岗位名称（回车跳过，默认「未命名岗位」）：").strip() or "未命名岗位"
        else:
            title = "未命名岗位"

        jd = jd_text
        if not jd and interactive:
            jd = input("请粘贴岗位 JD（回车结束）：").strip()
        if not jd:
            print("未提供 JD，无法生成，退出。")
            return

        task = task_store.create_task(title, jd, company=company, availability=availability)
        print(f"[任务] 已创建 {task['id']}（{title}），结果将落盘到 {JOBS_DIR}")

    jd_block = ""
    jd_errors: list[str] = []
    if use_jd_parse:
        print("[JD] 解析岗位要求…")
        jd_analysis, jd_errors = parse_jd(jd, llm=llm)
        if jd_errors:
            print(f"[JD] {len(jd_errors)} 处待核对：")
            for e in jd_errors[:5]:
                print(f"  - {e}")
        task = task_store.update_task(task["id"], jd_analysis=jd_analysis)
        jd_block = (
            "\n\n## JD 解析结果（直接使用，不要重新抽取）\n"
            + json.dumps(
                {
                    "requirements": jd_analysis.get("requirements", []),
                    "core_abilities": jd_analysis.get("core_abilities", []),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"以下是知识库内容：\n\n{kb_context}\n\n"
                f"以下是通用表达偏好（必须遵循）：\n{_load_preferences()}\n\n"
                f"以下是岗位信息（header 里的 job_title / availability 原样照抄）：\n"
                f"- 岗位名称：{task['job_title']}\n"
                f"- 到岗时间：{task.get('availability') or '（未提供，availability 留空）'}\n"
                f"{jd_block}\n\n"
                f"以下是岗位 JD：\n\n{jd}\n\n"
                "请按规则只输出一个 JSON（结构见系统提示），不要输出 markdown 正文或解释。"
            ),
        },
    ]

    version_changes = "续改" if task_id else "初版"
    warnings: list[dict] = []
    errors = warns = 0
    while True:
        resp = llm.chat(messages)
        payload, raw = _parse_with_retry(llm, messages, resp.text)
        payload, raw = _autofix_overlaps(llm, messages, payload, raw, autofix)

        if "resume" not in payload:
            print("[错误] 输出缺少 resume 字段，无法落盘。")
            break
        payload["resume"] = _normalize_sections(payload["resume"], kb_store.load())
        _validate_resume(payload["resume"])

        kb = kb_store.load()
        task = _apply_payload(task_store, task, payload)
        thresholds = check_thresholds(task.get("jd_analysis") or {}, kb, task)
        warnings = collect_warnings(payload["resume"], kb, task)
        for e in jd_errors:
            warnings.append({"type": "jd_parse_issue", "severity": "warn", "message": e})
        task = task_store.update_task(
            task["id"], warnings=warnings, threshold_checks=thresholds
        )
        md_path = _write_analysis_md(task, payload, warnings)
        task = task_store.add_version(
            task["id"],
            resume_json=payload["resume"],
            analysis_md=md_path.read_text(encoding="utf-8"),
            changes=version_changes,
        )

        print(f"\n[已落盘] 任务 {task['id']} 第 {task['versions'][-1]['version']} 版")
        print(f"[分析] 匹配表 / 正文 / 打招呼 / 缺口已写入 {md_path}")
        errors, warns = summarize(warnings)
        print(
            f"[摘要] 匹配 {len(task.get('matches', []))} 条 / "
            f"缺口 open {sum(1 for g in task.get('gaps', []) if g.get('status') == 'open')} 条"
        )
        print(f"[检查] {len(warnings)} 处需要确认（error {errors} / warn {warns}）")
        for w in warnings[:6]:
            print(f"  - [{w.get('severity')}] {w.get('message', '')[:90]}")
        if warnings:
            print(f"  详见 {md_path}")

        if not interactive:
            break
        more = input("\n[继续] 要调整哪条字条/匹配？（直接说要求，或输入 q 结束）：").strip()
        if more.lower() == "q":
            break
        version_changes = more
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": more})

    if strict and errors:
        print("[strict] 存在 error 级检查项，跳过 docx / pdf / png 导出")
    elif export_docx or export_png:
        from ..export.docx_export import render_resume_from_task

        render_resume_from_task(task["id"], export_pdf=export_png, export_png=export_png)


def main() -> None:
    parser = argparse.ArgumentParser(description="B：岗位分析 + 简历生成（结构化 JSON，落盘到 data/jobs/）")
    parser.add_argument("--jd", help="JD 文件路径（txt/md）")
    parser.add_argument("--task", help="续跑已有任务 id（同一岗位反复修改时用，结果追加为下一版）")
    parser.add_argument("--job-title", help="岗位名称")
    parser.add_argument("--company", help="公司名称")
    parser.add_argument("--availability", help="到岗时间/每周天数/实习时长（如「随时到岗，每周5天，可实习6个月」）")
    parser.add_argument("--no-interactive", action="store_true", help="非交互：生成一版后落盘退出")
    parser.add_argument("--export-docx", action="store_true", help="生成后自动渲染成排好版的 Word 简历")
    parser.add_argument("--export-png", action="store_true", help="生成后导出 PDF + PNG（发 BOSS 直聘用）")
    parser.add_argument("--no-autofix", action="store_true", help="关掉「字条重合自动回喂修订」")
    parser.add_argument("--strict", action="store_true", help="有 error 级检查项时不导出成稿")
    parser.add_argument("--no-jd-parse", action="store_true", help="跳过独立的 JD 解析，让 B 自己从 JD 抽要求")
    args = parser.parse_args()

    jd_text = None
    if args.jd:
        jd_text = Path(args.jd).read_text(encoding="utf-8")

    generate(
        interactive=not args.no_interactive,
        jd_text=jd_text,
        job_title=args.job_title,
        company=args.company,
        availability=args.availability,
        export_docx=args.export_docx,
        export_png=args.export_png,
        task_id=args.task,
        autofix=not args.no_autofix,
        strict=args.strict,
        use_jd_parse=not args.no_jd_parse,
    )


if __name__ == "__main__":
    main()
