"""四个虚构行业 demo 的人物设定（全部虚构，仅参考公开 JD 的能力结构）。"""

SOURCES = {
    "finance": """# 来源

- 中金公司 项目实习生-权益研究岗（J19225）岗位信息（得早学就创转载）：
  https://www.deizao.net/index/index/shixixq/jobid/117306

说明：本 demo 的人物、学校、公司、数字全部虚构；岗位职责与能力要求参考上述公开 JD 的表述整理。
""",
    "consulting": """# 来源

- 罗兰贝格 2026 秋季 PTA 招聘信息（超级简历）：
  https://www.wondercv.com/xiaozhao/roland-berger-2026-fall-pta-11494-aefb47/
- 贝恩公司 2026–2027 实习生招聘（超级简历）：
  https://www.wondercv.com/xiaozhao/bain-greater-china-2026-2027-internship-19393-29f604/
- 麦肯锡中国区 2027 校园招聘（北师大珠海校区就业中心）：
  https://career.bnuzh.edu.cn/index.php/web/Index/jobs-brief-detail?id=T1UXSPY

说明：本 demo 的人物、学校、公司、数字全部虚构；能力要求参考上述公开 JD 整理。
""",
    "data": """# 来源

- 众安保险 数据分析实习生岗位信息（得早学就创转载）：
  https://www.deizao.net/index/index/shixixq/jobid/285758

说明：本 demo 的人物、学校、公司、数字全部虚构；岗位职责与能力要求参考上述公开 JD 整理。
""",
    "law": """# 来源

- 迪卡侬中国 法律部门实习生岗位信息（得早学就创转载）：
  https://www.deizao.cn/index/index/shixixq/jobid/260541

说明：本 demo 的人物、学校、公司、数字全部虚构；岗位职责与能力要求参考上述公开 JD 整理。
""",
}


def _exp(eid, title, category, role, start, end, facts, actions, results, abilities):
    return {
        "id": eid,
        "title": title,
        "category": category,
        "role": role,
        "start_date": start,
        "end_date": end,
        "facts": facts,
        "actions": actions,
        "results": results,
        "ability_hypotheses": abilities,
        "verification_status": "verified",
        "source_refs": ["demo"],
        "open_questions": [],
    }


def _star(sid, eid, ability, situation, task, action, result):
    return {
        "id": sid,
        "experience_id": eid,
        "ability": ability,
        "situation": situation,
        "task": task,
        "action": action,
        "result": result,
        "source_refs": ["demo"],
        "status": "verified",
    }


def _edu(school, major, degree, start, end, gpa, rank, courses, note=""):
    return {
        "school": school,
        "major": major,
        "degree": degree,
        "start_date": start,
        "end_date": end,
        "gpa": gpa,
        "gpa_scale": 4.0,
        "rank": rank,
        "courses": [{"name": n, "grade": g} for n, g in courses],
        "english": [{"name": "CET-6", "score": 610}],
        "note": note,
    }


