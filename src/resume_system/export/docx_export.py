"""简历 DOCX 渲染器：从结构化 JSON 生成排好版的 Word 文件。

排版规范见 docs/layout_spec.md（数值真值以本文件常量为准）：
- 正文/栏目标题：微软雅黑；顶部信息框：宋体
- 字号固定：姓名 18 / 标题 13.5 / 正文 12 pt
- 超一页按 experience_rank 从低到高删字条，再回填到填满；不缩放字号
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pypdf import PdfReader

from ..config import DATA_DIR, OUTPUT_DIR, ROOT, load_style
from ..naming import output_dir, output_stem

_STYLE = load_style()
FONT_HEI = _STYLE["fonts"]["heading"]
FONT_FANGSONG = _STYLE["fonts"]["body"]
FONT_HEADER = _STYLE["fonts"]["header"]
HEADING_COLOR = RGBColor.from_string(_STYLE["colors"]["heading"].lstrip("#"))
BASE_FONT = {
    "name": _STYLE["sizes"]["name"],
    "heading": _STYLE["sizes"]["heading"],
    "body": _STYLE["sizes"]["body"],
}
BODY_INDENT_PT = _STYLE["spacing"]["body_indent_pt"]
LINE_SPACING_PT = _STYLE["spacing"]["line_pt"]
ENTRY_GAP_PT = _STYLE["spacing"]["entry_gap_pt"]
BULLET_GAP_PT = _STYLE["spacing"]["bullet_gap_pt"]
TAB_CENTER_CM = _STYLE["tabs"]["center_cm"]
TAB_RIGHT_CM = _STYLE["tabs"]["right_cm"]
PAGE = _STYLE["page"]
PHOTO_HEIGHT_CM = _STYLE["photo"]["height_cm"]
PNG_DPI = 200

SOFFICE = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
MUTOOL = shutil.which("mutool")
PDFTOPPM = shutil.which("pdftoppm")
LO_PROFILE = Path(tempfile.gettempdir()) / "resume_system_lo_profile"

JOBS_DIR = DATA_DIR / "jobs"
KB_PATH = DATA_DIR / "knowledge_base" / "knowledge_base.json"


# --------------------------------------------------------------------------- #
# 基础 helpers
# --------------------------------------------------------------------------- #
def _set_run(run, font: str, size: float, bold: bool = False, color: RGBColor | None = None) -> None:
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = color or RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rpr.get_or_add_rFonts().set(qn("w:eastAsia"), font)


def _add_bottom_border(paragraph, color: str = "2F5597") -> None:
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _remove_table_borders(table) -> None:
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        borders.append(el)
    tblPr.append(borders)


def _split_first_clause(value: str) -> tuple[str, str]:
    for sep in ("，", ","):
        idx = value.find(sep)
        if idx > 0:
            return value[:idx], value[idx:]
    return value, ""


def _add_bold_runs(paragraph, text: str, bold_terms: list[str], font: str, size: float) -> None:
    """按 bold 词把一段纯文本拆成加粗/常规 run（顺手清掉模型残留的 **）。"""
    text = (text or "").replace("**", "")
    terms = [t for t in (bold_terms or []) if t and t in text]
    if not terms:
        _set_run(paragraph.add_run(text), font, size)
        return
    pattern = "|".join(re.escape(t) for t in sorted(set(terms), key=len, reverse=True))
    marks = set(terms)
    for part in re.split(f"({pattern})", text):
        if not part:
            continue
        _set_run(paragraph.add_run(part), font, size, bold=part in marks)


def _heading(doc, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(3)
    _set_run(p.add_run(text), FONT_HEI, BASE_FONT["heading"], bold=True, color=HEADING_COLOR)
    _add_bottom_border(p)


# --------------------------------------------------------------------------- #
# 各区块
# --------------------------------------------------------------------------- #
def _header_lines(container, profile: dict, header: dict) -> None:
    name_size, body_size = BASE_FONT["name"], BASE_FONT["body"]
    contact = " | ".join(x for x in [profile.get("phone", ""), profile.get("email", "")] if x)

    p = container.paragraphs[0] if container.paragraphs else container.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    _set_run(p.add_run(profile.get("name", "")), FONT_HEADER, name_size, bold=True)

    def add_line():
        q = container.add_paragraph()
        q.paragraph_format.space_after = Pt(0)
        q.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
        return q

    if contact:
        _set_run(add_line().add_run(contact), FONT_HEADER, body_size)

    availability = (header.get("availability") or "").strip()
    if availability:
        head, tail = _split_first_clause(availability)
        q = add_line()
        _set_run(q.add_run("到岗时间："), FONT_HEADER, body_size)
        _set_run(q.add_run(head), FONT_HEADER, body_size, bold=True)
        if tail:
            _set_run(q.add_run(tail), FONT_HEADER, body_size)

    job = (header.get("job_title") or "").strip()
    if job:
        q = add_line()
        _set_run(q.add_run(f"求职意向：{job}"), FONT_HEADER, body_size)


def _write_header(doc, profile: dict, header: dict) -> None:
    photo_path = None
    if profile.get("photo"):
        p = ROOT / profile["photo"]
        photo_path = p if p.exists() else None

    if not photo_path:
        _header_lines(doc, profile, header)
        return

    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    _remove_table_borders(table)
    table.columns[0].width = Cm(15.0)
    table.columns[1].width = Cm(4.0)
    left, right = table.cell(0, 0), table.cell(0, 1)
    left.width, right.width = Cm(15.0), Cm(4.0)
    for cell in (left, right):
        tcPr = cell._tc.get_or_add_tcPr()
        vAlign = OxmlElement("w:vAlign")
        vAlign.set(qn("w:val"), "top")
        tcPr.append(vAlign)

    _header_lines(left, profile, header)
    p = right.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run().add_picture(str(photo_path), height=Cm(PHOTO_HEIGHT_CM))


def _edu_time(s: dict) -> str:
    """教育时间：有结束写区间；无结束且开始时间在未来写「入学」，否则写「至今」。"""
    start, end = s.get("start", ""), s.get("end", "")
    if start and end:
        return f"{start}–{end}"
    if not start:
        return ""
    today = __import__("datetime").date.today().strftime("%Y-%m")
    return f"{start} 入学" if start > today else f"{start} 至今"


def _write_education(doc, education: dict) -> None:
    _heading(doc, "教育背景")
    body_size = BASE_FONT["body"]
    for s in education.get("schools", []):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(TAB_CENTER_CM), WD_TAB_ALIGNMENT.CENTER)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(TAB_RIGHT_CM), WD_TAB_ALIGNMENT.RIGHT)

        time_str = _edu_time(s)
        if s.get("note"):
            time_str = f"{time_str}（{s['note']}）"
        degree = f"（{s['degree']}）" if s.get("degree") else ""
        _set_run(p.add_run(time_str), FONT_FANGSONG, body_size)
        p.add_run("\t")
        _set_run(p.add_run(s.get("school", "")), FONT_FANGSONG, body_size)
        p.add_run("\t")
        _set_run(p.add_run(f"{s.get('college', '')}{degree}"), FONT_FANGSONG, body_size)

    for f in education.get("fields", []):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
        p.paragraph_format.left_indent = Pt(BODY_INDENT_PT)
        _set_run(p.add_run(f"{f.get('label', '').replace('**', '')}："), FONT_FANGSONG, body_size, bold=True)
        _set_run(p.add_run(f.get("text", "").replace("**", "")), FONT_FANGSONG, body_size)


def _project_parts(exp: dict, kb_index: dict) -> tuple[str, str, str]:
    src = kb_index.get(exp.get("experience_id"), {})
    name = (src.get("title") or exp.get("experience_id", "")).split("·")[0].strip()
    role = src.get("role") or ""
    start, end = src.get("start_date", ""), src.get("end_date", "")
    time_str = f"{start}–{end}" if start and end else (start or "")
    return time_str, name, role


def _write_sections(doc, sections: list[dict], kb_index: dict) -> None:
    body_size = BASE_FONT["body"]
    for sec in sections:
        if not sec.get("experiences"):
            continue
        _heading(doc, sec.get("title", ""))
        first = True
        for exp in sec["experiences"]:
            if not exp.get("bullets"):
                continue
            time_str, name, role = _project_parts(exp, kb_index)
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
            if not first:
                p.paragraph_format.space_before = Pt(ENTRY_GAP_PT)
            first = False
            p.paragraph_format.tab_stops.add_tab_stop(Cm(TAB_CENTER_CM), WD_TAB_ALIGNMENT.CENTER)
            p.paragraph_format.tab_stops.add_tab_stop(Cm(TAB_RIGHT_CM), WD_TAB_ALIGNMENT.RIGHT)
            for i, part in enumerate([time_str, name, role]):
                if i:
                    p.add_run("\t")
                _set_run(p.add_run(part), FONT_FANGSONG, body_size, bold=True)

            for b in exp["bullets"]:
                q = doc.add_paragraph()
                q.paragraph_format.space_after = Pt(0)
                q.paragraph_format.space_before = Pt(BULLET_GAP_PT)
                q.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
                q.paragraph_format.left_indent = Pt(BODY_INDENT_PT)
                _set_run(q.add_run(f"{b.get('label', '').replace('**', '')}："), FONT_FANGSONG, body_size, bold=True)
                _add_bold_runs(q, b.get("desc", ""), b.get("bold", []), FONT_FANGSONG, body_size)


def _write_abilities(doc, abilities: list[dict]) -> None:
    _heading(doc, "个人能力")
    body_size = BASE_FONT["body"]
    for ab in abilities:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(BULLET_GAP_PT)
        p.paragraph_format.line_spacing = Pt(LINE_SPACING_PT)
        p.paragraph_format.left_indent = Pt(BODY_INDENT_PT)
        _set_run(p.add_run(f"{ab.get('label', '').replace('**', '')}："), FONT_FANGSONG, body_size, bold=True)
        _add_bold_runs(p, ab.get("text", ""), ab.get("bold", []), FONT_FANGSONG, body_size)


def _render_resume(resume: dict, profile: dict, output_path: Path, kb_index: dict) -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(PAGE["width_cm"])
    section.page_height = Cm(PAGE["height_cm"])
    section.left_margin = Cm(PAGE["margin_cm"])
    section.right_margin = Cm(PAGE["margin_cm"])
    section.top_margin = Cm(PAGE["margin_cm"])
    section.bottom_margin = Cm(PAGE["margin_cm"])

    _write_header(doc, profile, resume.get("header", {}))
    _write_education(doc, resume.get("education", {}))
    _write_sections(doc, resume.get("sections", []), kb_index)
    _write_abilities(doc, resume.get("abilities", []))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


# --------------------------------------------------------------------------- #
# 单页适配
# --------------------------------------------------------------------------- #
def _all_units(resume: dict, rank: dict[str, int]) -> list[tuple[str, int]]:
    """按「相关度低 → 高、同段从后往前」排出可删单位。"""
    exps = [exp for sec in resume.get("sections", []) for exp in sec.get("experiences", [])]
    exps.sort(key=lambda e: rank.get(e.get("experience_id", ""), 999), reverse=True)
    units: list[tuple[str, int]] = []
    for exp in exps:
        for i in range(len(exp.get("bullets", [])) - 1, -1, -1):
            units.append((exp.get("experience_id", ""), i))
    return units


def _view(resume: dict, removed: set[tuple[str, int]]) -> dict:
    out = copy.deepcopy(resume)
    sections = []
    for sec in out.get("sections", []):
        exps = []
        for exp in sec.get("experiences", []):
            keep = [
                b
                for i, b in enumerate(exp.get("bullets", []))
                if (exp.get("experience_id", ""), i) not in removed
            ]
            if keep:
                exp["bullets"] = keep
                exps.append(exp)
        if exps:
            sec["experiences"] = exps
            sections.append(sec)
    out["sections"] = sections
    return out


def _pages(resume: dict, profile: dict, kb_index: dict, tmp: Path) -> int:
    tmp_docx = tmp / "fit.docx"
    _render_resume(resume, profile, tmp_docx, kb_index)
    pdf = _docx_to_pdf(tmp_docx, tmp)
    return len(PdfReader(str(pdf)).pages)


def _pick_unit(
    resume: dict, rank: dict[str, int], removed: set[tuple[str, int]]
) -> tuple[str, int] | None:
    """优先删「还有多条字条」的经历里最不相关的一条，避免整块消失导致页面突然空一截。"""
    exps = [exp for sec in resume.get("sections", []) for exp in sec.get("experiences", [])]
    exps.sort(key=lambda e: rank.get(e.get("experience_id", ""), 999), reverse=True)

    multi: list[tuple[int, str, int]] = []
    single: list[tuple[int, str, int]] = []
    for exp in exps:
        eid = exp.get("experience_id", "")
        live = [i for i in range(len(exp.get("bullets", []))) if (eid, i) not in removed]
        if not live:
            continue
        item = (rank.get(eid, 999), eid, live[-1])
        (multi if len(live) >= 2 else single).append(item)

    pool = multi or single
    if not pool:
        return None
    _, eid, index = max(pool, key=lambda x: x[0])
    return (eid, index)


def _fit_to_one_page(resume: dict, rank: dict[str, int], profile: dict, kb_index: dict) -> dict:
    removed: set[tuple[str, int]] = set()
    order: list[tuple[str, int]] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        while True:
            if _pages(_view(resume, removed), profile, kb_index, tmp) <= 1:
                break
            nxt = _pick_unit(resume, rank, removed)
            if nxt is None:
                print("[提示] 已删到无可删，仍超一页，请手动处理。")
                break
            removed.add(nxt)
            order.append(nxt)

        added = 0
        for u in reversed(order):
            removed.discard(u)
            if _pages(_view(resume, removed), profile, kb_index, tmp) > 1:
                removed.add(u)
            else:
                added += 1

    if order:
        msg = f"[适配] 为压到 1 页，删掉 {len(order)} 条字条"
        if added:
            msg += f"，回填 {added} 条"
        print(msg + "。")
    return _view(resume, removed)


# --------------------------------------------------------------------------- #
# PDF / PNG 导出
# --------------------------------------------------------------------------- #
def _docx_to_pdf(docx_path: Path, out_dir: Path) -> Path:
    LO_PROFILE.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            SOFFICE,
            f"-env:UserInstallation=file://{LO_PROFILE}",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(docx_path),
        ],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return out_dir / (docx_path.stem + ".pdf")


def _pdf_to_png(pdf_path: Path, out_prefix: Path, dpi: int = PNG_DPI) -> list[Path]:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    for old in out_prefix.parent.glob(out_prefix.name + "-*.png"):
        old.unlink()
    if MUTOOL:
        subprocess.run(
            [MUTOOL, "draw", "-r", str(dpi), "-o", f"{out_prefix}-%d.png", str(pdf_path)],
            check=True,
            capture_output=True,
            timeout=120,
        )
    elif PDFTOPPM:
        subprocess.run(
            [PDFTOPPM, "-png", "-r", str(dpi), str(pdf_path), str(out_prefix)],
            check=True,
            capture_output=True,
            timeout=120,
        )
    else:
        raise RuntimeError("未找到 mutool 或 pdftoppm，无法导出 PNG")
    return sorted(out_prefix.parent.glob(out_prefix.name + "-*.png"))


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def render_resume_from_task(
    task_id: str | None,
    output_path: Path | None = None,
    export_pdf: bool = False,
    export_png: bool = False,
    dpi: int = PNG_DPI,
) -> Path:
    """从任务的结构化 resume_json 渲染；旧 markdown 任务明确报错。"""
    if task_id:
        task_file = JOBS_DIR / f"{task_id}.json"
    else:
        files = sorted(JOBS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        task_file = files[0] if files else None
    if not task_file or not task_file.exists():
        raise FileNotFoundError("未找到任务文件，请先跑 agent_b 生成简历")

    task = json.loads(task_file.read_text(encoding="utf-8"))
    version = task["versions"][-1]
    if "resume_json" not in version:
        raise ValueError(
            f"任务 {task['id'][:8]} 是旧格式（markdown），新渲染器只支持 resume_json；"
            "请用原 JD 重新生成一版。"
        )
    resume = copy.deepcopy(version["resume_json"])
    header = resume.setdefault("header", {})
    header.setdefault("job_title", task.get("job_title", ""))
    if not header.get("availability"):
        header["availability"] = task.get("availability", "")

    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    profile = kb.get("profile", {})
    kb_index = {e["id"]: e for e in kb.get("experiences", [])}
    rank = {
        i.get("experience_id"): int(i.get("rank", 999))
        for i in task.get("experience_rank", [])
    }

    out_dir = output_dir(task, OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    output = output_path or (out_dir / f"{output_stem(task)}.docx")

    fitted = _fit_to_one_page(resume, rank, profile, kb_index)
    _render_resume(fitted, profile, output, kb_index)

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = _docx_to_pdf(output, Path(tmp))
        pages = len(PdfReader(str(pdf_path)).pages)
        if pages > 1:
            print(f"[警告] 简历 {pages} 页，超过一页，请自行删减内容。")
        if export_pdf:
            final_pdf = output.with_suffix(".pdf")
            shutil.copyfile(pdf_path, final_pdf)
            print(f"[完成] 已生成 {final_pdf.name}")
        if export_png:
            for p in _pdf_to_png(pdf_path, output.with_suffix(""), dpi):
                print(f"[完成] 已生成 {p.name}")

    print(
        f"[完成] 已生成 {output}（姓名 {BASE_FONT['name']}pt / 标题 {BASE_FONT['heading']}pt / 正文 {BASE_FONT['body']}pt）"
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="把任务的结构化简历渲染成 Word（可选 PDF/PNG）")
    parser.add_argument("--task", help="任务 id（默认最新任务）")
    parser.add_argument("--output", help="输出 docx 路径")
    parser.add_argument("--pdf", action="store_true", help="同时导出 PDF")
    parser.add_argument("--png", action="store_true", help="同时导出 PNG（发 BOSS 直聘用）")
    parser.add_argument("--dpi", type=int, default=PNG_DPI, help=f"PNG 分辨率（默认 {PNG_DPI}）")
    args = parser.parse_args()

    output = Path(args.output) if args.output else None
    path = render_resume_from_task(args.task, output, export_pdf=args.pdf, export_png=args.png, dpi=args.dpi)
    print(f"文件：{path}")


if __name__ == "__main__":
    main()
