# Agent 用法（零 API key）

本文写给**已经在用 AI agent 的人**（Claude Code、Cursor、DSH 等），或想用自己的模型跑通这条流程的人。

核心原则：**这条流程不需要你配置任何模型 API key**。真正"动脑"的两步——A 提取经历、B 生成简历——由你自己的 agent / 模型完成；本仓库只提供**骨架（schema）+ 校验器 + 渲染器**，这些是纯 Python，零 key。

## 谁做哪部分

| 步骤 | 谁来做 | 需要 key 吗 |
|---|---|---|
| 读材料、提取事实/STAR → `knowledge_base.json` | 你的 agent（自己的模型） | 否 |
| 读 JD + 知识库 → 简历正文 + 任务文件 | 你的 agent（自己的模型） | 否 |
| schema / 引用 / 正文结构校验 | `python tools/validate.py` | 否 |
| 查重 | `python -m resume_system.review --task <id>` | 否 |
| 渲染 docx / pdf / png | `python -m resume_system.export.docx_export` | 否（PDF/PNG 需 LibreOffice） |

## 数据与工具的边界

- 事实只存 `data/knowledge_base/knowledge_base.json`（schema 见 `schemas/knowledge_base.schema.json`）。
- 岗位专属表达存 `data/jobs/<任务id>.json`（schema 见 `schemas/job_task.schema.json`），不覆盖知识库。
- 简历正文是结构化 JSON（`schemas/resume.schema.json`），渲染器不解析 markdown。
- 硬规则见 `AGENTS.md`：事实优先、证据可溯源、经历与表达分离、不编造。

## 完整流程

### 0. 准备原始材料

```bash
python tools/ingest.py 材料.docx 材料.pdf   # 抽成纯文本进 data/raw/（零 key）
```

### 1. A：提取经历 → 知识库

用你自己的模型读 `data/raw/`，按 `schemas/knowledge_base.schema.json` 产出 `data/knowledge_base/knowledge_base.json`。

- 采集口径看 `docs/experience_template.md`（工作块五要素：能力标签 / 动作 / 方法工具 / 量化数字 / 个人贡献）。
- 能力去重规则看 `src/resume_system/prompts/a_explore.md`。
- 核实状态只写 `verified` / `pending` / `inferred`；`action` / `result` 必须能溯源到 `source_refs`。

写完后校验：

```bash
python tools/validate.py
```

### 2. B：生成简历 → 任务文件

用你自己的模型读 JD + 知识库，产出 `data/jobs/<任务id>.json`：

- 顶层字段按 `schemas/job_task.schema.json`（至少 `id` / `job_title` / `jd_text` / `requirements` / `matches` / `selected_experience_ids` / `gaps` / `versions` / `preferences` / `status` / `created_at` / `updated_at`）；
- `versions[0].resume_json` 按 `schemas/resume.schema.json`（`header` / `education` / `sections` / `abilities`）。

生成口径看 `src/resume_system/prompts/b_resume.md` + `b_style.md`（能力短语、力度词、价值收尾、bold 规则）。

`validate.py` 会强制检查，所以注意：

- 每段经历只能放在它 `category` 对应的板块标题下（见 `config/categories.yaml`）；
- `experience_id` / `ability_id` / `star_statement_ids` 必须来自知识库真实 id，拿不准写 `""` 或 `[]`，绝不编造；
- 每条 bullet 的 `bold` 词必须原样出现在 `desc` 里。

写完后再次校验：

```bash
python tools/validate.py
```

### 3. 自检 + 渲染

```bash
python -m resume_system.review --task <任务id>   # 字条重合检查（零 key）

RESUME_OUTPUT_DIR=/tmp/out \
python -m resume_system.export.docx_export --task <任务id> --pdf --png
```

产物在 `output/<公司>/<岗位>/`。

## 换数据目录

```bash
RESUME_DATA_DIR=/path/to/private/data   # 指向你自己的私有 data/
```