FINANCE = {
    "id": "finance",
    "name": "陈亦舟",
    "education": _edu(
        "示例财经大学", "金融学", "硕士", "2024-09", "2027-06", 3.9, "前 5%",
        [("公司金融", "A"), ("投资学", "A"), ("计量经济学", "A-")],
    ),
    "honors": [
        {"title": "校级一等奖学金", "year": "2025", "level": "校级", "detail": "前 5%"},
        {"title": "校级案例大赛", "year": "2024", "level": "校级", "detail": "二等奖"},
    ],
    "skills": [
        {"category": "数据终端", "items": ["Wind", "Excel（数据透视表）"]},
        {"category": "编程与建模", "items": ["Python（pandas）", "DCF / 可比公司估值"]},
    ],
    "experiences": [
        _exp(
            "fin-exp-1", "示例证券研究所 · 行业研究实习生", "internship", "行业研究实习生",
            "2025-07", "2025-12",
            ["跟踪 3 家消费公司财报与经营数据", "维护 200+ 条行业数据库", "搭建 DCF 与可比公司估值模型", "撰写 2 篇行业跟踪报告"],
            ["跟踪财报与经营数据", "维护行业数据库", "搭建估值模型", "撰写行业报告"],
            ["2 篇报告被团队采用", "覆盖 3 家公司"],
            ["财务分析与估值", "行业研究"],
        ),
        _exp(
            "fin-exp-2", "示例消费基金 · 研究助理", "internship", "研究助理",
            "2026-01", "2026-05",
            ["整理 50 家可比公司数据", "参与 10 场专家访谈并整理纪要", "输出 1 份赛道复盘"],
            ["整理可比公司数据", "参与专家访谈", "输出赛道复盘"],
            ["1 份复盘进入组合讨论"],
            ["行业研究", "专家访谈"],
        ),
    ],
    "stars": [
        _star("fin-star-1", "fin-exp-1", "财务分析与估值", "覆盖消费行业", "给出估值判断",
              "搭建 DCF 与可比公司模型，跟踪 3 家公司财报", "输出估值区间与关键假设"),
        _star("fin-star-2", "fin-exp-1", "行业研究", "行业跟踪", "撰写跟踪报告",
              "维护 200+ 条行业数据库，整理供需与竞争格局", "2 篇报告被团队采用"),
        _star("fin-star-3", "fin-exp-2", "行业研究", "赛道复盘", "提炼关键信号",
              "参与 10 场专家访谈并整理纪要", "输出 1 份赛道复盘"),
    ],
    "abilities": [
        {"id": "fin-ab-1", "label": "财务分析与估值", "description": "财报分析、DCF 与可比公司估值", "star_statement_refs": ["fin-star-1"]},
        {"id": "fin-ab-2", "label": "行业研究", "description": "行业数据、竞争格局与专家访谈", "star_statement_refs": ["fin-star-2", "fin-star-3"]},
    ],
    "profile_blocks": [
        {"label": "财务与估值", "text": "熟练使用 Wind、Excel 搭建 DCF 与可比公司估值模型，能跟踪财报与经营数据并输出估值判断。", "bold": ["Wind", "DCF", "估值判断"]},
        {"label": "行业研究", "text": "能维护行业数据库、整理竞争格局，并通过专家访谈提炼渠道与库存信号。", "bold": ["行业数据库", "专家访谈"]},
        {"label": "语言能力", "text": "CET-6 610 分，可阅读英文财报、研报与行业资料。", "bold": ["英文财报"]},
    ],
    "resume": {
        "实习经历": [
            ("fin-exp-1", [
                {"label": "财务分析与估值", "desc": "搭建 DCF 与可比公司估值模型，跟踪 3 家消费公司财报与经营数据；输出估值区间与关键假设，支撑团队投资判断。", "bold": ["DCF", "3 家", "估值区间"]},
                {"label": "行业数据与报告", "desc": "维护 200+ 条行业数据库，整理 2 篇行业跟踪报告；覆盖供需、竞争格局与政策变化，为组合调整提供依据。", "bold": ["200+ 条", "2 篇"]},
            ]),
            ("fin-exp-2", [
                {"label": "专家访谈与复盘", "desc": "参与 10 场专家访谈并整理纪要，提炼渠道与库存关键信号；输出 1 份赛道复盘，支撑持仓讨论。", "bold": ["10 场", "1 份"]},
            ]),
        ]
    },
    "job": {
        "title": "行业研究实习生",
        "company": "示例证券",
        "availability": "每周到岗 4 天，可连续实习 3 个月以上",
        "jd": """行业研究实习生（示例证券，虚构）

岗位职责
1. 跟踪重点公司财报与经营情况，整理行业与公司基础数据；
2. 协助行业与个股基本面研究，参与估值与报告撰写。

任职要求
1. 研究生在读，金融相关专业；
2. 具备基础的行业与公司分析能力，熟练使用 Wind/Excel；
3. 每周至少出勤 3 天，可连续实习 3 个月以上。
""",
        "matches": [
            {"requirement": "跟踪财报与经营情况", "ability_id": "fin-ab-1", "ability_label": "财务分析与估值", "star_statement_ids": ["fin-star-1"], "match_level": "强", "reason": "实习中持续跟踪 3 家公司财报并搭建估值模型"},
            {"requirement": "行业与公司基础数据整理", "ability_id": "fin-ab-2", "ability_label": "行业研究", "star_statement_ids": ["fin-star-2"], "match_level": "强", "reason": "维护 200+ 条行业数据库并撰写跟踪报告"},
            {"requirement": "协助基本面研究", "ability_id": "fin-ab-2", "ability_label": "行业研究", "star_statement_ids": ["fin-star-3"], "match_level": "中", "reason": "通过 10 场专家访谈支撑赛道复盘"},
        ],
    },
    "sources": SOURCES["finance"],
}

