from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml


def setup_logging() -> None:
    """统一日志格式（幂等，只配置一次）；CLI 入口在 main() 里调用。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

# 项目根目录（src/resume_system/config.py 向上两级）
ROOT = Path(__file__).resolve().parents[2]

# 数据与输出目录：默认在仓库内，可用环境变量指向私有目录或 demo
def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if not raw:
        return default.resolve()
    p = Path(raw)
    return (p if p.is_absolute() else ROOT / p).resolve()


DATA_DIR = _env_path("RESUME_DATA_DIR", ROOT / "data")
OUTPUT_DIR = _env_path("RESUME_OUTPUT_DIR", ROOT / "output")


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_optional_text(rel_path: str) -> str:
    """读取 DATA_DIR 下的可选私有文件（不存在返回空串）。"""
    p = DATA_DIR / rel_path
    return p.read_text(encoding="utf-8") if p.exists() else ""


DEFAULT_STYLE = {
    "page": {"width_cm": 21.0, "height_cm": 29.7, "margin_cm": 0.8},
    "fonts": {"heading": "微软雅黑", "body": "微软雅黑", "header": "宋体-简"},
    "sizes": {"name": 18, "heading": 13.5, "body": 12},
    "colors": {"accent": "#2F5597", "text": "#222222"},
    "spacing": {"line_pt": 12.7, "bullet_gap_pt": 3.2, "entry_gap_pt": 8, "body_indent_pt": 15},
    "tabs": {"center_cm": 9.7, "right_cm": 19.4},
    "photo": {"height_cm": 3.0},
    "layout": {
        "order": ["education", "sections", "skills", "abilities"],   # 主区块顺序；不出现的块不渲染
        "show": {"photo": True, "availability": True, "job_title": True},
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_style() -> dict:
    """排版配置（config/style.yaml）：默认值 ← 主题预设 ← 顶层手写覆盖。

    `theme` 选中 themes 里的预设；顶层其它字段覆盖预设（可局部微调）。
    """
    p = ROOT / "config" / "style.yaml"
    data = load_yaml(p) if p.exists() else {}
    base = DEFAULT_STYLE
    theme_name = data.get("theme")
    theme = (data.get("themes") or {}).get(theme_name) if theme_name else None
    if theme:
        base = _deep_merge(DEFAULT_STYLE, theme)
    override = {k: v for k, v in data.items() if k not in ("theme", "themes")}
    return _deep_merge(base, override)


def load_categories() -> list[dict]:
    """经历板块定义（config/categories.yaml），按 order 排序。"""
    data = load_yaml(ROOT / "config" / "categories.yaml")
    return sorted(data.get("categories", []), key=lambda c: c.get("order", 99))


def load_abilities() -> list[dict]:
    """能力词表（config/abilities.yaml）：JD 关键词覆盖检查等使用。"""
    data = load_yaml(ROOT / "config" / "abilities.yaml")
    return data.get("abilities", [])


def load_profile_blocks() -> list[dict]:
    """个人能力固定文案：data/profile_blocks.yaml（可选）。"""
    p = DATA_DIR / "profile_blocks.yaml"
    if not p.exists():
        return []
    data = load_yaml(p)
    return data.get("abilities", [])
