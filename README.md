# 个人 AI 简历系统（骨架版）

[English](README.en.md)

经历探索（A）+ 岗位分析（B）。数据与模型解耦，可更换大模型。

```
resume-system/
├── config/
│   ├── models.yaml             # 换模型的开关
│   ├── abilities.yaml          # JD 解析用的能力词表
│   ├── categories.yaml         # 经历板块（实习/项目/竞赛/科研/校园…）
│   └── style.yaml              # 排版（字体/字号/间距/边距/照片）
├── schemas/                    # JSON Schema（校验数据 + 约束模型输出）
├── data/                       # 事实唯一来源（纯 JSON，模型无关；不进公开仓库）
│   ├── raw/                    #   原始材料原件（只读）
│   ├── knowledge_base/         #   长期知识库（A 维护，B 读）
│   └── jobs/                   #   单次求职任务工作区（B 维护，每次投递一份）
├── src/resume_system/
│   ├── llm/                    # 模型抽象层（base + 适配器 + factory）
│   ├── storage/                # 数据访问唯一入口
│   ├── tools/                  # 给模型调的工具（function calling）
│   ├── agents/                 # A / B 流程
│   ├── export/                 # DOCX 渲染器（B 正文 -> 排好版的 Word 简历）
│   └── prompts/                # 提示词（与代码分离）
├── output/                     # 简历成稿输出（.docx / .pdf / .png；不进公开仓库）
├── examples/demo/              # 虚构人物的可运行示例
└── tools/                      # 给你用的维护脚本
```

## 安装

需要 Python ≥ 3.10。

```bash
pip install -e .

# 跑测试
pip install -e ".[dev]"
pytest -q
```

导出 PDF/PNG 需要 LibreOffice（`soffice`），PNG 还需要 `mutool` 或 `pdftoppm`；只出 docx 时不需要。

## 配置

```bash
cp .env.example .env
# 填入 DEEPSEEK_API_KEY
# 按需编辑 config/models.yaml（model / base_url）
```

## 架构与数据流

见 [docs/architecture.md](docs/architecture.md)。一句话：

```
raw ──A──> knowledge_base.json
JD  ──jd_parse──> jd_analysis ──B──> resume_json + 匹配/缺口/rank
                                   └──> docx / pdf / png + 分析 md
```

## 使用

```bash
# 校验：知识库 schema + 跨文件引用 + 任务引用（改完 data/ 都跑这一条）
python tools/validate.py

# 自检：检查同一段经历里的字条是否能力/措辞重合（不调模型）
python -m resume_system.review --task <任务id>

# JD 解析（独立命令）：JD -> 岗位需求 JSON，不生成简历
python -m resume_system.jd_parse --jd jd.txt --out jd_analysis.json

# 跑 A：从 data/raw 读材料，提取经历写入知识库
python -m resume_system.agents.agent_a

# 跑 A 补缺口：读取 data/jobs 里 B 报的缺口，追问补料并写回知识库
python -m resume_system.agents.agent_a --resolve-gaps

# 跑 B：先解析 JD，再输出结构化 JSON（resume_json）+ 分析 md，落盘到 data/jobs/
# 默认会多跑一次 JD 解析；加 --no-jd-parse 可跳过，让 B 自己从 JD 抽要求
python -m resume_system.agents.agent_b --jd jd.txt --job-title "市场调研分析师"
# 加 --export-docx 则生成后自动渲染成排好版的 Word 简历（固定字号；超一页先按相关度删，删完再回填到填满）
python -m resume_system.agents.agent_b --jd jd.txt --job-title "市场调研分析师" --no-interactive --export-docx
# 加 --export-png 则同时导出 PDF + PNG（发 BOSS 直聘用，默认 200 DPI）
python -m resume_system.agents.agent_b --jd jd.txt --job-title "市场调研分析师" --no-interactive --export-png
# 同一个岗位继续改：加 --task <任务id>，结果追加为同一任务的新版本（不新建任务文件）
python -m resume_system.agents.agent_b --task <任务id> --export-docx
# 不传 --jd 则交互粘贴 JD；不传 --no-interactive 则生成后可继续迭代修改

# 或：把已有任务的简历正文单独渲染（--pdf / --png / --dpi 可选）
python -m resume_system.export.docx_export --task <任务id>
python -m resume_system.export.docx_export --task <任务id> --pdf --png --dpi 200
```

