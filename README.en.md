# resume-system

A small, data-first resume pipeline with **zero API-key dependency**. The "thinking" steps (A: extract experiences, B: generate the resume) are done by your own AI agent (Claude Code / Cursor / …); this repo provides the JSON schemas, a validator, and a renderer — all pure Python, no model calls, no API key.

- **A (explore)**: extract facts / STAR evidence from raw materials → knowledge base JSON
- **B (generate)**: parse a JD, match evidence, write a structured resume (JSON)
- **Renderer**: JSON → one-page DOCX / PDF / PNG + companion analysis markdown

Facts and wording are separated: the knowledge base stores what happened, each job task stores how it was expressed.

## Quickstart (zero key)

Full agent workflow: [docs/agent_usage.md](docs/agent_usage.md).

```bash
pip install -e .

# 1. ingest materials (docx/pdf/txt/md)
python tools/ingest.py path/to/materials/

# 2. have your agent produce data/knowledge_base/knowledge_base.json
#    (following schemas/knowledge_base.schema.json)

# 3. validate
python tools/validate.py

# 4. have your agent produce a job task (with resume_json), then render
python -m resume_system.export.docx_export --task <task-id> --pdf --png
```

Try the fictional demo without any model or agent:

```bash
RESUME_DATA_DIR=examples/demo/data RESUME_OUTPUT_DIR=/tmp/demo_out \
python -m resume_system.export.docx_export --task demo-render --pdf --png
```

## Features

- Structured `resume_json` (education / sections / bullets / abilities) — the renderer never parses markdown
- Configurable sections, ability taxonomy, layout, and fonts (`config/*.yaml`)
- Schema + cross-reference validation (`python tools/validate.py`)
- Overlap detection (within and across experiences)
- Pre-publish checks: missing honors, wrong section, unmet thresholds
- Privacy boundary: `data/` and `output/` are git-ignored; a fictional demo is included

## Requirements

- Python ≥ 3.10
- LibreOffice (`soffice`) for PDF/PNG; `mutool` or `pdftoppm` for PNG
- Fonts: defaults are Microsoft YaHei / Songti; change `config/style.yaml` or install equivalents

## Tests

```bash
pip install -e ".[dev]"
pytest -q
```

## Limitations

- Layout is designed for a one-page Chinese resume (A4)
- No OCR for scanned PDFs/images
- Generation quality depends on your own agent/model; this repo guarantees structure and traceability, not judgment

## Privacy

Real knowledge bases, raw materials, photos, job tasks and outputs never enter the public repository. They live in `data/` and `output/`, both ignored by git. The public demo uses fictional data only.

## License

MIT — see [LICENSE](LICENSE).
