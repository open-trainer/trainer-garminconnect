from __future__ import annotations

import argparse
import logging
import os

from dotenv import load_dotenv

from .garmin_client import GarminClientFactory
from .metrics import GarminMetricFetcher
from .services import TaskProcessor
from .task_sources import FileTaskSource
from .token_sources import FileTokenProvider


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Garmin Connect metrics for tasks from external sources."
    )
    parser.add_argument("--tasks-dir", default=os.getenv("TASKS_DIR", "tasks"))
    parser.add_argument("--results-dir", default=os.getenv("RESULTS_DIR", "results"))
    parser.add_argument("--tokens-dir", default=os.getenv("TOKENS_DIR", "tokens"))
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return parser


def main() -> int:
    load_dotenv()
    args = build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    task_source = FileTaskSource(
        task_source=args.tasks_dir,
        result_source=args.results_dir,
    )
    token_provider = FileTokenProvider(tokens_dir=args.tokens_dir)
    processor = TaskProcessor(
        task_source=task_source,
        token_provider=token_provider,
        metric_fetcher=GarminMetricFetcher(),
        client_factory=GarminClientFactory(),
    )

    results = processor.run()
    logging.info("Processed %s task(s)", len(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

