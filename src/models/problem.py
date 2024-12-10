from typing import List

from models.order import Order

class Problem:
    def __init__(self, test_id: str, orders: List['Order']):
        self.test_id = test_id
        self.orders = orders

    def get_test_id(self) -> str:
        return self.test_id

    def get_orders(self) -> List['Order']:
        return self.orders
