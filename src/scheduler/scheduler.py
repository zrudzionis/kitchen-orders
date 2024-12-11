import json
import logging
from typing import List

import psycopg2
from psycopg2 import connection

from models.config import Config
from clients.challenge_client import ChallengeClient
from models.problem import Problem
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from models.action import Action

logger = logging.getLogger(__name__)


def schedule_problem_orders(problem: Problem, config: Config) -> List[Action]:
    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")
    executors = {"default": ProcessPoolExecutor(max_workers=len(problem.orders))}
    scheduler = BackgroundScheduler(executors=executors)

    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20, dbname=dbname, user=user, password=password, host=host, port=port
    )

    actions = []
    for order in problem.orders:
        run_time = datetime.now() + timedelta(seconds=i * 2)
        scheduler.add_job(task_function, "date", run_date=run_time, args=(i,))

    scheduler.start()


def get_problem(config: Config) -> Problem:
    if config.problem_file_path:
        with open(config.problem_file_path, "r") as fp:
            problem_dict = json.load(fp)
            return Problem(**problem_dict)
    else:
        client = ChallengeClient(config.endpoint, config.auth)
        return client.fetch_problem()
