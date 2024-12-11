from psycopg2.pool import SimpleConnectionPool
from psycopg2 import connection

from src.constants import TRANSACTION_ISOLATION_LEVELS, TransactionIsolationLevel


class DatabaseClient:
    def __init__(self, connection_pool: SimpleConnectionPool):
        self.connection_pool = connection_pool

    def get_connection(self):
        return self.connection_pool.getconn()

    def release_connection(self, connection: connection):
        self.connection_pool.putconn(connection)

    def fetch_inventory(self, connection: connection):
        """Fetch the inventory counts for all storage types."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM inventory;")
            return cursor.fetchall()

    def update_inventory(
        self, connection: connection, storage_type: str, new_count: int
    ):
        """Update the inventory count for a specific storage type."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE inventory
                SET inventory_count = %s
                WHERE storage_type = %s;
                """,
                (new_count, storage_type),
            )

    def insert_order(self, connection: connection, order_id: str, storage_type: str):
        """Insert a new order into the order_storage table."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO order_storage (order_id, storage_type)
                VALUES (%s, %s);
                """,
                (order_id, storage_type),
            )

    def delete_order(self, connection: connection, order_id: str):
        """Delete an order from the order_storage table."""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM order_storage
                WHERE order_id = %s;
                """,
                (order_id,),
            )

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

    def set_transaction_isolation_level(
        self, connection: connection, level: TransactionIsolationLevel
    ):
        if level.lower() not in TRANSACTION_ISOLATION_LEVELS:
            raise ValueError(f"Invalid isolation level: {level}")

        with connection.cursor() as cursor:
            cursor.execute(f"SET TRANSACTION ISOLATION LEVEL {level.upper()};")


# Example usage
if __name__ == "__main__":
    client = DatabaseClient(
        dbname="your_db",
        user="your_user",
        password="your_password",
        host="localhost",
        port="5432",
    )

    # Example transaction
    try:
        with client as conn:  # This will start a transaction
            # Set transaction isolation level
            client.set_transaction_isolation_level(conn, "read committed")

            # Fetch current inventory
            print("Current Inventory:")
            print(client.fetch_inventory(conn))

            # Update inventory count for 'hot'
            client.update_inventory(conn, "hot", 3)

            # Insert a new order
            client.insert_order(conn, "order123", "hot")

            # Delete an order
            client.delete_order(conn, "order123")
    except Exception as e:
        print(f"Transaction failed: {e}")

    # Close the connection pool
    client.close()
