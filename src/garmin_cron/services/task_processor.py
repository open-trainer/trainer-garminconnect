from __future__ import annotations

from datetime import datetime, timezone
import logging

from ..domain import MetricResult, TaskResult
from ..garmin_client import GarminClientFactory
from ..interfaces import IMetricFetcher, ITaskSource, ITokenProvider


class TaskProcessor:
    def __init__(
        self,
        task_source: ITaskSource,
        token_provider: ITokenProvider,
        metric_fetcher: IMetricFetcher,
        client_factory: GarminClientFactory,
    ) -> None:
        self.task_source = task_source
        self.token_provider = token_provider
        self.metric_fetcher = metric_fetcher
        self.client_factory = client_factory

    def run(self) -> list[TaskResult]:
        tasks = self.task_source.get_tasks()
        results: list[TaskResult] = []

        for task in tasks:
            try:
                auth_payload = self.token_provider.get_auth_payload(task.token_source)
                client = self.client_factory.create(auth_payload=auth_payload)
                metric_results = [
                    MetricResult(
                        metric=metric,
                        payload=self.metric_fetcher.fetch(
                            client=client,
                            metric_name=metric.name,
                            from_date=metric.from_date,
                            to_date=metric.to_date,
                        ),
                    )
                    for metric in task.metrics
                ]
                results.append(
                    TaskResult(
                        task=task,
                        metrics=metric_results,
                        executed_at=datetime.now(timezone.utc).strftime(
                            "%Y%m%dT%H%M%SZ"
                        ),
                    )
                )
            except Exception:  # pragma: no cover - depends on external API
                logging.exception("Failed processing task for user_id=%s", task.user_id)

        if results:
            self.task_source.save_results(results)
        return results

