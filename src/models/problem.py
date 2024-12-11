from typing import List

from models.order import Order


class Problem:
    def __init__(self, test_id: str, orders: List[Order]):
        self.test_id = test_id
        self.orders = orders

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return dict(
            test_id=self.test_id, orders=[order.to_dict() for order in self.orders]
        )
