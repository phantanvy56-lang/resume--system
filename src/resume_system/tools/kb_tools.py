from __future__ import annotations

from typing import Callable

ADD_EXPERIENCE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_experience",
        "description": "向知识库写入一条核实过的经历（事实、行动、结果、能力假设、核实状态、来源）。",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "经历标题"},
                "category": {
                    "type": "string",
                    "description": "经历板块 id，取值见 config/categories.yaml（默认 internship/competition/research/campus）",
                },
                "role": {"type": "string", "description": "角色 / 职务（如 研究助理、队长、项目负责人）"},
                "start_date": {"type": "string", "description": "起始时间，精确到月，如 2025-09（可空）"},
                "end_date": {"type": "string", "description": "结束时间，精确到月，如 2026-05；在读/在岗可空"},
                "facts": {"type": "array", "items": {"type": "string"}},
                "actions": {"type": "array", "items": {"type": "string"}},
                "results": {"type": "array", "items": {"type": "string"}},
                "ability_hypotheses": {"type": "array", "items": {"type": "string"}},
                "verification_status": {
                    "type": "string",
                    "enum": ["verified", "pending", "inferred"],
                },
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "open_questions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "category", "facts", "verification_status", "source_refs"],
        },
    },
}

ADD_STAR_STATEMENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_star_statement",
        "description": "写入一条 STAR 描述（结构化四段），标注体现的能力；statement（成品句）由 B 生成，A 不写。",
        "parameters": {
            "type": "object",
            "properties": {
                "ability": {"type": "string", "description": "体现的能力标签"},
                "situation": {"type": "string", "description": "情境 S"},
                "task": {"type": "string", "description": "任务 T"},
                "action": {"type": "string", "description": "行动 A"},
                "result": {"type": "string", "description": "结果 R，尽量量化"},
                "statement": {"type": "string", "description": "可直接上简历的成品句（可选，B 生成）"},
                "source_refs": {"type": "array", "items": {"type": "string"}},
                "status": {
                    "type": "string",
                    "enum": ["verified", "pending", "inferred"],
                },
                "experience_id": {"type": "string"},
            },
            "required": ["ability", "action", "result", "source_refs", "status"],
        },
    },
}

UPDATE_EXPERIENCE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "update_experience",
        "description": "根据用户的新信息更新已有经历（如升级核实状态、补事实）。只传要改的字段。",
        "parameters": {
            "type": "object",
            "properties": {
                "experience_id": {"type": "string"},
                "category": {
                    "type": "string",
                    "description": "经历板块 id，取值见 config/categories.yaml（默认 internship/competition/research/campus）",
                },
                "role": {"type": "string", "description": "角色 / 职务"},
                "start_date": {"type": "string", "description": "起始时间，精确到月"},
                "end_date": {"type": "string", "description": "结束时间，精确到月"},
                "facts": {"type": "array", "items": {"type": "string"}},
                "actions": {"type": "array", "items": {"type": "string"}},
                "results": {"type": "array", "items": {"type": "string"}},
                "ability_hypotheses": {"type": "array", "items": {"type": "string"}},
                "verification_status": {
                    "type": "string",
                    "enum": ["verified", "pending", "inferred"],
                },
                "open_questions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["experience_id"],
        },
    },
}

UPDATE_STAR_STATEMENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "update_star_statement",
        "description": "根据用户的新信息更新已有 STAR 描述。只传要改的字段。",
        "parameters": {
            "type": "object",
            "properties": {
                "statement_id": {"type": "string"},
                "ability": {"type": "string"},
                "situation": {"type": "string"},
                "task": {"type": "string"},
                "action": {"type": "string"},
                "result": {"type": "string"},
                "statement": {"type": "string"},
                "status": {"type": "string", "enum": ["verified", "pending", "inferred"]},
            },
            "required": ["statement_id"],
        },
    },
}

ADD_ABILITY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_ability",
        "description": "写入一个去重后的规范能力，并关联到体现该能力的 STAR 描述。",
        "parameters": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "规范能力标签"},
                "star_statement_refs": {"type": "array", "items": {"type": "string"}, "description": "指向 star_statements 的 id 列表"},
                "description": {"type": "string", "description": "该能力的一两句说明"},
            },
            "required": ["label", "star_statement_refs"],
        },
    },
}

UPDATE_ABILITY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "update_ability",
        "description": "更新已有规范能力（改标签、合并、增删关联的 STAR）。只传要改的字段。",
        "parameters": {
            "type": "object",
            "properties": {
                "ability_id": {"type": "string"},
                "label": {"type": "string"},
                "star_statement_refs": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"},
            },
            "required": ["ability_id"],
        },
    },
}

ASK_USER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "ask_user",
        "description": "当信息缺口无法从材料推断时，向用户提出具体问题（优先给几种详细猜测让用户选）。",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
}

TOOL_SCHEMAS = [
    ADD_EXPERIENCE_SCHEMA,
    ADD_STAR_STATEMENT_SCHEMA,
    UPDATE_EXPERIENCE_SCHEMA,
    UPDATE_STAR_STATEMENT_SCHEMA,
    ADD_ABILITY_SCHEMA,
    UPDATE_ABILITY_SCHEMA,
    ASK_USER_SCHEMA,
]


def make_executors(store, interactive: bool = True) -> dict[str, Callable]:
    """把工具定义绑定到知识库实例，返回 name -> 执行函数。"""

    def add_experience(**kwargs) -> str:
        exp, action = store.upsert_experience(kwargs)
        label = "已更新经历" if action == "updated" else "已写入经历"
        return f"{label}: {exp['id']} - {exp['title']}（重跑不会重复）"

    def add_star_statement(**kwargs) -> str:
        stmt, action = store.upsert_star_statement(kwargs)
        label = "已更新 STAR" if action == "updated" else "已写入 STAR"
        return f"{label}: {stmt['id']} - {stmt['ability']}（同经历同能力只保留一条）"

    def update_experience(experience_id: str, **fields) -> str:
        exp = store.update_experience(experience_id, **fields)
        return f"已更新经历: {exp['id']} - {exp['title']}"

    def update_star_statement(statement_id: str, **fields) -> str:
        stmt = store.update_star_statement(statement_id, **fields)
        return f"已更新 STAR 描述: {stmt['id']} - {stmt['ability']}"

    def add_ability(**kwargs) -> str:
        ab, action = store.upsert_ability(kwargs)
        label = "已更新能力" if action == "updated" else "已写入能力"
        return f"{label}: {ab['id']} - {ab['label']}（同标签只保留一条）"

    def update_ability(ability_id: str, **fields) -> str:
        ab = store.update_ability(ability_id, **fields)
        return f"已更新能力: {ab['id']} - {ab['label']}"

    def ask_user(question: str) -> str:
        print(f"\n[问题] {question}")
        if interactive:
            return input("你的回答（回车跳过）：").strip() or "(用户未回答)"
        return "问题已提交给用户，等待回答。"

    return {
        "add_experience": add_experience,
        "add_star_statement": add_star_statement,
        "update_experience": update_experience,
        "update_star_statement": update_star_statement,
        "add_ability": add_ability,
        "update_ability": update_ability,
        "ask_user": ask_user,
    }
