import datetime
import logging
import random
import time
from typing import Dict, List

import psycopg2
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

import constants
from models.config import Config
from models.problem import Problem
from models.action import Action
from constants import (
    MaxInventory,
    StorageType,
    TransactionIsolationLevel,
    JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS,
)
from clients.database_client import DatabaseClient
from models.action_log import ActionLog
from models.database_config import DatabaseConfig
from models.order import Order

logger = logging.getLogger(__name__)


def schedule_problem_orders(problem: Problem, config: Config) -> List[Action]:
    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")
    executors = {"default": ProcessPoolExecutor(max_workers=constants.MAX_PROCESSES)}
    scheduler = BackgroundScheduler(executors=executors)
    jobs_finished = dict()
    job_listener = _get_job_listener(jobs_finished)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    db_config = DatabaseConfig()
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1,
        constants.MAX_DB_CONNECTIONS,
        dbname=db_config.db_name,
        user=db_config.user,
        password=db_config.password,
        host=db_config.host,
        port=db_config.port,
    )
    db_client = DatabaseClient(connection_pool)

    action_log = ActionLog()
    now = datetime.now()

    for i, order in enumerate(problem.orders):
        store_order_time = now + datetime.timedelta(milliseconds=i * config.order_rate)
        jobs_finished[f"{order.id}_place"] = False
        scheduler.add_job(
            store_order,
            "date",
            run_date=store_order_time,
            args=(
                order,
                db_client,
                action_log,
            ),
            id=f"{order.id}_place",
        )

        pickup_delta = random.randint(config.min_pickup, config.max_pickup)
        pickup_order_time = store_order_time + datetime.timedelta(seconds=pickup_delta)
        jobs_finished[f"{order.id}_pickup"] = False
        scheduler.add_job(
            pickup_order,
            "date",
            run_date=pickup_order_time,
            args=(
                order,
                db_client,
                action_log,
            ),
            id=f"{order.id}_pickup",
        )

    scheduler.start()

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

    _wait_until_all_jobs_finish(jobs_finished)

    logger.info("All jobs completed.")

    scheduler.shutdown()

    return action_log.actions


def store_order(order: Order, db_client: DatabaseClient, action_log: ActionLog):
    connection = db_client.get_connection()
    try:
        inventory = db_client.fetch_inventory(connection)
    except Exception as e:
        logger.error(f"Unexepected error while fetching inventory. Error: {e}")
        raise
    finally:
        db_client.release_connection()
    shelf_available = inventory.shelf < MaxInventory.SHELF
    best_storage_available = (
        (order.temp == StorageType.HOT and inventory.hot < MaxInventory.HOT)
        or (order.temp == StorageType.COLD and inventory.cold < MaxInventory.COLD)
        or (order.temp == StorageType.SHELF and shelf_available)
    )

    # TODO add retries

    if best_storage_available:
        _place_order_to_best_storage(order, db_client, action_log)
    elif shelf_available:
        _place_order_when_best_storage_is_full(order, db_client, action_log)
    else:
        _place_order_when_no_space_left(order, db_client, action_log)


def _place_order_to_best_storage(
    order: Order, db_client: DatabaseClient, action_log: ActionLog
) -> None:
    with db_client as connection:
        db_client.set_transaction_isolation_level(
            connection, TransactionIsolationLevel.READ_COMMITTED
        )
        db_client.insert_order(connection, order, order.temp)
        action_log.place(order.id)


def _place_order_when_best_storage_is_full(
    order: Order, db_client: DatabaseClient, action_log: ActionLog
) -> None:
    with db_client as connection:
        db_client.set_transaction_isolation_level(
            connection, TransactionIsolationLevel.READ_COMMITTED
        )
        db_client.insert_order(connection, order, StorageType.SHELF)
        action_log.place(order.id)


def _place_order_when_no_space_left(
    order: Order, db_client: DatabaseClient, action_log: ActionLog
) -> None:
    with db_client as connection:
        db_client.set_transaction_isolation_level(
            connection, TransactionIsolationLevel.REPEATABLE_READ
        )
        order_to_move = db_client.fetch_order_to_move(connection)
        order_to_move_id = order_to_discard_id = None

        if order_to_move:
            order_to_move_id = order_to_move.id
            db_client.move_order(
                connection,
                order_to_move.storage_type,
                order_to_move.order.temp,
                order_to_move_id,
            )
            action_log.discard(order.id)
        else:
            order_to_discard = db_client.fetch_order_to_discard(connection)
            order_to_discard_id = order_to_discard.id
            db_client.delete_order(connection, order_to_discard_id)

        db_client.insert_order(connection, order, StorageType.SHELF)

        if order_to_move_id:
            action_log.move(order_to_move_id)
        elif order_to_discard_id:
            action_log.discard(order_to_discard_id)
        action_log.place(order.id)


def pickup_order(order: Order, db_client: DatabaseClient, action_log: ActionLog):
    # TODO handle discarded order
    # TODO we should probably retry here couple of times
    with db_client as connection:
        db_client.set_transaction_isolation_level(
            connection, constants.TransactionIsolationLevel.READ_COMMITTED
        )
        db_client.delete_order(connection, order.id)
        action_log.pickup(order.id)


def _get_job_listener(job_map: Dict[str, bool]):
    def job_listener(event):
        nonlocal job_map
        job_id = event.job_id
        if event.exception:
            logger.error(f"Job {job_id} failed.")
        else:
            logger.info(f"Job {job_id} completed.")
        job_map[job_id] = True

    return job_listener


def _wait_until_all_jobs_finish(jobs_finished: Dict[str, bool]):
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
