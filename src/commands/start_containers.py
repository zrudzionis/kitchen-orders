import logging

from plumbum import local, FG

logger = logging.getLogger(__name__)

docker_compose = local["docker-compose"]


def start_containers():
    docker_compose["build"] & FG
    docker_compose["up"] & FG
