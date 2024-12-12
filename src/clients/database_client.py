from typing import Optional
from psycopg2.pool import SimpleConnectionPool

from src.constants import (
    TRANSACTION_ISOLATION_LEVELS,
    StorageType,
    TransactionIsolationLevel,
    MaxInventory,
)
from src.models.inventory import Inventory
from src.models.order import Order
from src.models.storage_order import StorageOrder


class DatabaseClient:
    def __init__(self, connection_pool: SimpleConnectionPool):
        self.connection_pool = connection_pool

    def get_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, connection):
        self.connection_pool.putconn(connection)

    def fetch_inventory(self, connection) -> Inventory:
        with connection.cursor() as cursor:
            cursor.execute("SELECT storage_type, inventory_count FROM inventory;")
            rows = cursor.fetchall()
            inventory_map = {row[0]: row[1] for row in rows}
            return Inventory(
                hot=inventory_map[StorageType.HOT],
                cold=inventory_map[StorageType.COLD],
                shelf=inventory_map[StorageType.SHELF],
            )

    def fetch_order_to_move(self, connection) -> Optional[StorageOrder]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                    SELECT
                        (SELECT COUNT(*) FROM order_storage WHERE storage_type = 'hot') AS hot_count,
                        (SELECT COUNT(*) FROM order_storage WHERE storage_type = 'cold') AS cold_count
                """
            )
        hot_count, cold_count = cursor.fetchone()

        if hot_count >= MaxInventory.HOT and cold_count >= MaxInventory.COLD:
            return None

        cursor.execute(
            """
                WITH prioritized_orders AS (
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
                            END AS real_age
                    FROM order_storage
                    WHERE storage_type = 'shelf' AND best_storage_type IN ('hot', 'cold')
                ),

                fresh_hot_order AS (
                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM prioritized_orders
                    WHERE storage_type = 'hot' AND real_age <= fresh_max_age
                    ORDER BY fresh_max_age - real_age ASC
                    LIMIT 1
                ),

                stale_hot_order AS (
                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM prioritized_orders
                    WHERE storage_type = 'hot' AND real_age > fresh_max_age
                    ORDER BY real_age - fresh_max_age ASC
                    LIMIT 1
                ),

                fresh_cold_order AS (
                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM prioritized_orders
                    WHERE storage_type = 'cold' AND real_age <= fresh_max_age
                    ORDER BY fresh_max_age - real_age ASC
                    LIMIT 1
                ),

                stale_cold_order AS (
                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM prioritized_orders
                    WHERE storage_type = 'cold' AND real_age > fresh_max_age
                    ORDER BY real_age - fresh_max_age ASC
                    LIMIT 1
                )

                SELECT * FROM (
                    -- Select one fresh hot order if available, else stale hot order
                    SELECT * FROM fresh_hot_order
                    UNION ALL
                    SELECT * FROM stale_hot_order WHERE NOT EXISTS (SELECT 1 FROM fresh_hot_order)
                ) AS hot_order
                UNION ALL
                (
                    -- Select one fresh cold order if available, else stale cold order
                    SELECT * FROM fresh_cold_order
                    UNION ALL
                    SELECT * FROM stale_cold_order WHERE NOT EXISTS (SELECT 1 FROM fresh_cold_order)
                ) AS cold_order
                LIMIT 2;

            """
        )

        rows = cursor.fetchall()
        for row in rows:
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
            hot_storage_available = (
                best_storage_type == StorageType.HOT and hot_count < MaxInventory.HOT
            )
            cold_storage_available = (
                best_storage_type == StorageType.COLD and hot_count < MaxInventory.COLD
            )
            if hot_storage_available or cold_storage_available:
                return storage_order
        return None

    def fetch_order_to_discard(self, connection) -> Optional[StorageOrder]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                    WITH prioritized_orders AS (
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
                                END AS real_age
                        FROM order_storage
                        WHERE storage_type = 'shelf'
                    ),
                    candidate_orders AS (
                        SELECT
                            order_id,
                            order_name,
                            storage_type,
                            best_storage_type,
                            fresh_max_age,
                            real_age
                        FROM prioritized_orders
                        WHERE real_age > fresh_max_age
                        ORDER BY real_age DESC
                        LIMIT 1
                    )
                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM candidate_orders

                    UNION ALL

                    SELECT
                        order_id,
                        order_name,
                        storage_type,
                        best_storage_type,
                        fresh_max_age,
                        real_age
                    FROM prioritized_orders
                    WHERE order_id NOT IN (SELECT order_id FROM candidate_orders)
                    ORDER BY real_age DESC
                    LIMIT 1;
                """
            )
            row = cursor.fetchone()
            if row is None:
                return None

            order_id, order_name, storage_type, best_storage_type, freshness, age = row
            order = Order(order_id, order_name, best_storage_type, freshness)
            storage_order = StorageOrder(storage_type, age, order)
            return storage_order

    def move_order(self, connection, from_storage, to_storage, order_id) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH updated_inventory AS (
                    UPDATE inventory
                    SET inventory_count = CASE
                        WHEN storage_type = %s THEN inventory_count - 1
                        WHEN storage_type = %s THEN inventory_count + 1
                    END
                    WHERE storage_type IN (%s, %s)
                    RETURNING storage_type
                )
                UPDATE order_storage
                SET storage_type = %s
                WHERE order_id = %s;
                """,
                (
                    from_storage,
                    to_storage,
                    from_storage,
                    to_storage,
                    to_storage,
                    order_id,
                ),
            )

    def insert_order(self, connection, order: Order, storage_type: str) -> None:
        """Insert a new order into the order_storage table and update inventory."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH inserted_order AS (
                    INSERT INTO order_storage (order_id, order_name, storage_type, best_storage_type, fresh_max_age, cumulative_age)
                    VALUES (%s, %s, %s, %s, %s, 0)
                    RETURNING storage_type
                )
                UPDATE inventory
                SET inventory_count = inventory_count + 1
                WHERE storage_type = %s;
                """,
                (
                    order.id,
                    order.name,
                    storage_type,
                    order.temp,
                    order.freshness,
                    storage_type,
                ),
            )

    def delete_order(self, connection, order_id: str):
        """Delete an order from the order_storage table and update inventory."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH deleted_order AS (
                    DELETE FROM order_storage
                    WHERE order_id = %s
                    RETURNING storage_type
                )
                UPDATE inventory
                SET inventory_count = inventory_count - 1
                WHERE storage_type = (SELECT storage_type FROM deleted_order);
                """,
                (order_id,),
            )

    def set_transaction_isolation_level(
        self, connection, level: TransactionIsolationLevel
    ):
        if level.lower() not in TRANSACTION_ISOLATION_LEVELS:
            raise ValueError(f"Invalid isolation level: {level}")

        with connection.cursor() as cursor:
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {level.upper()};")

    def __enter__(self):
        self.connection = self.get_connection()
        self.connection.autocommit = False  # Disable autocommit for transactions
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        if exc_type is not None:
            self.connection.rollback()  # Rollback the transaction if an error occurs
        else:
            self.connection.commit()  # Commit the transaction if no error occurs
        self.release_connection(self.connection)