CONSULTING = {
    "id": "consulting",
    "name": "林知远",
    "education": _edu(
        "示例大学", "管理学", "本科", "2023-09", "2027-06", 3.8, "前 10%",
        [("战略管理", "A"), ("运营管理", "A"), ("统计学", "A-")],
    ),
    "honors": [
        {"title": "校级优秀学生干部", "year": "2025", "level": "校级", "detail": ""},
        {"title": "校级案例竞赛", "year": "2025", "level": "校级", "detail": "冠军"},
    ],
    "skills": [
        {"category": "办公工具", "items": ["Excel（建模）", "PowerPoint"]},
        {"category": "研究方法", "items": ["桌面研究", "专家访谈", "市场测算"]},
    ],
    "experiences": [
        _exp(
            "con-exp-1", "示例咨询 · 兼职项目助理（PTA）", "internship", "PTA",
            "2025-09", "2026-02",
            ["完成 30 份桌面研究与竞品扫描", "整理 12 场专家访谈纪要", "搭建 Excel 市场测算模型", "输出 20 页汇报材料"],
            ["桌面研究与竞品扫描", "整理访谈纪要", "搭建测算模型", "制作汇报材料"],
            ["支撑 2 个项目的客户汇报"],
            ["结构化问题拆解", "访谈与桌面研究", "汇报呈现"],
        ),
        _exp(
            "con-exp-2", "校级案例竞赛 · 队长", "competition", "队长",
            "2025-03", "2025-06",
            ["带队拆解 1 个消费品增长案例", "搭建 3 年收入测算", "完成 15 页英文汇报"],
            ["拆解问题", "搭建测算", "英文汇报"],
            ["校赛冠军"],
            ["结构化问题拆解", "汇报呈现"],
        ),
    ],
    "stars": [
        _star("con-star-1", "con-exp-1", "结构化问题拆解", "项目启动", "拆解客户增长问题",
              "用议题树拆解 3 层问题，完成 30 份桌面研究", "支撑项目组确定分析框架"),
        _star("con-star-2", "con-exp-1", "访谈与桌面研究", "专家访谈", "提炼关键信息",
              "整理 12 场访谈纪要，归纳渠道与价格带信号", "形成 1 份访谈洞察"),
        _star("con-star-3", "con-exp-2", "汇报呈现", "案例竞赛", "完成英文汇报",
              "搭建 3 年收入测算并制作 15 页英文材料", "获得校赛冠军"),
    ],
    "abilities": [
        {"id": "con-ab-1", "label": "结构化问题拆解", "description": "议题树、假设驱动、市场测算", "star_statement_refs": ["con-star-1"]},
        {"id": "con-ab-2", "label": "访谈与桌面研究", "description": "专家访谈、竞品与行业研究", "star_statement_refs": ["con-star-2"]},
        {"id": "con-ab-3", "label": "汇报呈现", "description": "PPT 与英文汇报", "star_statement_refs": ["con-star-3"]},
    ],
    "profile_blocks": [
        {"label": "结构化问题拆解", "text": "习惯用议题树拆解问题，能把模糊目标拆成可验证假设，并用 Excel 搭建市场测算。", "bold": ["议题树", "市场测算"]},
        {"label": "访谈与桌面研究", "text": "完成 30 份桌面研究与 12 场专家访谈纪要，能快速提炼渠道、价格带与竞争信号。", "bold": ["30 份", "12 场"]},
        {"label": "中英文汇报", "text": "能独立制作 15 页以上的中英文汇报材料，CET-6 610 分。", "bold": ["中英文汇报", "CET-6 610"]},
    ],
    "resume": {
        "实习经历": [
            ("con-exp-1", [
                {"label": "结构化问题拆解", "desc": "用议题树拆解客户增长问题，完成 30 份桌面研究与竞品扫描；搭建 Excel 市场测算模型，支撑项目组确定分析框架。", "bold": ["议题树", "30 份", "市场测算"]},
                {"label": "访谈与汇报", "desc": "整理 12 场专家访谈纪要，归纳渠道与价格带信号；输出 20 页汇报材料，支撑 2 个项目的客户汇报。", "bold": ["12 场", "20 页"]},
            ])
        ],
        "竞赛经历": [
            ("con-exp-2", [
                {"label": "案例分析与汇报", "desc": "带队拆解消费品增长案例，搭建 3 年收入测算并完成 15 页英文汇报；获得校赛冠军。", "bold": ["3 年", "15 页", "冠军"]},
            ])
        ],
    },
    "job": {
        "title": "战略咨询 PTA",
        "company": "示例咨询",
        "availability": "每周到岗 3 天，可连续实习 12 周以上",
        "jd": """战略咨询 PTA（示例咨询，虚构）

工作内容
1. 参与咨询项目，协助桌面研究、竞品扫描与数据整理；
2. 整理专家访谈纪要，提炼关键信息；
3. 协助搭建 Excel 测算模型、制作汇报材料。

任职要求
1. 本科或硕士在读，专业不限；
2. 较强的逻辑分析与问题解决能力；
3. 中英文口头与书面表达流利；
4. 每周至少 3 个工作日，连续 12 周以上。
""",
        "matches": [
            {"requirement": "逻辑分析与问题解决", "ability_id": "con-ab-1", "ability_label": "结构化问题拆解", "star_statement_ids": ["con-star-1"], "match_level": "强", "reason": "用议题树拆解增长问题并搭建测算"},
            {"requirement": "桌面研究与访谈", "ability_id": "con-ab-2", "ability_label": "访谈与桌面研究", "star_statement_ids": ["con-star-2"], "match_level": "强", "reason": "30 份桌面研究、12 场访谈纪要"},
            {"requirement": "中英文汇报", "ability_id": "con-ab-3", "ability_label": "汇报呈现", "star_statement_ids": ["con-star-3"], "match_level": "强", "reason": "15 页英文案例汇报获校赛冠军"},
        ],
    },
    "sources": SOURCES["consulting"],
}

