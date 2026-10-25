import json
from pathlib import Path

import pytest
from jsonschema import validate

from resume_system.config import load_categories
from resume_system.export.docx_export import _render_resume

ROOT = Path(__file__).resolve().parents[1]
DEMOS = sorted(
    p for p in (ROOT / "examples").glob("demo*")
    if (p / "data/knowledge_base/knowledge_base.json").exists()
)


@pytest.mark.parametrize("demo", DEMOS, ids=[p.name for p in DEMOS])
def test_demo_kb_schema(demo):
    kb = json.loads((demo / "data/knowledge_base/knowledge_base.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/knowledge_base.schema.json").read_text(encoding="utf-8"))
    validate(kb, schema)


@pytest.mark.parametrize("demo", DEMOS, ids=[p.name for p in DEMOS])
def test_demo_resume_schema_and_sections(demo):
    task_file = next((demo / "data/jobs").glob("*.json"))
    task = json.loads(task_file.read_text(encoding="utf-8"))
    resume = task["versions"][-1]["resume_json"]
    schema = json.loads((ROOT / "schemas/resume.schema.json").read_text(encoding="utf-8"))
    validate(resume, schema)

    kb = json.loads((demo / "data/knowledge_base/knowledge_base.json").read_text(encoding="utf-8"))
    labels = {c["id"]: c["label"] for c in load_categories()}
    cat = {e["id"]: e["category"] for e in kb["experiences"]}
    for sec in resume["sections"]:
        for exp in sec["experiences"]:
            assert sec["title"] == labels[cat[exp["experience_id"]]]


@pytest.mark.parametrize("demo", DEMOS, ids=[p.name for p in DEMOS])
def test_demo_renders_docx(demo, tmp_path):
    task_file = next((demo / "data/jobs").glob("*.json"))
    task = json.loads(task_file.read_text(encoding="utf-8"))
    kb = json.loads((demo / "data/knowledge_base/knowledge_base.json").read_text(encoding="utf-8"))
    resume = task["versions"][-1]["resume_json"]
    out = tmp_path / "demo.docx"
    _render_resume(resume, kb["profile"], out, {e["id"]: e for e in kb["experiences"]})
    assert out.exists()
