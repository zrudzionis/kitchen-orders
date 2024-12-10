import json
import random
import requests
from datetime import timedelta
from typing import List
from logging import getLogger

from models.action import Action
from models.order import Order
from models.problem import Problem

logger = getLogger(__name__)

class Client:
    def __init__(self, endpoint: str, auth: str):
        self.endpoint = endpoint
        self.auth = auth

    def new_problem(self, name: str, seed: int = 0) -> 'Problem':
        if seed == 0:
            seed = random.randint(1, 1 << 63)  # Mimics Java's Random().nextLong()

        url = f"{self.endpoint}/interview/challenge/new?auth={self.auth}&name={name}&seed={seed}"
        response = requests.get(url)

        if not response.ok:
            raise IOError(f"{url}: {response.reason}")

        test_id = response.headers.get("x-test-id")
        logger.info(f"Fetched new test problem, id={test_id}: {url}")
        return Problem(test_id, Order.parse(response.text))

    def solve_problem(self, test_id: str, rate: timedelta, min_time: timedelta, max_time: timedelta, actions: List['Action']) -> str:
        solution = Solution(
            options=Options(rate, min_time, max_time),
            actions=actions
        )
        url = f"{self.endpoint}/interview/challenge/solve?auth={self.auth}"
        headers = {
            "Content-Type": "application/json",
            "x-test-id": test_id
        }
        response = requests.post(url, data=solution.encode(), headers=headers)

        if not response.ok:
            raise IOError(f"{url}: {response.reason}")
        return response.text


class Options:
    def __init__(self, rate: timedelta, min_time: timedelta, max_time: timedelta):
        self.rate = int(rate.total_seconds() * 1_000_000)  # Convert to microseconds
        self.min = int(min_time.total_seconds() * 1_000_000)
        self.max = int(max_time.total_seconds() * 1_000_000)

    def to_dict(self):
        return {
            "rate": self.rate,
            "min": self.min,
            "max": self.max
        }


class Solution:
    def __init__(self, options: Options, actions: List['Action']):
        self.options = options
        self.actions = actions

    def encode(self) -> str:
        return json.dumps({
            "options": self.options.to_dict(),
            "actions": [action.__dict__ for action in self.actions]
        })
