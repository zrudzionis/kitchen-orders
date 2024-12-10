
import logging
import time
import sys

from src import constants
from src.clients.challenge_client import ChallengeClient
from src.scheduler.scheduler_utils import is_cooking_in_progress, load_config

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


logger = logging.getLogger(__name__)


def main():
    while True:
        orders = None
        cooking_in_progress = is_cooking_in_progress()
        if cooking_in_progress and not orders:
            config = load_config()
            client = ChallengeClient(config.endpoint, config.auth)
            client.get_new_problem

        if not cooking_in_progress:
            order = None


if __name__ == "__main__":
    main()
