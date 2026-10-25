from __future__ import annotations

import json
import re
from pathlib import Path

from ..config import DATA_DIR, ROOT, load_categories
from ..llm.factory import get_llm
from ..storage.kb_store import KBStore
from ..storage.task_store import TaskStore
from ..tools.kb_tools import TOOL_SCHEMAS, make_executors

PROMPT_PATH = ROOT / "src" / "resume_system" / "prompts" / "a_explore.md"
RAW_DIR = DATA_DIR / "raw"
KB_PATH = DATA_DIR / "knowledge_base" / "knowledge_base.json"
SCHEMA_PATH = ROOT / "schemas" / "knowledge_base.schema.json"
JOBS_DIR = DATA_DIR / "jobs"
TASK_SCHEMA_PATH = ROOT / "schemas" / "job_task.schema.json"

RAW_SUFFIXES = {".txt", ".md"}
CHUNK_CHARS = 20000


def _system_prompt() -> str:
    lines = ["", "", "## 可选板块（category）", ""]
    for c in load_categories():
        lines.append(f"- {c['id']}：{c['label']}")
    return PROMPT_PATH.read_text(encoding="utf-8") + "\n".join(lines)


def _load_raw_materials(only: str | None = None) -> list[tuple[str, str]]:
    """按文件读出原始材料；only 可以只跑名字里包含该字符串的文件。"""
    items: list[tuple[str, str]] = []
    if RAW_DIR.exists():
        for p in sorted(RAW_DIR.iterdir()):
            if not p.is_file() or p.suffix.lower() not in RAW_SUFFIXES:
                continue
            if only and only not in p.name:
                continue
            items.append((p.name, p.read_text(encoding="utf-8")))
    return items


def _chunks(text: str, max_chars: int = CHUNK_CHARS) -> list[str]:
    """按空行分段拼块，避免把整份材料一次性塞进上下文；单段超长时硬切。"""
    if len(text) <= max_chars:
        return [text]

    paras = re.split(r"\n\s*\n", text)
    chunks: list[str] = []
    cur = ""
    for para in paras:
        if cur and len(cur) + len(para) + 2 > max_chars:
            chunks.append(cur)
            cur = para
        else:
            cur = para if not cur else cur + "\n\n" + para
    if cur:
        chunks.append(cur)

    out: list[str] = []
    for c in chunks:
        while len(c) > max_chars:
            out.append(c[:max_chars])
            c = c[max_chars:]
        if c:
            out.append(c)
    return out


def _run_loop(llm, executors, messages: list[dict], max_rounds: int, interactive: bool) -> None:
    """跑一个会话循环。工具报错作为工具结果回给模型，不让异常打断整轮提取。"""
    for _ in range(max_rounds):
        resp = llm.chat(messages, tools=TOOL_SCHEMAS)
        if not resp.tool_calls:
            print(resp.text or "(无输出)")
            if interactive:
                more = input("\n[继续] 还有要补充/修改的吗？直接说，或输入 q 结束：").strip()
                if more and more.lower() != "q":
                    messages.append({"role": "user", "content": more})
                    continue
            break

        messages.append(
            {"role": "assistant", "content": resp.text, "tool_calls": resp.tool_calls}
        )
        for tc in resp.tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                result = "参数不是合法 JSON，请重新发起这个工具调用。"
            else:
                fn = executors.get(name)
                if fn is None:
                    result = f"未知工具: {name}"
                else:
                    try:
                        result = fn(**args)
                    except Exception as e:  # noqa: BLE001
                        result = (
                            f"写入失败：{type(e).__name__}: {e}\n"
                            "请修正参数后重试；不要跳过这条事实，也不要编造。"
                        )
            messages.append(
                {"role": "tool", "tool_call_id": tc["id"], "content": result}
            )
    else:
        print("达到最大轮数，已停止。")


