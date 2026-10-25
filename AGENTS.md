# 维护须知（给所有维护本项目的 Agent / 人）

## 数据唯一来源
- `data/` 是事实底座，纯 JSON，与任何模型/工具无关。
- `data/raw/` 是原始材料原件，永不覆盖、不改写。
- 改完 `data/` 里的数据后必须跑 `python tools/validate.py` 校验（schema + 交叉引用 + 任务引用 + `resume_json`）。
- B 的正文结构以 `schemas/resume.schema.json` 为准；只有 markdown 的旧任务已冻结，需用原 JD 重跑。

## 边界规则（不可违反）
1. **事实优先**：不编造经历、个人贡献、方法、数据、成果。
2. **证据可追溯**：核实状态只能是 `verified` / `pending` / `inferred` 之一，重要事实关联来源。
3. **经历与表达分离**：知识库存事实；针对某个岗位的简历是「表达」，不回写覆盖事实记录。
4. **数据与工具解耦**：不把关键记忆存进任何模型/工具的隐式记忆，只存文件。
5. **反馈分类沉淀**：区分「事实补充 / 通用表达偏好 / 岗位专属修改 / 系统规则变更」，不把局部修改固化为全局规则。

## 换模型
只改 `config/models.yaml` 和 `src/resume_system/llm/`（新增适配器 + 在 factory.py 注册）。
不要动 `agents/`、`tools/`、`data/`——它们只依赖 `llm/base.py` 的接口。
