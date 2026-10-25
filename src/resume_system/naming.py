"""输出文件命名与目录：一家公司一个文件夹，一次投递一个子文件夹。"""
from __future__ import annotations

import re
from pathlib import Path

_BAD_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_name(name: str) -> str:
    """去掉文件名/目录名里的非法字符。"""
    return _BAD_CHARS.sub("-", name or "").strip()


def job_name(task: dict) -> str:
    return safe_name(task.get("job_title") or "") or "未命名岗位"


def output_stem(task: dict) -> str:
    """简历成稿的统一文件名（不含扩展名）：公司_岗位。

    公司为空时退化为 岗位。
    """
    job = job_name(task)
    company = safe_name(task.get("company") or "")
    return f"{company}_{job}" if company else job


def output_dir(task: dict, base: Path) -> Path:
    """输出目录：output/公司/岗位/；公司为空时 output/岗位/。"""
    company = safe_name(task.get("company") or "")
    return base / company / job_name(task) if company else base / job_name(task)
