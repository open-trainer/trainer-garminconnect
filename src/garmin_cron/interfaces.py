from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .domain import Task, TaskResult


class ITaskSource(ABC):
    @abstractmethod
    def get_tasks(self) -> list[Task]:
        """Read tasks from an external source."""

    @abstractmethod
    def save_results(self, results: list[TaskResult]) -> None:
        """Persist task results and update task state."""


class ITokenProvider(ABC):
    @abstractmethod
    def get_auth_payload(self, token_source: str) -> dict[str, Any]:
        """Resolve authentication payload for a task token source."""


class IMetricFetcher(ABC):
    @abstractmethod
    def fetch(
        self,
        client: Any,
        metric_name: str,
        from_date: Any,
        to_date: Any,
    ) -> Any:
        """Fetch a metric payload from Garmin Connect."""

