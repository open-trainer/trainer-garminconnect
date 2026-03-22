from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..domain import MetricRequest, Task, TaskResult
from ..interfaces import ITaskSource


def _parse_date(raw: str) -> datetime.date:
    return datetime.strptime(raw, "%Y-%m-%d").date()


class FileTaskSource(ITaskSource):
    def __init__(self, task_source: str, result_source: str) -> None:
        self.task_source = Path(task_source)
        self.result_source = Path(result_source)

    def get_tasks(self) -> list[Task]:
        tasks: list[Task] = []
        for task_file in sorted(self.task_source.glob("*/task.json")):
            task_payload = json.loads(task_file.read_text(encoding="utf-8"))
            metrics = [
                MetricRequest(
                    name=item["name"],
                    from_date=_parse_date(item["from"]),
                    to_date=_parse_date(item["to"]),
                )
                for item in task_payload.get("metrics", [])
            ]
            tasks.append(
                Task(
                    user_id=task_payload["user_id"],
                    token_source=task_payload["token_source"],
                    metrics=metrics,
                    source_path=str(task_file),
                )
            )
        return tasks

    def save_results(self, results: list[TaskResult]) -> None:
        now = datetime.now(timezone.utc)
        next_end = (now + timedelta(days=1)).date()

        for task_result in results:
            result_dir = self.result_source / task_result.task.user_id
            result_dir.mkdir(parents=True, exist_ok=True)
            result_file = result_dir / f"result_{task_result.executed_at}.json"
            payload = {
                "user_id": task_result.task.user_id,
                "executed_at": task_result.executed_at,
                "metrics": [
                    {
                        "metric": asdict(metric_result.metric),
                        "payload": metric_result.payload,
                    }
                    for metric_result in task_result.metrics
                ],
            }
            result_file.write_text(
                json.dumps(payload, ensure_ascii=True, indent=2, default=str),
                encoding="utf-8",
            )

            task_file = Path(task_result.task.source_path)
            task_payload = json.loads(task_file.read_text(encoding="utf-8"))
            for item in task_payload.get("metrics", []):
                previous_end = item["to"]
                item["from"] = previous_end
                item["to"] = next_end.isoformat()
            task_file.write_text(
                json.dumps(task_payload, ensure_ascii=True, indent=2),
                encoding="utf-8",
            )

