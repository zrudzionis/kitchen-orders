import datetime as dt
from datetime import datetime, timezone

import logging
import random
from typing import List

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

import constants
from models.config import Config
from models.problem import Problem
from models.action import Action

from clients.database.connection_pool import get_database_connection_pool
from clients.database.database_client import DatabaseClient
from models.action_log import ActionLog
from models.database_config import DatabaseConfig
from jobs.job_utils import report_on_job_progress, get_job_listener
from jobs.place_order import place_order
from jobs.pickup_order import pickup_order


logger = logging.getLogger(__name__)


def schedule_problem_orders(problem: Problem, config: Config) -> List[Action]:
    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")
    executors = {"default": ThreadPoolExecutor(max_workers=constants.MAX_WORKERS)}
    scheduler = BackgroundScheduler(executors=executors)
    jobs_finished = dict()
    job_listener = get_job_listener(jobs_finished)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    connection_pool = get_database_connection_pool(
        DatabaseConfig(), max_connections=constants.MAX_DB_CONNECTIONS
    )
    db_client = DatabaseClient()
    action_log = ActionLog()

    now = datetime.now(timezone.utc)
    start_time = now + dt.timedelta(seconds=constants.JOBS_INITIAL_DELAY_SECONDS)

    for i, order in enumerate(problem.orders):
        store_order_time = start_time + dt.timedelta(milliseconds=i * config.order_rate)
        jobs_finished[f"{order.id}_place"] = False
        scheduler.add_job(
            place_order,
            "date",
            run_date=store_order_time,
            args=(order, db_client, action_log, connection_pool),
            id=f"{order.id}_place",
        )

        pickup_delta = random.randint(config.min_pickup, config.max_pickup)
        pickup_order_time = store_order_time + dt.timedelta(seconds=pickup_delta)
        jobs_finished[f"{order.id}_pickup"] = False
        scheduler.add_job(
            pickup_order,
            "date",
            run_date=pickup_order_time,
            args=(order, db_client, action_log, connection_pool),
            id=f"{order.id}_pickup",
        )

    scheduler.start()

    report_on_job_progress(jobs_finished)

    logger.info("All jobs completed.")

    scheduler.shutdown(wait=True)

    connection_pool.dispose()

    return action_log.get_snapshot()
