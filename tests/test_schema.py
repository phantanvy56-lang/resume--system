import json
from pathlib import Path

from jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]


def test_demo_kb_matches_schema():
    kb = json.loads((ROOT / "examples/demo/data/knowledge_base/knowledge_base.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/knowledge_base.schema.json").read_text(encoding="utf-8"))
    validate(kb, schema)


def test_demo_resume_matches_schema():
    task = json.loads((ROOT / "examples/demo/data/jobs/demo-render.json").read_text(encoding="utf-8"))
    resume = task["versions"][-1]["resume_json"]
    schema = json.loads((ROOT / "schemas/resume.schema.json").read_text(encoding="utf-8"))
    validate(resume, schema)
