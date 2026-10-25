# 虚构 Demo

这里的五个人物、学校、公司、数字**全部虚构**，只用于演示不同行业的能力结构。

| 目录 | 行业 | 岗位 | 参考的公开 JD |
|---|---|---|---|
| `demo/` | 电商运营 | 电商运营实习生 | 虚构示例 |
| `demo-finance/` | 金融 / 行研 | 行业研究实习生 | [中金 权益研究](https://www.deizao.net/index/index/shixixq/jobid/117306) |
| `demo-consulting/` | 管理咨询 | 战略咨询 PTA | [罗兰贝格](https://www.wondercv.com/xiaozhao/roland-berger-2026-fall-pta-11494-aefb47/)、[贝恩](https://www.wondercv.com/xiaozhao/bain-greater-china-2026-2027-internship-19393-29f604/)、[麦肯锡](https://career.bnuzh.edu.cn/index.php/web/Index/jobs-brief-detail?id=T1UXSPY) |
| `demo-data/` | 数据分析 | 数据分析实习生 | [众安保险](https://www.deizao.net/index/index/shixixq/jobid/285758) |
| `demo-law/` | 法务 | 法务实习生 | [迪卡侬 法务](https://www.deizao.cn/index/index/shixixq/jobid/260541) |

岗位要求参考上述公开 JD 的能力结构；人物经历、雇主和所有数字均为虚构，与这些公司无关。

## 渲染

```bash
RESUME_DATA_DIR=examples/demo-finance/data \
RESUME_OUTPUT_DIR=/tmp/demo_finance \
python -m resume_system.export.docx_export --task finance-render --pdf --png
```

把 `demo-finance` 换成 `demo-consulting`、`demo-data`、`demo-law`，任务 id 分别是
`consulting-render`、`data-render`、`law-render`。

## 重新生成

改动人物设定后：

```bash
python examples/build_demos.py
```

生成脚本在 `examples/build_demos.py`，人物设定在 `examples/demo_specs.py`。
