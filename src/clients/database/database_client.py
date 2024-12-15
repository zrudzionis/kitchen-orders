from contextlib import contextmanager
from typing import Optional
from sqlalchemy import text, Connection

from constants import (
    StorageType,
    TransactionIsolationLevel,
    MaxInventory,
)
from models.inventory import Inventory
from models.order import Order
from models.storage_order import StorageOrder


class DatabaseClient:
    def fetch_inventory(self, connection: Connection) -> Inventory:
        result = connection.execute(
            text("SELECT storage_type, inventory_count FROM inventory;"),
        )
        inventory_map = {row[0]: row[1] for row in result}
        return Inventory(
            hot=inventory_map[StorageType.HOT],
            cold=inventory_map[StorageType.COLD],
            shelf=inventory_map[StorageType.SHELF],
        )

    def fetch_order_to_move(
            self,
            connection: Connection) -> Optional[StorageOrder]:
        result = connection.execute(
            text(
                """
                SELECT
                    (SELECT COUNT(*) FROM order_storage WHERE storage_type = 'hot') AS hot_count,
                    (SELECT COUNT(*) FROM order_storage WHERE storage_type = 'cold') AS cold_count
                """
            )
        )
        hot_count, cold_count = result.fetchone()

        storage_types = []
        if hot_count < MaxInventory.HOT:
            storage_types.append(StorageType.HOT)
        if cold_count < MaxInventory.COLD:
            storage_types.append(StorageType.COLD)

        if not storage_types:
            return None

        storage_types_str = "('" + "', '".join(storage_types) + "')"

        result = connection.execute(
            text(
                f"""
                SELECT
                    order_id,
                    order_name,
                    storage_type,
                    best_storage_type,
                    fresh_max_age,
                    cumulative_age - fresh_max_age +
                        CASE
                            WHEN storage_type = best_storage_type THEN
                                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                            ELSE
                                2 * EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                        END AS relative_age
                FROM order_storage
                WHERE storage_type = 'shelf' AND best_storage_type IN {storage_types_str}
                ORDER BY relative_age DESC
                LIMIT 1;
                """
            )
        )

        row = result.fetchone()
        if row is None:
            return None

        (
            order_id,
            order_name,
            storage_type,
            best_storage_type,
            fresh_max_age,
            age,
        ) = row
        order = Order(order_id, order_name, best_storage_type, fresh_max_age)
        return StorageOrder(storage_type, age, order)

    def fetch_order_to_discard(
            self,
            connection: Connection) -> Optional[StorageOrder]:
        result = connection.execute(
            text(
                """
                SELECT
                    order_id,
                    order_name,
                    storage_type,
                    best_storage_type,
                    fresh_max_age,
                    cumulative_age - fresh_max_age +
                        CASE
                            WHEN storage_type = best_storage_type THEN
                                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                            ELSE
                                2 * EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                        END AS relative_age
                FROM order_storage
                WHERE storage_type = 'shelf'
                ORDER BY relative_age DESC
                LIMIT 1;
                """
            )
        )
        row = result.fetchone()
        if row is None:
            return None

        order_id, order_name, storage_type, best_storage_type, freshness, age = row
        order = Order(order_id, order_name, best_storage_type, freshness)
        storage_order = StorageOrder(storage_type, age, order)
        return storage_order

    def move_order(
            self,
            connection: Connection,
            from_storage: str,
            to_storage: str,
            order_id: str) -> None:
        connection.execute(
            text(
                """
                WITH updated_inventory AS (
                    UPDATE inventory
                    SET inventory_count = CASE
                        WHEN storage_type = :from_storage THEN inventory_count - 1
                        WHEN storage_type = :to_storage THEN inventory_count + 1
                    END
                    WHERE storage_type IN (:from_storage, :to_storage)
                    RETURNING storage_type
                )
                UPDATE order_storage
                SET storage_type = :to_storage
                WHERE order_id = :order_id and storage_type = :from_storage;
                """
            ),
            {
                "from_storage": from_storage,
                "to_storage": to_storage,
                "order_id": order_id,
            },
        )

    def insert_order(
            self,
            connection: Connection,
            order: Order,
            storage_type: str) -> None:
        """Insert a new order into the order_storage table and update inventory."""
        connection.execute(
            text(
                """
                WITH inserted_order AS (
                    INSERT INTO order_storage (
                        order_id, order_name, storage_type, best_storage_type, fresh_max_age, cumulative_age
                    )
                    VALUES (:order_id, :order_name, :storage_type, :best_storage_type, :fresh_max_age, 0)
                    RETURNING storage_type
                )
                UPDATE inventory
                SET inventory_count = inventory_count + 1
                WHERE storage_type = :storage_type;
                """
            ),
            {
                "order_id": order.id,
                "order_name": order.name,
                "storage_type": storage_type,
                "best_storage_type": order.temp,
                "fresh_max_age": order.freshness,
            },
        )

    def delete_order_if_exists(
            self,
            connection: Connection,
            order_id: str) -> bool:
        """
        Delete an order from the order_storage table and update inventory.
        If order doesn't exist return False.
        """
        result = connection.execute(
            text(
                """
                WITH deleted_order AS (
                    DELETE FROM order_storage
                    WHERE order_id = :order_id
                    RETURNING storage_type
                )
                UPDATE inventory
                SET inventory_count = inventory_count - 1
                WHERE storage_type = (SELECT storage_type FROM deleted_order);
                """,
            ),
            {"order_id": order_id},
        )

        return result.rowcount == 1

    def delete_all_orders(self, connection: Connection) -> int:
        """
        Returns number of deleted orders.
        """
        result = connection.execute(
            text(
                """
                WITH deleted_order AS (
                    DELETE FROM order_storage
                    RETURNING storage_type
                )
                UPDATE inventory
                SET inventory_count = 0;
                """,
            ),
        )

        return result.rowcount

    def fetch_order_if_exists(
            self,
            connection: Connection,
            order_id: str) -> Optional[StorageOrder]:
        """
        Returns number of deleted orders.
        """
        result = connection.execute(
            text(
                """
                SELECT
                    order_id,
                    order_name,
                    storage_type,
                    best_storage_type,
                    fresh_max_age,
                    cumulative_age +
                        CASE
                            WHEN storage_type = best_storage_type THEN
                                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                            ELSE
                                2 * EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at))
                        END AS age
                FROM order_storage
                WHERE order_id = :order_id;
                """,
            ),
            {"order_id": order_id},
        )
        row = result.fetchone()
        if row is None:
            return None

        (
            order_id,
            order_name,
            storage_type,
            best_storage_type,
            fresh_max_age,
            age,
        ) = row

        order = Order(order_id, order_name, best_storage_type, fresh_max_age)
        storage_order = StorageOrder(storage_type, age, order)
        return storage_order

    @contextmanager
    def transaction(
        self,
        connection: Connection,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
    ):

        connection = connection.execution_options(
            isolation_level=isolation_level.value)
        try:
            connection.begin()
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
