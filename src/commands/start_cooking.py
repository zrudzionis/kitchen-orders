import logging
import os

from pydantic import ValidationError
from typer import Argument

from src import constants
from src.models.config import Config

logger = logging.getLogger(__name__)


def start_cooking(
    auth: str = Argument(
        help="Authentication token (required)",
    ),
    seed: int = Argument(help="Problem seed (random if zero)", default=0, min=0),
    order_rate: int = Argument(
        help="The rate at which orders should be placed in miliseconds",
        default=500,
        min=1,
    ),
    min_pickup: int = Argument(help="Minimum pickup time in seconds", default=4, min=1),
    max_pickup: int = Argument(help="Maximum pickup time in seconds", default=8, min=1),
    endpoint: str = Argument(
        default="https://api.cloudkitchens.com",
        help="Problem server endpoint",
    ),
):
    try:
        config = Config(
            auth=auth,
            seed=seed,
            order_rate=order_rate,
            min_pickup=min_pickup,
            max_pickup=max_pickup,
            endpoint=endpoint,
        )
        logger.info("Starting to cook")
        _start_cooking(config)
    except ValidationError as e:
        logger.error(f"Command line arguments validation error: {e.errors()}")
    finally:
        _cleanup()


def _start_cooking(config: Config):
    with open(constants.COOKING_IN_PROGRESS_FILE_PATH, "w") as fp:
        fp.write(config.model_dump_json())


def _cleanup():
    if os.path.exists(constants.COOKING_IN_PROGRESS_FILE_PATH):
        os.remove(constants.COOKING_IN_PROGRESS_FILE_PATH)
