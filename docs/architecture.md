# 架构与数据流

## 两条主流程

```
原始材料（txt/md，或 docx/pdf 经 tools/ingest.py 转换）
        │
        ▼
A（你的 agent，按 schemas/knowledge_base.schema.json 产出）
        │
        ▼
data/knowledge_base/knowledge_base.json       事实 / STAR / 能力 / 教育 / 荣誉 / 技能
        │
        ▼
B（你的 agent，按 schemas/resume.schema.json + prompts/b_resume.md 产出）
  ├─ JD 分析      JD ──> 岗位要求（config/abilities.yaml 词表）
  ├─ 匹配         JD + 知识库 ──> matches / gaps / experience_rank
  └─ 生成         resume_json（教育 / 板块 / 字条 / 个人能力）
        │
        ▼
渲染器（export/docx_export.py）
  └─ resume_json + 知识库 + config/style.yaml ──> docx / pdf / png
```

> 本仓库只含「骨架 + 校验 + 渲染」；A / B 两处"动脑"由你自己的 agent 完成（见 docs/agent_usage.md）。

## 目录职责

| 目录 | 职责 |
|---|---|
| `config/` | 排版、板块、能力词表；都是可改配置 |
| `schemas/` | 知识库、任务、简历正文的 JSON Schema |
| `src/resume_system/review.py` | 字条重合检查（同段 / 跨经历） |
| `src/resume_system/checks.py` | 发布前检查（荣誉、教育、板块、P0 覆盖） |
| `src/resume_system/export/` | 结构化正文 -> Word / PDF / PNG |
| `src/resume_system/prompts/` | 提示词（给 agent 参考，与代码分离） |
| `docs/` | 架构、排版、语言、agent 用法等说明 |
| `examples/` | 5 个虚构行业 demo |
| `data/`、`output/` | 本地数据与产物，**不进公开仓库** |

## 数据边界

- 事实只存在 `data/knowledge_base/`，A 维护，B 只读
- 岗位专属表达存在 `data/jobs/<task>.json`，不回写知识库
- 简历正文是结构化 JSON（`schemas/resume.schema.json`），渲染器不再解析 markdown
- `data/` 与 `output/` 由 `.gitignore` 排除；公开仓库只带 demo

## 扩展点

- 加板块：`config/categories.yaml`
- 改版式：`config/style.yaml`
- 加能力词：`config/abilities.yaml`
- 私有文案：`data/profile_blocks.yaml`、`few_shot.md`
