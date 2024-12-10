import json
import logging
import os

from pydantic import ValidationError

import constants
from models.config import Config
from clients.challenge_client import ChallengeClient
from models.problem import Problem

logger = logging.getLogger(__name__)


def is_cooking_in_progress() -> bool:
    return os.path.exists(constants.COOKING_IN_PROGRESS_FILE_PATH)


def load_config() -> Config:
    with open(constants.CONFIG_FILE_PATH, "r") as fp:
        config_dict = json.load(fp)
        try:
            return Config(**config_dict)
        except ValidationError as e:
            logger.error(
                f"Failed to load valid config from file: {constants.CONFIG_FILE_PATH}. Errors: {e.errors()}."
            )
            raise

def get_problem(config: Config) -> Problem:
    if config.problem_file_path:
        with open(config.problem_file_path, 'r') as fp:
            problem_dict = json.load(fp)
            return Problem(**problem_dict)
    else:
        client = ChallengeClient(config.endpoint, config.auth)
        return client.fetch_problem()
