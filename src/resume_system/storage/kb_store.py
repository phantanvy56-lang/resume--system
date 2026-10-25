from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from jsonschema import validate as jsonschema_validate

_LIST_FIELDS = ("facts", "actions", "results", "ability_hypotheses", "open_questions", "source_refs")
_STATUS_RANK = {"pending": 0, "inferred": 1, "verified": 2}


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _experience_key(exp: dict) -> tuple[str, str]:
    """幂等键：板块 + 标题里「·」之前的部分。"""
    return (exp.get("category", ""), _norm((exp.get("title") or "").split("·")[0]))


def _star_key(stmt: dict) -> tuple[str, str]:
    """幂等键：所属经历 + 能力。同一经历同一能力只保留一条。"""
    return (stmt.get("experience_id", ""), _norm(stmt.get("ability", "")))


def _merge_entry(existing: dict, incoming: dict) -> None:
    """把新数据并入已有条目：列表取并集，核实状态取更高，其余字段覆盖。"""
    for k, v in incoming.items():
        if k == "id":
            continue
        if k in _LIST_FIELDS and isinstance(v, list):
            cur = existing.get(k) or []
            for item in v:
                if item not in cur:
                    cur.append(item)
            existing[k] = cur
        elif k == "verification_status":
            if _STATUS_RANK.get(v, 0) > _STATUS_RANK.get(existing.get(k), 0):
                existing[k] = v
        elif k == "status":
            if _STATUS_RANK.get(v, 0) > _STATUS_RANK.get(existing.get(k), 0):
                existing[k] = v
        else:
            existing[k] = v


class KBStore:
    """知识库访问的唯一入口。所有写入都先过 schema 校验。"""

    def __init__(self, kb_path: Path, schema_path: Path):
        self.kb_path = kb_path
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def load(self) -> dict:
        if not self.kb_path.exists():
            return {
                "version": "0.1.0",
                "experiences": [],
                "star_statements": [],
                "abilities": [],
                "education": [],
                "honors": [],
                "skills": [],
                "profile": {"name": ""},
            }
        kb = json.loads(self.kb_path.read_text(encoding="utf-8"))
        # 兼容旧文件：缺失的新字段补空
        kb.setdefault("abilities", [])
        kb.setdefault("education", [])
        kb.setdefault("honors", [])
        kb.setdefault("skills", [])
        kb.setdefault("profile", {"name": ""})
        return kb

    def save(self, kb: dict) -> None:
        self.validate(kb)
        self.kb_path.parent.mkdir(parents=True, exist_ok=True)
        self.kb_path.write_text(
            json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def validate(self, kb: dict) -> None:
        jsonschema_validate(kb, self.schema)

    def add_experience(self, experience: dict) -> dict:
        return self.upsert_experience(experience)[0]

    def upsert_experience(self, experience: dict) -> tuple[dict, str]:
        """存在（同板块 + 同主标题）就合并更新，否则新增。返回 (条目, created|updated)。"""
        kb = self.load()
        key = _experience_key(experience)
        for exp in kb["experiences"]:
            if _experience_key(exp) == key:
                _merge_entry(exp, experience)
                self.save(kb)
                return exp, "updated"
        if not experience.get("id"):
            experience["id"] = str(uuid.uuid4())
        kb["experiences"].append(experience)
        self.save(kb)
        return experience, "created"

    def add_star_statement(self, statement: dict) -> dict:
        return self.upsert_star_statement(statement)[0]

    def upsert_star_statement(self, statement: dict) -> tuple[dict, str]:
        """同经历 + 同能力只保留一条；存在则合并。"""
        kb = self.load()
        key = _star_key(statement)
        for stmt in kb["star_statements"]:
            if _star_key(stmt) == key:
                _merge_entry(stmt, statement)
                self.save(kb)
                return stmt, "updated"
        if not statement.get("id"):
            statement["id"] = str(uuid.uuid4())
        kb["star_statements"].append(statement)
        self.save(kb)
        return statement, "created"

    def add_ability(self, ability: dict) -> dict:
        return self.upsert_ability(ability)[0]

    def upsert_ability(self, ability: dict) -> tuple[dict, str]:
        """同标签的能力合并，STAR 引用取并集。"""
        kb = self.load()
        label = _norm(ability.get("label", ""))
        for ab in kb["abilities"]:
            if _norm(ab.get("label", "")) == label:
                _merge_entry(ab, ability)
                self.save(kb)
                return ab, "updated"
        if not ability.get("id"):
            ability["id"] = str(uuid.uuid4())
        kb["abilities"].append(ability)
        self.save(kb)
        return ability, "created"

    def update_experience(self, experience_id: str, **fields) -> dict:
        kb = self.load()
        for exp in kb["experiences"]:
            if exp.get("id") == experience_id:
                for k, v in fields.items():
                    if k != "id":
                        exp[k] = v
                self.save(kb)
                return exp
        raise ValueError(f"未找到经历: {experience_id}")

    def update_star_statement(self, statement_id: str, **fields) -> dict:
        kb = self.load()
        for stmt in kb["star_statements"]:
            if stmt.get("id") == statement_id:
                for k, v in fields.items():
                    if k != "id":
                        stmt[k] = v
                self.save(kb)
                return stmt
        raise ValueError(f"未找到 STAR 描述: {statement_id}")

    def update_ability(self, ability_id: str, **fields) -> dict:
        kb = self.load()
        for ab in kb["abilities"]:
            if ab.get("id") == ability_id:
                for k, v in fields.items():
                    if k != "id":
                        ab[k] = v
                self.save(kb)
                return ab
        raise ValueError(f"未找到能力: {ability_id}")
