import datetime
import logging
import random
from typing import List

import psycopg2
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler


from models.config import Config
from models.problem import Problem
from models.action import Action
from src import constants
from src.clients.database_client import DatabaseClient
from src.models.database_config import DatabaseConfig
from src.models.order import Order

logger = logging.getLogger(__name__)


def schedule_problem_orders(problem: Problem, config: Config) -> List[Action]:
    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")
    executors = {"default": ProcessPoolExecutor(max_workers=constants.MAX_PROCESSES)}
    scheduler = BackgroundScheduler(executors=executors)

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

    actions = []
    now = datetime.now()
    for i, order in enumerate(problem.orders):
        store_order_time = now + datetime.timedelta(milliseconds=i * config.order_rate)
        scheduler.add_job(
            store_order,
            "date",
            run_date=store_order_time,
            args=(
                order,
                db_client,
                actions,
            ),
        )

        pickup_delta = random.randint(config.min_pickup, config.max_pickup)
        pickup_order_time = store_order_time + datetime.timedelta(seconds=pickup_delta)
        scheduler.add_job(
            pickup_order,
            "date",
            run_date=pickup_order_time,
            args=(
                order,
                db_client,
                actions,
            ),
        )

    scheduler.start()


def store_order(order: Order, db_client: DatabaseClient, actions: List[Action]):
    pass


def pickup_order(order: Order, db_client: DatabaseClient, actions: List[Action]):
    pass
