from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from jsonschema import validate as jsonschema_validate


def _now() -> str:
    """本地时区的 ISO 8601 时间戳（精确到秒）。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


class TaskStore:
    """单次求职任务工作区的唯一入口。所有写入都先过 schema 校验。

    对齐 KBStore：数据与模型解耦，任务文件是纯 JSON，只依赖 schema。
    """

    def __init__(self, jobs_dir: Path, schema_path: Path):
        self.jobs_dir = jobs_dir
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # ---- 路径与基础读写 ----

    def _path(self, task_id: str) -> Path:
        return self.jobs_dir / f"{task_id}.json"

    def load(self, task_id: str) -> dict:
        path = self._path(task_id)
        if not path.exists():
            raise FileNotFoundError(f"未找到任务: {task_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, task: dict) -> None:
        self.validate(task)
        task["updated_at"] = _now()
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._path(task["id"]).write_text(
            json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def validate(self, task: dict) -> None:
        jsonschema_validate(task, self.schema)

    def list_tasks(self) -> list[dict]:
        """列出所有任务，按更新时间倒序，返回轻量摘要。"""
        if not self.jobs_dir.exists():
            return []
        tasks = []
        for p in sorted(self.jobs_dir.glob("*.json"), reverse=True):
            try:
                t = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            tasks.append(
                {
                    "id": t.get("id"),
                    "job_title": t.get("job_title", ""),
                    "status": t.get("status", "draft"),
                    "updated_at": t.get("updated_at", ""),
                    "versions": len(t.get("versions", [])),
                    "gaps_open": sum(
                        1 for g in t.get("gaps", []) if g.get("status") == "open"
                    ),
                }
            )
        return tasks

    # ---- 创建与更新 ----

    def create_task(
        self,
        job_title: str,
        jd_text: str,
        company: str | None = None,
        availability: str | None = None,
        requirements: list[dict] | None = None,
        matches: list[dict] | None = None,
        selected_experience_ids: list[str] | None = None,
        gaps: list[dict] | None = None,
        preferences: dict | None = None,
    ) -> dict:
        now = _now()
        task = {
            "id": str(uuid.uuid4()),
            "job_title": job_title,
            "company": company or "",
            "availability": availability or "",
            "jd_text": jd_text,
            "requirements": requirements or [],
            "matches": matches or [],
            "selected_experience_ids": selected_experience_ids or [],
            "gaps": gaps or [],
            "versions": [],
            "preferences": preferences or {},
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        }
        self.save(task)
        return task

    def update_task(self, task_id: str, **fields) -> dict:
        """更新任务字段（requirements / matches / gaps / status 等）。只改传入的字段。"""
        task = self.load(task_id)
        for k, v in fields.items():
            if k != "id":
                task[k] = v
        self.save(task)
        return task

    def add_version(
        self,
        task_id: str,
        resume_text: str | None = None,
        changes: str = "",
        resume_json: dict | None = None,
        analysis_md: str | None = None,
    ) -> dict:
        """追加一个简历版本，版本号自动 +1。

        新链路写 resume_json + analysis_md；resume_text 只留给旧任务。
        """
        task = self.load(task_id)
        next_version = max((v.get("version", 0) for v in task["versions"]), default=0) + 1
        entry: dict = {
            "version": next_version,
            "changes": changes,
            "created_at": _now(),
        }
        if resume_text is not None:
            entry["resume_text"] = resume_text
        if resume_json is not None:
            entry["resume_json"] = resume_json
        if analysis_md is not None:
            entry["analysis_md"] = analysis_md
        task["versions"].append(entry)
        self.save(task)
        return task

    def set_gaps(self, task_id: str, gaps: list[dict]) -> dict:
        """整体替换缺口清单（B 每次生成后写入最新缺口）。"""
        return self.update_task(task_id, gaps=gaps)

    def update_gap_status(self, task_id: str, gap_index: int, status: str) -> dict:
        """把某条缺口标为 open / resolved（留给 A 回填使用）。"""
        task = self.load(task_id)
        if not 0 <= gap_index < len(task["gaps"]):
            raise IndexError(f"缺口序号越界: {gap_index}")
        task["gaps"][gap_index]["status"] = status
        self.save(task)
        return task