DATA = {
    "id": "data",
    "name": "周予安",
    "education": _edu(
        "示例大学", "统计学", "硕士", "2024-09", "2027-06", 3.9, "前 5%",
        [("回归分析", "A"), ("机器学习", "A"), ("数据库原理", "A")],
    ),
    "honors": [
        {"title": "校级一等奖学金", "year": "2025", "level": "校级", "detail": "前 5%"},
        {"title": "校级数据竞赛", "year": "2025", "level": "校级", "detail": "一等奖"},
    ],
    "skills": [
        {"category": "数据处理", "items": ["SQL", "Python（pandas）", "Excel"]},
        {"category": "分析建模", "items": ["回归分析", "AB 测试", "指标体系"]},
    ],
    "experiences": [
        _exp(
            "data-exp-1", "示例保险科技 · 数据分析实习生", "internship", "数据分析实习生",
            "2025-07", "2025-12",
            ["用 SQL 取数并清洗 10 万+ 条保单数据", "搭建 6 项风控指标看板", "设计并分析 1 组 AB 测试", "输出 2 份策略复盘"],
            ["SQL 取数与清洗", "搭建指标看板", "AB 测试", "策略复盘"],
            ["异常识别提前 2 天", "策略调整覆盖 3 个客群"],
            ["SQL 与指标", "统计建模", "业务分析"],
        ),
        _exp(
            "data-exp-2", "校级数据竞赛 · 队长", "competition", "队长",
            "2025-03", "2025-06",
            ["带队完成 1 个用户流失预测项目", "清洗 5 万条行为数据", "用逻辑回归与树模型对比"],
            ["数据清洗", "特征工程", "模型对比"],
            ["校赛一等奖"],
            ["统计建模", "业务分析"],
        ),
    ],
    "stars": [
        _star("data-star-1", "data-exp-1", "SQL 与指标", "风控数据接入", "建立监控指标",
              "用 SQL 清洗 10 万+ 条保单数据，搭建 6 项指标看板", "异常识别提前 2 天"),
        _star("data-star-2", "data-exp-1", "统计建模", "策略验证", "评估策略效果",
              "设计 AB 测试并做显著性检验", "策略调整覆盖 3 个客群"),
        _star("data-star-3", "data-exp-2", "统计建模", "用户流失预测", "提升预测效果",
              "对比逻辑回归与树模型，完成特征工程", "校赛一等奖"),
    ],
    "abilities": [
        {"id": "data-ab-1", "label": "SQL 与指标", "description": "取数、清洗、指标体系与看板", "star_statement_refs": ["data-star-1"]},
        {"id": "data-ab-2", "label": "统计建模", "description": "回归、AB 测试、模型对比", "star_statement_refs": ["data-star-2", "data-star-3"]},
        {"id": "data-ab-3", "label": "业务分析", "description": "异常归因与策略建议", "star_statement_refs": ["data-star-2"]},
    ],
    "profile_blocks": [
        {"label": "SQL 与数据处理", "text": "熟练使用 SQL 与 Python（pandas）取数、清洗与分析，能独立搭建指标看板。", "bold": ["SQL", "Python", "指标看板"]},
        {"label": "统计建模", "text": "掌握回归、AB 测试与模型对比，能用显著性检验判断策略效果。", "bold": ["回归", "AB 测试"]},
        {"label": "业务分析", "text": "能从指标异常出发做归因，输出可落地的策略建议。", "bold": ["指标异常", "策略建议"]},
    ],
    "resume": {
        "实习经历": [
            ("data-exp-1", [
                {"label": "SQL 取数与指标看板", "desc": "用 SQL 清洗 10 万+ 条保单数据，搭建 6 项风控指标看板；异常识别提前 2 天，支撑策略调整。", "bold": ["10 万+ 条", "6 项", "提前 2 天"]},
                {"label": "AB 测试与策略复盘", "desc": "设计 1 组 AB 测试并完成显著性检验，输出 2 份策略复盘；策略调整覆盖 3 个客群。", "bold": ["AB 测试", "2 份", "3 个客群"]},
            ])
        ],
        "竞赛经历": [
            ("data-exp-2", [
                {"label": "用户流失预测", "desc": "带队清洗 5 万条行为数据，对比逻辑回归与树模型完成用户流失预测；获得校赛一等奖。", "bold": ["5 万条", "逻辑回归", "一等奖"]},
            ])
        ],
    },
    "job": {
        "title": "数据分析实习生",
        "company": "示例保险科技",
        "availability": "每周到岗 4 天，可连续实习 3 个月以上",
        "jd": """数据分析实习生（示例保险科技，虚构）

主要职责
1. 负责外部风控数据源的测试、接入与上线后运营；
2. 基于产品形态与人群特征制定并优化风控策略；
3. 承保前后风险追踪，监控转化指标与风险表现，输出异常预警与解读。

岗位要求
1. 本科及以上在读，数学、统计、经济、金融等相关专业；
2. 熟练使用 Excel、SQL，具备数据敏感性；
3. 每周可实习 4 天及以上优先。
""",
        "matches": [
            {"requirement": "风控数据源测试与运营", "ability_id": "data-ab-1", "ability_label": "SQL 与指标", "star_statement_ids": ["data-star-1"], "match_level": "强", "reason": "清洗 10 万+ 条保单数据并搭建风控指标看板"},
            {"requirement": "风控策略制定与优化", "ability_id": "data-ab-2", "ability_label": "统计建模", "star_statement_ids": ["data-star-2"], "match_level": "强", "reason": "设计 AB 测试并验证策略效果"},
            {"requirement": "指标监控与异常解读", "ability_id": "data-ab-3", "ability_label": "业务分析", "star_statement_ids": ["data-star-2"], "match_level": "中", "reason": "从指标异常出发做归因并输出复盘"},
        ],
    },
    "sources": SOURCES["data"],
}

