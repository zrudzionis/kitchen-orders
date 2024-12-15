from typing import Dict, List

from models.order import Order


class Problem:
    def __init__(self, test_id: str, orders: List[Order]):
        self.test_id = test_id
        self.orders = orders

    def __str__(self):
        return str(self.to_dict())

    def to_dict(self):
        return dict(
            test_id=self.test_id, orders=[
                order.to_dict() for order in self.orders])

    @staticmethod
    def from_dict(data: Dict):
        test_id = data["test_id"]
        orders = [Order.from_dict(order_data) for order_data in data["orders"]]
        return Problem(test_id=test_id, orders=orders)
