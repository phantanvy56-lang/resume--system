# 虚构示例（demo）

这里的人物、公司、学校、数字**全部虚构**，只用于演示数据结构和渲染流程。

- `data/knowledge_base/knowledge_base.json`：张同学的知识库
- `data/profile_blocks.yaml`：个人能力三条（固定文案）
- `data/jobs/demo-render.json`：一份已生成好的结构化任务，可直接渲染
- `jd.md`：一份示例 JD

## 跑起来

```bash
pip install -e .

# 只渲染（不调模型）
RESUME_DATA_DIR=examples/demo/data \
RESUME_OUTPUT_DIR=/tmp/demo_out \
python -m resume_system.export.docx_export --task demo-render --pdf --png
```

产物在 `/tmp/demo_out/示例电商/电商运营实习生/`。

## 用 demo 数据跑模型（可选）

```bash
export DEEPSEEK_API_KEY=...
RESUME_DATA_DIR=examples/demo/data \
python -m resume_system.jd_parse --jd examples/demo/jd.md
```

注意：demo 的 `preferences.json`、`profile_blocks.yaml` 都是示例值，换成你自己的数据前不要直接套用。
