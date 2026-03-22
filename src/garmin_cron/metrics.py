from __future__ import annotations

from datetime import timedelta
from typing import Any

from .interfaces import IMetricFetcher


class GarminMetricFetcher(IMetricFetcher):
    """
    Metric adapter around python-garminconnect methods.
    """

    def fetch(
        self,
        client: Any,
        metric_name: str,
        from_date: Any,
        to_date: Any,
    ) -> Any:
        days = []
        current = from_date
        while current <= to_date:
            days.append(current)
            current = current + timedelta(days=1)

        if metric_name == "steps":
            return {day.isoformat(): client.get_steps_data(day.isoformat()) for day in days}
        if metric_name == "heart_rate":
            return {day.isoformat(): client.get_heart_rates(day.isoformat()) for day in days}
        if metric_name == "sleep":
            return {day.isoformat(): client.get_sleep_data(day.isoformat()) for day in days}
        if metric_name == "stats":
            return {day.isoformat(): client.get_stats(day.isoformat()) for day in days}
        if metric_name == "body_composition":
            return {
                day.isoformat(): client.get_body_composition(day.isoformat()) for day in days
            }
        if metric_name == "activities":
            return client.get_activities_by_date(from_date.isoformat(), to_date.isoformat())

        raise ValueError(
            f"Unsupported metric '{metric_name}'. "
            "Supported metrics: steps, heart_rate, sleep, stats, body_composition, activities."
        )

