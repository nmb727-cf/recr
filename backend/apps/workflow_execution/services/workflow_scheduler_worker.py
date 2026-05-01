from __future__ import annotations

import logging
import time

from apps.workflow_execution.services.workflow_scheduler_engine import WorkflowSchedulerEngine

logger = logging.getLogger(__name__)


class WorkflowSchedulerWorker:
    @staticmethod
    def run_once(*, limit: int = 100):
        tasks = WorkflowSchedulerEngine.process_due_tasks(limit=limit)
        return {
            'processed_count': len(tasks),
            'task_ids': [str(task.id) for task in tasks],
        }

    @staticmethod
    def run_loop(*, interval_seconds: int = 30, limit: int = 100, stop_after_cycles: int | None = None):
        cycle = 0
        while True:
            cycle += 1
            try:
                result = WorkflowSchedulerWorker.run_once(limit=limit)
                logger.info(
                    'Workflow scheduler worker cycle completed.',
                    extra={'cycle': cycle, **result},
                )
            except Exception:
                logger.exception('Workflow scheduler worker cycle failed.')

            if stop_after_cycles is not None and cycle >= stop_after_cycles:
                break
            time.sleep(interval_seconds)
