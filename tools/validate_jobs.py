#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from resume_system.config import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
JOBS_DIR = DATA_DIR / "jobs"
SCHEMA_PATH = ROOT / "schemas" / "job_task.schema.json"


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    files = sorted(JOBS_DIR.glob("*.json")) if JOBS_DIR.exists() else []
    if not files:
        print(f"[OK] 无任务文件（目录为空或不存在: {JOBS_DIR}）")
        return 0

    ok = 0
    failed = 0
    for p in files:
        try:
            task = json.loads(p.read_text(encoding="utf-8"))
            jsonschema_validate(task, schema)
        except (json.JSONDecodeError, ValidationError) as e:
            location = "/".join(str(x) for x in getattr(e, "absolute_path", []) or [])
            print(f"[FAIL] {p.name}: {getattr(e, 'message', str(e))}  @{location or '根'}")
            failed += 1
        else:
            gaps_open = sum(1 for g in task.get("gaps", []) if g.get("status") == "open")
            print(
                f"[OK] {p.name}: {task.get('job_title', '?')} | "
                f"{len(task.get('versions', []))} 版 | 缺口 open={gaps_open} | {task.get('status')}"
            )
            ok += 1

    print(f"\n共 {ok + failed} 个任务，通过 {ok}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
