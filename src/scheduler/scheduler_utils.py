import json
import logging
import os

from pydantic import ValidationError

from src import constants
from src.models.config import Config

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
