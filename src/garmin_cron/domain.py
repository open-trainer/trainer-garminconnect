from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class MetricRequest:
    name: str
    from_date: date
    to_date: date


@dataclass(frozen=True)
class Task:
    user_id: str
    token_source: str
    metrics: list[MetricRequest]
    source_path: str


@dataclass(frozen=True)
class MetricResult:
    metric: MetricRequest
    payload: Any


@dataclass(frozen=True)
class TaskResult:
    task: Task
    metrics: list[MetricResult]
    executed_at: str

