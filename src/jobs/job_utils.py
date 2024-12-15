import logging
import time
from typing import Dict
from src.constants import JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS

logger = logging.getLogger(__name__)


def get_job_listener(job_map: Dict[str, bool]):
    def job_listener(event):
        nonlocal job_map
        job_id = event.job_id
        if event.exception:
            logger.error(f"Job {job_id} failed.")
        else:
            logger.info(f"Job {job_id} completed.")
        job_map[job_id] = True

    return job_listener


def report_on_job_progress(jobs_finished: Dict[str, bool]):
    passed_seconds = 0
    while not all(jobs_finished.values()):
        if (
            passed_seconds > 0
            and passed_seconds % JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS == 0
        ):
            jobs_in_progress = [
                key for key, value in jobs_finished.items() if value is False
            ]
            logger.info(f"Jobs in progress: {jobs_in_progress}")
        time.sleep(1)
        passed_seconds += 1

