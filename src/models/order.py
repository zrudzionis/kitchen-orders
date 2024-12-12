from typing import Dict, List


class Order:
    def __init__(self, id: str, name: str, temp: str, freshness: int):
        self.id = id
        self.name = name
        self.temp = temp
        self.freshness = freshness

    @staticmethod
    def parse_orders(raw_orders: List[Dict]) -> List["Order"]:
        return [Order(**item) for item in raw_orders]

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> str:
        return dict(
            id=self.id,
            name=self.name,
            temp=self.temp,
            freshness=self.freshness,
        )