> 旧任务若只有 markdown（没有 `resume_json`），新渲染器会明确报错，请用原 JD 重跑一版。

所有成稿统一输出到 **`output/<公司>/<岗位>/`**（公司为空时 `output/<岗位>/`），一次投递一个文件夹，内含 `.docx` / `.pdf` / `.png` 和 `_分析.md`；文件名统一 `<公司>_<岗位>`（公司为空时 `<岗位>`）。手动整理的历史成稿放在 `output/_手动成稿/`。

## 换模型

改 `config/models.yaml` 里的 `provider`/`model` 后重启即可；接入新厂商时在
`src/resume_system/llm/` 写一个适配器并注册到 `factory.py`，其余代码不动。

## 排版与个性化

| 想改什么 | 改哪里 |
|---|---|
| 字体 / 字号 / 颜色 / 边距 / 行距 / 制表位 / 照片高度 | `config/style.yaml` |
| 经历板块类型、标题、顺序 | `config/categories.yaml` |
| JD 解析的能力词表 | `config/abilities.yaml` |
| 个人能力三条固定文案 | `data/profile_blocks.yaml` |
| 补充 few-shot | `data/few_shot.md` |
| 打招呼固定句式 | `data/greeting.md` |
| 通用表达偏好 | `data/preferences.json` |
| 模型 | `config/models.yaml` |

改完重新生成或重新渲染即可，不用动代码。`data/` 下的文件不进公开仓库。

字体要求：默认用「微软雅黑」和「宋体-简」，本机没有会在 Word/LibreOffice 里 fallback。字体有授权限制，不随仓库分发；换字体改 `config/style.yaml` 即可。

## 测试

```bash
pip install -e ".[dev]"
pytest -q
```

CI 在 `.github/workflows/tests.yml`，不依赖模型和 LibreOffice（渲染测试只生成 docx，不数页）。

## 限制

- 版式是为**中文一页简历**设计的：A4、单页、微软雅黑/宋体；多页或英文简历要改 `config/style.yaml` 和裁页逻辑
- 只有 markdown 的旧任务已冻结，新渲染器会明确报错，需要用原 JD 重新生成
- 未接 OCR：扫描件/图片抽不出文字，`tools/ingest.py` 会警告
- JD 解析和正文生成各一次模型调用；`--no-jd-parse` 可省掉前者
- 生成质量依赖模型，系统只保证结构、格式和可核对性

## 文档索引

| 文件 | 作用 |
|---|---|
| `docs/architecture.md` | 架构与数据流 |
| `docs/layout_spec.md` | 排版规范（栏目、字体、字号、顺序） |
| `docs/style_rules.md` | 简历字条语言规则（抽象版，无真实案例） |
| `docs/experience_template.md` | 经历采集固定模板（A 用） |
| `docs/打招呼_写作规则.md` | 打招呼话术规则（BOSS / 邮件 / 内推） |

待补的精确数字/待确认事实记在各条经历的 `open_questions` 里（`data/knowledge_base/knowledge_base.json`）。

## 隐私边界

- `data/`、`output/` 在 `.gitignore` 里：真实知识库、原始材料、照片、任务、成稿**都不会进公开仓库**
- 私有提示词覆盖也放在 `data/`：`profile_blocks.yaml`（个人能力三条）、`few_shot.md`、`greeting.md`、`preferences.json`
- 公开仓库只包含引擎、schema、抽象规则和 `examples/demo/` 的**虚构数据**
- 想让程序读别的数据目录：`RESUME_DATA_DIR=/path/to/private/data`

## Demo

```bash
pip install -e .
RESUME_DATA_DIR=examples/demo/data RESUME_OUTPUT_DIR=/tmp/demo_out \
python -m resume_system.export.docx_export --task demo-render --pdf --png
```

`examples/demo/README.md` 有完整说明；demo 里所有人物、学校、公司、数字均为虚构。

## License

MIT，见 [LICENSE](LICENSE)。
