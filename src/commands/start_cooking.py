import logging

from pydantic import ValidationError
from typer import Argument
import requests

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
    problem_file_path: str = Argument(
        default="",
        help="Problem used for local testing outside docker container.",
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
            problem_file_path=problem_file_path,
        )
        _start_cooking(config)
    except ValidationError as e:
        errors = [error["msg"] for error in e.errors()]
        logger.error(f"Command line arguments validation errors: {errors}")


def _start_cooking(config: Config):
    logger.info("Starting to cook.")
    response = requests.post(
        constants.SCHEDULE_ORDERS_ENDPOINT,
        json=config.model_dump(),
        timeout=None,
    )
    if response.ok:
        logger.info(f"OK response: {response.json()}")
    else:
        logger.error(f"Status code: {response.status_code}. Message: {response.text}")
