import logging

from pydantic import ValidationError
from typer import Option
import requests

from src import constants
from src.models.config import Config

logger = logging.getLogger(__name__)


def start_cooking(
    auth: str = Option(
        default="",
        help="Authentication token (required)",
    ),
    seed: int = Option(default=0, min=0, help="Problem seed (random if zero)"),
    order_rate: int = Option(
        default=500,
        min=1,
        help="The rate at which orders should be placed in miliseconds",
    ),
    min_pickup: int = Option(default=4, min=1, help="Minimum pickup time in seconds"),
    max_pickup: int = Option(default=8, min=1, help="Maximum pickup time in seconds"),
    endpoint: str = Option(
        default="https://api.cloudkitchens.com",
        help="Problem server endpoint",
    ),
    problem_file_path: str = Option(
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
    config_dict = config.model_dump()

    logger.info(f"Requesting web server to solve problem with config: {config_dict}")

    response = requests.post(
        constants.SCHEDULE_ORDERS_ENDPOINT,
        json=config_dict,
        timeout=None,
    )
    if response.ok:
        logger.info(f"OK response: {response.json()}")
    else:
        logger.error(f"Status code: {response.status_code}. Message: {response.text}")
