import logging

from plumbum import local, FG

logger = logging.getLogger(__name__)

docker_compose = local["docker-compose"]


def remove_containers():
    docker_compose["down", "--remove-orphans", "--volumes"] & FG
