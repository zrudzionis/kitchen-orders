import datetime as dt
from datetime import datetime, timezone

import logging
import random
import time
from typing import Dict, List

from sqlalchemy import Connection, Engine
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

import constants
from models.config import Config
from models.problem import Problem
from models.action import Action
from constants import (
    MaxInventory,
    StorageType,
    JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS,
    TransactionIsolationLevel,
)
from src.clients.database.connection_pool import (
    get_database_connection_pool,
)
from src.clients.database.database_client import DatabaseClient
from models.action_log import ActionLog
from models.database_config import DatabaseConfig
from models.order import Order

logger = logging.getLogger(__name__)


def schedule_problem_orders(problem: Problem, config: Config) -> List[Action]:
    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")
    executors = {"default": ThreadPoolExecutor(max_workers=constants.MAX_WORKERS)}
    scheduler = BackgroundScheduler(executors=executors)
    jobs_finished = dict()
    job_listener = _get_job_listener(jobs_finished)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    connection_pool = get_database_connection_pool(
        DatabaseConfig(), max_connections=constants.MAX_DB_CONNECTIONS
    )
    db_client = DatabaseClient()
    action_log = ActionLog()

    initial_delay_seconds = 3
    now = datetime.now(timezone.utc)
    start_time = now + dt.timedelta(seconds=initial_delay_seconds)

    for i, order in enumerate(problem.orders):
        store_order_time = start_time + dt.timedelta(milliseconds=i * config.order_rate)
        jobs_finished[f"{order.id}_place"] = False
        scheduler.add_job(
            store_order,
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

    _report_on_job_progress(jobs_finished)

    logger.info("All jobs completed.")

    scheduler.shutdown(wait=True)

    connection_pool.dispose()

    return action_log.get_snapshot()


def store_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    session_pool: Engine,
):
    with session_pool.connect() as connection:
        # TODO remove this
        logger.info(f"Placing order: {order.id}")
        _store_order(order, db_client, action_log, connection)


def _store_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):
    # TODO remove this
    logger.info(f"{order.id}. Session in transaction: {connection.in_transaction()}")

    try:
        with db_client.transaction(connection):
            inventory = db_client.fetch_inventory(connection)
    except Exception as e:
        logger.error(f"Unexepected error while fetching inventory. Error: {e}")
        raise

    # TODO remove this
    logger.info(
        f"{order.id}. Session in transaction after fetch inventory: {connection.in_transaction()}"
    )

    shelf_available = inventory.shelf < MaxInventory.SHELF
    best_storage_available = (
        (order.temp == StorageType.HOT and inventory.hot < MaxInventory.HOT)
        or (order.temp == StorageType.COLD and inventory.cold < MaxInventory.COLD)
        or (order.temp == StorageType.SHELF and shelf_available)
    )

    # TODO remove
    logger.info(
        f"Placing order. best_storage_available: {best_storage_available}, shelf_available: {shelf_available}"
    )

    # TODO add retries

    if best_storage_available:
        _place_order_to_best_storage(order, db_client, action_log, connection)
    elif shelf_available:
        _place_order_when_best_storage_is_full(order, db_client, action_log, connection)
    else:
        _place_order_when_no_space_left(order, db_client, action_log, connection)


def _place_order_to_best_storage(
    order: Order,
    db_client: DatabaseClient,
    actions_log: ActionLog,
    connection: Connection,
) -> None:
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        db_client.insert_order(connection, order, order.temp)
        actions_log.place(order.id)


def _place_order_when_best_storage_is_full(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
) -> None:
    db_client.insert_order(connection, order, StorageType.SHELF)
    action_log.place(order.id)


def _place_order_when_no_space_left(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
) -> None:
    order_to_move = db_client.fetch_order_to_move(connection)
    order_to_move_id = order_to_discard_id = None

    if order_to_move:
        db_client.move_order(
            connection,
            order_to_move.storage_type,
            order_to_move.order.temp,
            order_to_move.id,
        )
        order_to_move_id = order_to_move.id
    else:
        order_to_discard = db_client.fetch_order_to_discard(connection)
        db_client.delete_order(connection, order_to_discard.id)
        order_to_discard_id = order_to_discard.id

    db_client.insert_order(connection, order, StorageType.SHELF)

    if order_to_move_id:
        action_log.move(order.id)
    elif order_to_discard_id:
        action_log.discard(order.id)
    action_log.place(order.id)


def pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    session_pool: Engine,
):
    with session_pool.connect() as connection:
        # TODO remove
        logger.info(f"Picking up order: {order.id}")
        _pickup_order(order, db_client, action_log, connection)


def _pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        # TODO handle discarded order
        # TODO we should probably retry here couple of times
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


def _report_on_job_progress(jobs_finished: Dict[str, bool]):
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
