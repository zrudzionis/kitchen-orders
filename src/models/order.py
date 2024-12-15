from typing import Dict, List


class Order:
    def __init__(self, order_id: str, name: str, temp: str, freshness: int):
        self.id = order_id
        self.name = name
        self.temp = temp
        self.freshness = freshness

    @staticmethod
    def parse_orders(raw_orders: List[Dict]) -> List["Order"]:
        return [Order.from_dict(order_dict) for order_dict in raw_orders]

    @staticmethod
    def from_dict(order_dict: Dict) -> str:
        return Order(
            order_id=order_dict["id"],
            name=order_dict["name"],
            temp=order_dict["temp"],
            freshness=order_dict["freshness"],
        )

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> str:
        return dict(
            id=self.id,
            name=self.name,
            temp=self.temp,
            freshness=self.freshness,
        )
