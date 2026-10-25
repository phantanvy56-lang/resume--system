#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from resume_system.config import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
KB_PATH = DATA_DIR / "knowledge_base" / "knowledge_base.json"
SCHEMA_PATH = ROOT / "schemas" / "knowledge_base.schema.json"


def main() -> int:
    if not KB_PATH.exists():
        print(f"未找到知识库文件: {KB_PATH}")
        return 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))

    try:
        jsonschema_validate(kb, schema)
    except ValidationError as e:
        location = "/".join(str(p) for p in e.absolute_path)
        print(f"[FAIL] 校验失败：{e.message}")
        print(f"       位置：{location or '(根)'}")
        return 1

    print(
        f"[OK] 校验通过：{len(kb.get('experiences', []))} 条经历，"
        f"{len(kb.get('star_statements', []))} 条 STAR 证据，"
        f"{len(kb.get('abilities', []))} 项能力"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
