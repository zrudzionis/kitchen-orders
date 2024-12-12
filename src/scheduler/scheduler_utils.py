import json
from flask import Config

from src.clients.challenge_client import ChallengeClient
from src.models.problem import Problem


def get_problem(config: Config) -> Problem:
    if config.problem_file_path:
        with open(config.problem_file_path, "r") as fp:
            problem_dict = json.load(fp)
            return Problem(**problem_dict)
    else:
        client = ChallengeClient(config.endpoint, config.auth)
        return client.fetch_problem()
