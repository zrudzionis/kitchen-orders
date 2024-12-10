from typing import Dict, List


class Order:
    def __init__(self, id: str, name: str, temp: str, freshness: int):
        self.id = id
        self.name = name
        self.storage_temperature = temp
        self.freshness = freshness

    @staticmethod
    def parse_orders(raw_orders: List[Dict]) -> List["Order"]:
        return [Order(**item) for item in raw_orders]

    def get_id(self) -> str:
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_storage_temperature(self) -> str:
        return self.storage_temperature

    def get_freshness(self) -> int:
        return self.freshness

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> str:
        return dict(
            id=self.id,
            name=self.name,
            temp=self.storage_temperature,
            freshness=self.freshness,
        )
