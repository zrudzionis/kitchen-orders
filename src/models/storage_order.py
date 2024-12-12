from src.models.order import Order


class StorageOrder:
    def __init__(self, storage_type: str, age: int, order: Order):
        self.id = order.id
        self.storage_type = storage_type
        self.age = age
        self.order = order

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> str:
        return dict(
            storage_type=self.storage_type, age=self.age, order=self.order.to_dict()
        )
