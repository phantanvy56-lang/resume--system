import json
from pathlib import Path

from docx import Document

from resume_system.export.docx_export import _render_resume

ROOT = Path(__file__).resolve().parents[1]


def test_render_demo_to_docx(tmp_path):
    task = json.loads((ROOT / "examples/demo/data/jobs/demo-render.json").read_text(encoding="utf-8"))
    resume = task["versions"][-1]["resume_json"]
    kb = json.loads((ROOT / "examples/demo/data/knowledge_base/knowledge_base.json").read_text(encoding="utf-8"))
    out = tmp_path / "demo.docx"

    _render_resume(resume, kb["profile"], out, {e["id"]: e for e in kb["experiences"]})
    assert out.exists()

    doc = Document(out)
    text = [p.text for p in doc.paragraphs if p.text.strip()]
    assert "教育背景" in text
    assert "个人能力" in text
    assert any("示例大学" in t for t in text)