LAW = {
    "id": "law",
    "name": "许清和",
    "education": _edu(
        "示例大学", "法学", "硕士", "2024-09", "2027-06", 3.8, "前 10%",
        [("合同法", "A"), ("公司法", "A"), ("法律检索", "A")],
        note="法律职业资格 A 证",
    ),
    "honors": [
        {"title": "校级二等奖学金", "year": "2025", "level": "校级", "detail": "前 10%"},
        {"title": "模拟法庭比赛", "year": "2024", "level": "校级", "detail": "优秀辩手"},
    ],
    "skills": [
        {"category": "法律工具", "items": ["北大法宝", "Westlaw", "Excel"]},
        {"category": "语言", "items": ["英文合同审阅", "法律翻译"]},
    ],
    "experiences": [
        _exp(
            "law-exp-1", "示例律所 · 实习生", "internship", "实习生",
            "2025-07", "2025-12",
            ["审阅与修订 40 份中英文合同", "完成 30 次法律法规与案例检索", "撰写 5 份法律备忘录", "完成 8 份文件翻译"],
            ["合同审阅", "法律检索", "备忘录撰写", "法律翻译"],
            ["5 份备忘录被主办律师采用"],
            ["合同审阅", "法律检索"],
        ),
        _exp(
            "law-exp-2", "示例零售集团 · 法务实习生", "internship", "法务实习生",
            "2026-01", "2026-05",
            ["审核 20 份产品宣传与促销规则", "处理 15 件产品质量与宣传客诉", "起草股东会/董事会决议 6 份"],
            ["广告合规审核", "客诉处理", "决议起草"],
            ["形成 1 份广告合规检查清单"],
            ["合规与沟通", "合同审阅"],
        ),
    ],
    "stars": [
        _star("law-star-1", "law-exp-1", "合同审阅", "合同量较大", "控制合同风险",
              "审阅与修订 40 份中英文合同，标注风险条款", "5 份备忘录被主办律师采用"),
        _star("law-star-2", "law-exp-1", "法律检索", "争议解决", "支持法律意见",
              "完成 30 次法规与案例检索，撰写 5 份备忘录", "检索结论进入法律意见"),
        _star("law-star-3", "law-exp-2", "合规与沟通", "广告合规", "降低宣传风险",
              "审核 20 份宣传与促销规则，处理 15 件客诉", "形成 1 份合规检查清单"),
    ],
    "abilities": [
        {"id": "law-ab-1", "label": "合同审阅", "description": "中英文合同审阅与风险条款识别", "star_statement_refs": ["law-star-1"]},
        {"id": "law-ab-2", "label": "法律检索", "description": "法规与案例检索、备忘录撰写", "star_statement_refs": ["law-star-2"]},
        {"id": "law-ab-3", "label": "合规与沟通", "description": "广告合规、客诉处理与跨部门沟通", "star_statement_refs": ["law-star-3"]},
    ],
    "profile_blocks": [
        {"label": "合同审阅", "text": "审阅与修订 40 份中英文合同，能识别风险条款并输出修改建议；法律职业资格 A 证。", "bold": ["40 份", "风险条款", "A 证"]},
        {"label": "法律检索与写作", "text": "熟练使用北大法宝与 Westlaw，完成 30 次检索并撰写 5 份法律备忘录。", "bold": ["北大法宝", "Westlaw", "5 份"]},
        {"label": "合规与沟通", "text": "审核广告与促销规则、处理客诉，能与业务部门沟通并形成合规检查清单。", "bold": ["合规检查清单"]},
    ],
    "resume": {
        "实习经历": [
            ("law-exp-1", [
                {"label": "合同审阅与修订", "desc": "审阅与修订 40 份中英文合同，标注风险条款并输出修改建议；5 份备忘录被主办律师采用。", "bold": ["40 份", "风险条款", "5 份"]},
                {"label": "法律检索与备忘录", "desc": "完成 30 次法规与案例检索，撰写 5 份法律备忘录；检索结论进入法律意见。", "bold": ["30 次", "5 份"]},
            ]),
            ("law-exp-2", [
                {"label": "广告合规与客诉", "desc": "审核 20 份产品宣传与促销规则，处理 15 件客诉；形成 1 份广告合规检查清单。", "bold": ["20 份", "15 件", "合规检查清单"]},
            ]),
        ]
    },
    "job": {
        "title": "法务实习生",
        "company": "示例零售集团",
        "availability": "每周到岗 4 天，可连续实习 6 个月以上",
        "jd": """法务实习生（示例零售集团，虚构）

工作职责
1. 协助审阅及修订中英文合同与法律文件；
2. 协助审核产品宣传广告与促销活动规则；
3. 处理产品质量及宣传客诉；
4. 进行法律法规与案例检索，撰写法律备忘录；
5. 法律翻译，起草并整理股东会/董事会决议。

任职要求
1. 每周至少 4 天，实习期 6 个月以上；
2. 通过法律职业资格考试、取得 A 证优先；
3. 英文流利，工作细心，沟通能力强。
""",
        "matches": [
            {"requirement": "中英文合同审阅", "ability_id": "law-ab-1", "ability_label": "合同审阅", "star_statement_ids": ["law-star-1"], "match_level": "强", "reason": "审阅修订 40 份中英文合同"},
            {"requirement": "法律检索与备忘录", "ability_id": "law-ab-2", "ability_label": "法律检索", "star_statement_ids": ["law-star-2"], "match_level": "强", "reason": "30 次检索、5 份备忘录"},
            {"requirement": "广告合规与客诉", "ability_id": "law-ab-3", "ability_label": "合规与沟通", "star_statement_ids": ["law-star-3"], "match_level": "强", "reason": "审核 20 份宣传规则并处理 15 件客诉"},
        ],
    },
    "sources": SOURCES["law"],
}

SPECS = [FINANCE, CONSULTING, DATA, LAW]
