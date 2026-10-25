# resume-system

A small, data-first resume pipeline:

- **A (explore)**: reads raw materials, extracts facts / STAR evidence into a knowledge base
- **B (generate)**: parses a JD, matches evidence, writes a structured resume (JSON)
- **Renderer**: turns the JSON into a one-page DOCX / PDF / PNG with a companion analysis markdown

Facts and wording are separated: the knowledge base stores what happened, each job task stores how it was expressed.

## Quickstart

```bash
pip install -e .
cp .env.example .env          # put DEEPSEEK_API_KEY here

# 1. ingest materials (docx/pdf/txt/md)
python tools/ingest.py path/to/materials/

# 2. build the knowledge base (interactive)
python -m resume_system.agents.agent_a --only report

# 3. generate a resume for a JD
python -m resume_system.agents.agent_b \
  --jd jd.txt --job-title "Data Analyst" \
  --company "Example Inc" --no-interactive \
  --export-docx --export-png

# 4. validate data
python tools/validate.py
```

Try the fictional demo without an API key:

```bash
RESUME_DATA_DIR=examples/demo/data RESUME_OUTPUT_DIR=/tmp/demo_out \
python -m resume_system.export.docx_export --task demo-render --pdf --png
```

## Features

- Structured `resume_json` (education / sections / bullets / abilities) — the renderer never parses markdown
- Configurable sections, ability taxonomy, layout, and fonts (`config/*.yaml`)
- JD analysis with capability / threshold / trait classification and P0 coverage checks
- Overlap detection (within and across experiences) with optional model self-repair
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
- Old markdown-only tasks are frozen; regenerate from the original JD
- Generation quality depends on the chosen model; the system guarantees structure and traceability, not judgment

## Privacy

Real knowledge bases, raw materials, photos, job tasks and outputs never enter the public repository.
They live in `data/` and `output/`, both ignored by git. The public demo uses fictional data only.

## License

MIT — see [LICENSE](LICENSE).
