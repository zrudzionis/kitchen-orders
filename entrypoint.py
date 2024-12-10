import logging
import sys

import typer

from src.commands.start_cooking import start_cooking
from src.commands.start_containers import start_containers

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    app = typer.Typer()
    app.command()(start_containers)
    app.command()(start_cooking)
    app()


if __name__ == "__main__":
    main()
