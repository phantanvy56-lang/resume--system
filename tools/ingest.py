#!/usr/bin/env python3
"""把结果文档（docx/pdf/txt/md）抽成纯文本，存进 data/raw/，供 A 处理。"""
from __future__ import annotations

import sys
from pathlib import Path

from resume_system.config import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = DATA_DIR / "raw"


def extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".pdf":
        return extract_pdf(path)
    raise ValueError(f"不支持的文件类型: {ext}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="把文件抽成纯文本存进 data/raw/（raw 只读，已存在默认跳过）")
    parser.add_argument("paths", nargs="+", help="文件或目录")
    parser.add_argument("--force", action="store_true", help="允许覆盖 data/raw/ 里同名文件")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for arg in args.paths:
        p = Path(arg)
        files = [p] if p.is_file() else sorted(p.rglob("*"))
        for f in files:
            if not f.is_file():
                continue
            try:
                text = extract_text(f)
            except Exception as e:  # noqa: BLE001
                print(f"[跳过] {f.name}: {e}")
                continue
            if len(text.strip()) < 20:
                print(f"[警告] {f.name}: 只抽出 {len(text.strip())} 个字符，可能是扫描件/图片；系统未接 OCR")
            out = RAW_DIR / f"{f.stem}.txt"
            if out.exists() and not args.force:
                print(f"[跳过] {f.name}: data/raw/{out.name} 已存在（raw 只读；确需覆盖加 --force）")
                continue
            out.write_text(text, encoding="utf-8")
            print(f"[OK] {f.name} -> data/raw/{out.name} ({len(text)} 字)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
