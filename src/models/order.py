import json
from typing import List

class Order:
    def __init__(self, id: str, name: str, temp: str, freshness: int):
        self.id = id
        self.name = name
        self.temp = temp
        self.freshness = freshness

    @staticmethod
    def parse(json_data: str) -> List['Order']:
        return [Order(**item) for item in json.loads(json_data)]

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_temp(self) -> str:
        return self.temp

    def get_freshness(self) -> int:
        return self.freshness

    def __str__(self) -> str:
        return f"{{id: {self.id}, name: {self.name}, temp: {self.temp}, freshness: {self.freshness} }}"