def explore(
    max_rounds: int = 6,
    interactive: bool = True,
    only: str | None = None,
    max_chars: int = CHUNK_CHARS,
) -> None:
    """A：经历探索。按文件分块读原始材料 -> 提取事实/STAR -> 写回知识库。"""
    store = KBStore(KB_PATH, SCHEMA_PATH)
    llm = get_llm()
    executors = make_executors(store, interactive=interactive)
    system_prompt = _system_prompt()

    materials = _load_raw_materials(only)
    if not materials:
        print("(暂无原始材料，请把 txt/md 文件放进 data/raw/，或用 --only 指定)")
        return

    before = store.load()
    n_exp0, n_star0 = len(before.get("experiences", [])), len(before.get("star_statements", []))

    for name, text in materials:
        chunks = _chunks(text, max_chars)
        for idx, chunk in enumerate(chunks, 1):
            print(f"\n[材料] {name}（{idx}/{len(chunks)}，{len(chunk)} 字）")
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"请处理以下原始材料（文件《{name}》，第 {idx}/{len(chunks)} 段）："
                        "提取事实、产出 STAR 描述，并写入知识库。\n"
                        "同一条经历/同一能力的证据重复出现时不必重复写，写入工具会自动去重。\n\n"
                        f"{chunk}"
                    ),
                },
            ]
            _run_loop(llm, executors, messages, max_rounds, interactive)

    after = store.load()
    print(
        f"\n[完成] 经历 {n_exp0} -> {len(after.get('experiences', []))} 条，"
        f"STAR {n_star0} -> {len(after.get('star_statements', []))} 条"
    )


def _collect_open_gaps() -> list[tuple[str, int, dict]]:
    """收集所有任务里 status=open 的缺口，返回 [(task_id, gap_index, gap), ...]。"""
    result = []
    if not JOBS_DIR.exists():
        return result
    for p in sorted(JOBS_DIR.glob("*.json")):
        try:
            task = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for i, gap in enumerate(task.get("gaps", [])):
            if gap.get("status") == "open":
                result.append((task["id"], i, gap))
    return result


def _gaps_to_text(gaps: list[tuple[str, int, dict]]) -> str:
    """把缺口整理成给 A 的追问上下文。"""
    lines = []
    for idx, (_task_id, _gi, gap) in enumerate(gaps, 1):
        req = gap.get("requirement", "")
        question = gap.get("question", "") or gap.get("missing_ability", "")
        lines.append(f"{idx}. JD 要求「{req}」缺证据；待追问：{question}")
    return "\n".join(lines)


def resolve_gaps(interactive: bool = True, max_rounds: int = 6) -> None:
    """A：从任务工作区读取 B 报的缺口，追问用户补料并写回知识库，最后把缺口标为 resolved。"""
    gaps = _collect_open_gaps()
    if not gaps:
        print("没有待补的缺口（所有任务里的 gaps 都已是 resolved）。")
        return

    gap_text = _gaps_to_text(gaps)
    print(f"发现 {len(gaps)} 条待补缺口：\n{gap_text}\n")

    store = KBStore(KB_PATH, SCHEMA_PATH)
    task_store = TaskStore(JOBS_DIR, TASK_SCHEMA_PATH)
    llm = get_llm()
    executors = make_executors(store, interactive=interactive)
    system_prompt = _system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "以下是 B 在生成简历时发现的缺口（知识库里缺失、无法从材料推断的信息）。\n"
                "请逐条用「猜测法」追问用户，把确认后的新事实/经历/能力证据用工具写回知识库。\n"
                "用户明确表示「没有」的项，不要强行编造，跳过即可。\n\n"
                f"{gap_text}"
            ),
        },
    ]
    _run_loop(llm, executors, messages, max_rounds, interactive)

    resolved = 0
    for task_id, gi, _gap in gaps:
        try:
            task_store.update_gap_status(task_id, gi, "resolved")
            resolved += 1
        except (IndexError, FileNotFoundError) as e:
            print(f"[警告] 标记缺口失败（task={task_id[:8]} gap={gi}）：{e}")
    print(f"\n已将 {resolved} 条缺口标记为 resolved。")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="A：经历探索 + 缺口补料")
    parser.add_argument("--resolve-gaps", action="store_true", help="从任务工作区读取缺口，追问补料并写回知识库")
    parser.add_argument("--no-interactive", action="store_true", help="非交互")
    parser.add_argument("--only", help="只处理名字里包含该字符串的原始材料（如 --only 调研）")
    parser.add_argument("--chunk-chars", type=int, default=CHUNK_CHARS, help=f"单块最大字符数（默认 {CHUNK_CHARS}）")
    args = parser.parse_args()

    if args.resolve_gaps:
        resolve_gaps(interactive=not args.no_interactive)
    else:
        explore(
            interactive=not args.no_interactive,
            only=args.only,
            max_chars=args.chunk_chars,
        )


if __name__ == "__main__":
    main()
