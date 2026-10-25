# 架构与数据流

## 两条主流程

```
原始材料（txt/md，或 docx/pdf 经 tools/ingest.py 转换）
        │
        ▼
A（agent_a）── 工具调用 ──> data/knowledge_base/knowledge_base.json
                              事实 / STAR / 能力 / 教育 / 荣誉 / 技能
        │
        ▼
B（agent_b）
  ├─ jd_parse      JD ──> jd_analysis（要求 / 能力 / 优先级 / 待核实）
  ├─ 匹配          JD + 知识库 ──> matches / gaps / experience_rank
  └─ 生成          resume_json（教育 / 板块 / 字条 / 个人能力）+ greeting
        │
        ▼
渲染器（export/docx_export.py）
  └─ resume_json + 知识库 + config/style.yaml ──> docx / pdf / png
  分析 md 由数据生成：output/<公司>/<岗位>/<公司>_<岗位>_分析.md
```

## 目录职责

| 目录 | 职责 |
|---|---|
| `config/` | 模型、排版、板块、能力词表；都是可改配置 |
| `schemas/` | 知识库、任务、简历正文、JD 解析的 JSON Schema |
| `src/resume_system/llm/` | 模型抽象层，换模型只改这里 + models.yaml |
| `src/resume_system/agents/` | A 探索、B 生成 |
| `src/resume_system/tools/` | 给 A 用的 function calling 工具 |
| `src/resume_system/storage/` | 数据访问唯一入口（知识库 / 任务） |
| `src/resume_system/review.py` | 字条重合检查（同段 / 跨经历） |
| `src/resume_system/checks.py` | 发布前检查（荣誉、教育、板块、P0 覆盖） |
| `src/resume_system/export/` | 结构化正文 -> Word / PDF / PNG |
| `docs/` | 排版、语言、打招呼、架构等说明 |
| `examples/` | 5 个虚构行业 demo + 生成脚本 |
| `data/`、`output/` | 本地数据与产物，**不进公开仓库** |

## 数据边界

- 事实只存在 `data/knowledge_base/`，A 维护，B 只读
- 岗位专属表达存在 `data/jobs/<task>.json`，不回写知识库
- 简历正文是结构化 JSON（`schemas/resume.schema.json`），渲染器不再解析 markdown
- `data/` 与 `output/` 由 `.gitignore` 排除；公开仓库只带 demo

## 扩展点

- 换模型：`config/models.yaml` + `llm/` 新增适配器
- 加板块：`config/categories.yaml`
- 改版式：`config/style.yaml`
- 加能力词：`config/abilities.yaml`
- 私有文案：`data/profile_blocks.yaml`、`few_shot.md`、`greeting.md`
