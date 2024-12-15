import json

from clients.challenge_client import ChallengeClient
from models.problem import Problem
from models.config import Config


def load_problem(config: Config) -> Problem:
    if config.problem_file_path:
        with open(config.problem_file_path, "r", encoding="utf-8") as fp:
            problem_dict = json.load(fp)
            return Problem.from_dict(problem_dict)
    else:
        client = ChallengeClient(config.endpoint, config.auth)
        return client.fetch_problem(name="", seed=config.seed)
