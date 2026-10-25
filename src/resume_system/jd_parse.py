"""JD 解析：JD 原文 -> 岗位需求 JSON（只解析岗位，不涉及候选人）。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from .config import ROOT
from .llm.factory import get_llm

PROMPT_PATH = ROOT / "src" / "resume_system" / "prompts" / "b_jd.md"
ABILITIES_PATH = ROOT / "config" / "abilities.yaml"
SCHEMA_PATH = ROOT / "schemas" / "jd_analysis.schema.json"


def load_abilities(path: Path = ABILITIES_PATH) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data.get("abilities", [])


def _abilities_text(abilities: list[dict]) -> str:
    lines = []
    for a in abilities:
        aliases = "、".join(a.get("aliases", [])) or "—"
        lines.append(f"- {a['id']} | {a['name']} | 别名：{aliases} | {a.get('definition', '')}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    raw = m.group(1) if m else text
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("输出里没有找到 JSON 对象")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("顶层不是 JSON 对象")
    return data


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def check_jd_analysis(data: dict, jd_text: str, ability_ids: set[str]) -> list[str]:
    """结构以外、必须靠代码核对的部分。返回问题列表。"""
    errors: list[str] = []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    try:
        jsonschema_validate(data, schema)
    except ValidationError as e:
        location = "/".join(str(x) for x in e.absolute_path) or "根"
        return [f"schema: {e.message} @{location}"]

    jd_norm = _norm(jd_text)
    ids = [r.get("id", "") for r in data.get("requirements", [])]
    if len(ids) != len(set(ids)):
        errors.append("requirements 的 id 有重复")

    p0 = 0
    for r in data.get("requirements", []):
        span = r.get("source_span", "")
        if _norm(span) not in jd_norm:
            errors.append(f"{r.get('id')} 的 source_span 在 JD 原文里找不到：{span[:40]}")
        aid = r.get("ability_id", "")
        if r.get("kind") == "能力" and not aid:
            errors.append(f"{r.get('id')} 是能力要求，但缺少 ability_id")
        if aid and aid != "NEW" and aid not in ability_ids:
            errors.append(f"{r.get('id')} 的 ability_id「{aid}」不在词表里")
        if r.get("priority") == "P0":
            p0 += 1
    if p0 > 5:
        errors.append(f"P0 有 {p0} 条，超过上限 5")

    kind_by_id = {r.get("id"): r.get("kind") for r in data.get("requirements", [])}
    req_ids = set(ids)
    for ab in data.get("core_abilities", []):
        for rid in ab.get("requirement_ids", []):
            if rid not in req_ids:
                errors.append(f"核心能力「{ab.get('name')}」引用了不存在的 {rid}")
            elif kind_by_id.get(rid) != "能力":
                errors.append(f"核心能力「{ab.get('name')}」引用了非能力要求 {rid}")
        if ab.get("ability_id") not in ability_ids and ab.get("ability_id") != "NEW":
            errors.append(f"核心能力「{ab.get('name')}」的 ability_id 不在词表里")

    covered = {rid for ab in data.get("core_abilities", []) for rid in ab.get("requirement_ids", [])}
    for r in data.get("requirements", []):
        if r.get("priority") == "P0" and r.get("id") not in covered:
            errors.append(f"{r.get('id')} 是 P0，但没有挂到任何核心能力上")

    return errors


def parse_jd(jd_text: str, llm=None, max_attempts: int = 2) -> tuple[dict, list[str]]:
    """返回 (解析结果, 问题列表)。有问题会回喂一次，让模型自己修。"""
    llm = llm or get_llm()
    abilities = load_abilities()
    ability_ids = {a["id"] for a in abilities}
    system = (
        PROMPT_PATH.read_text(encoding="utf-8")
        + "\n\n## 能力词表（ability_id 只能从这里选）\n\n"
        + _abilities_text(abilities)
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"请解析下面这份 JD，只输出 JSON：\n\n{jd_text}"},
    ]

    last_data: dict = {}
    last_errors: list[str] = []
    for attempt in range(max_attempts):
        resp = llm.chat(messages)
        try:
            data = _extract_json(resp.text)
        except (json.JSONDecodeError, ValueError) as e:
            last_data, last_errors = {}, [f"JSON 解析失败：{e}"]
        else:
            last_data = data
            last_errors = check_jd_analysis(data, jd_text, ability_ids)
            if not last_errors:
                return data, []

        print(f"[解析] 第 {attempt + 1} 次输出有 {len(last_errors)} 个问题，回喂修正", file=sys.stderr)
        messages += [
            {"role": "assistant", "content": resp.text},
            {
                "role": "user",
                "content": (
                    "上次输出有这些问题：\n- " + "\n- ".join(last_errors[:10]) + "\n"
                    "请修正后重新输出完整 JSON。注意：requirements 最多 12 条、core_abilities 最多 5 项，"
                    "source_span 必须是 JD 原文连续片段，ability_id 只能来自词表。"
                ),
            },
        ]
    return last_data, last_errors


def main() -> int:
    parser = argparse.ArgumentParser(description="JD 解析：输出岗位需求 JSON")
    parser.add_argument("--jd", required=True, help="JD 文件路径（txt/md）")
    parser.add_argument("--out", help="结果写到这个 JSON 文件；不传则打印到 stdout")
    args = parser.parse_args()

    jd_text = Path(args.jd).read_text(encoding="utf-8")
    data, errors = parse_jd(jd_text)

    if errors:
        print(f"[警告] {len(errors)} 处需要人工核对：", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"[完成] 已写入 {args.out}")
    else:
        print(text)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
