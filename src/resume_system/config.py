from __future__ import annotations

import os
from pathlib import Path

import yaml

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


def load_models_config() -> dict:
    return load_yaml(ROOT / "config" / "models.yaml")


def load_optional_text(rel_path: str) -> str:
    """读取 DATA_DIR 下的可选私有文件（不存在返回空串）。"""
    p = DATA_DIR / rel_path
    return p.read_text(encoding="utf-8") if p.exists() else ""


DEFAULT_STYLE = {
    "page": {"width_cm": 21.0, "height_cm": 29.7, "margin_cm": 0.8},
    "fonts": {"heading": "微软雅黑", "body": "微软雅黑", "header": "宋体-简"},
    "sizes": {"name": 18, "heading": 13.5, "body": 12},
    "colors": {"heading": "#2F5597", "text": "#000000"},
    "spacing": {"line_pt": 12.7, "bullet_gap_pt": 3.2, "entry_gap_pt": 8, "body_indent_pt": 15},
    "tabs": {"center_cm": 9.7, "right_cm": 19.4},
    "photo": {"height_cm": 3.0},
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
    """排版配置（config/style.yaml），缺失项用默认值补齐。"""
    p = ROOT / "config" / "style.yaml"
    return _deep_merge(DEFAULT_STYLE, load_yaml(p) if p.exists() else {})


def load_categories() -> list[dict]:
    """经历板块定义（config/categories.yaml），按 order 排序。"""
    data = load_yaml(ROOT / "config" / "categories.yaml")
    return sorted(data.get("categories", []), key=lambda c: c.get("order", 99))


def load_profile_blocks() -> list[dict]:
    """个人能力固定文案：data/profile_blocks.yaml（可选）。"""
    p = DATA_DIR / "profile_blocks.yaml"
    if not p.exists():
        return []
    data = load_yaml(p)
    return data.get("abilities", [])
