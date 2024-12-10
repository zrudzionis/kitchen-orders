import logging
import sys

from scheduler.scheduler_utils import get_problem, is_cooking_in_progress, load_config
from models.config import Config

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


logger = logging.getLogger(__name__)


def schedule_orders(config: Config = None):
    while True:
        problem = None
        cooking_in_progress = is_cooking_in_progress()

        if cooking_in_progress and not problem:
            if not config:
                config = load_config()
            problem = get_problem(config)
            logger.info(f"Loaded problem id: {problem.test_id}")
            # TODO start implementing scheduling


if __name__ == "__main__":
    schedule_orders()
