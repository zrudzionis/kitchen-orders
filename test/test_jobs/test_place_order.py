from typing import List
import unittest

from src.clients.database.connection_pool import get_database_connection_pool
from src.clients.database.database_client import DatabaseClient
from src.constants import MaxInventory, StorageType
from src.jobs.place_order import place_order
from src.jobs.pickup_order import pickup_order
from src.models.action_log import ActionLog
from src.models.database_config import DatabaseConfig
from src.models.order import Order
from src.models.action import Action


class TestPlaceOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection_pool = get_database_connection_pool(DatabaseConfig(), max_connections=2)
        cls.connection = cls.connection_pool.connect()
        cls.db_client = DatabaseClient()

    def setUp(self):
        pass

    def assertActionsEqual(self, action_log: ActionLog, expected_actions: List[str]):
        got_actions = [action.action_type for action in action_log.get_snapshot()]
        msg = f"Expected: {expected_actions}, got: {got_actions}"

        self.assertEqual(len(got_actions), len(expected_actions), msg)
        for expected_action, got_action in zip(expected_actions, got_actions):
            self.assertEqual(expected_action, got_action, msg)

    def fill_hot_storage(self, start_id=1):
        for i in range(start_id, start_id + MaxInventory.HOT):
            self.db_client.insert_order(
                self.connection,
                Order(str(i), str(i), StorageType.HOT, 10 + i),
                StorageType.HOT,
            )
        self.connection.commit()

    def fill_shelf_storage(self, start_id=1, best_storage_type=StorageType.SHELF):
        for i in range(start_id, start_id + MaxInventory.SHELF):
            self.db_client.insert_order(
                self.connection,
                Order(str(i), str(i), best_storage_type, 10 + i),
                StorageType.SHELF,
            )
        self.connection.commit()


    def test_all_storage_is_available_then_does_not_fail(self):
        action_log = ActionLog()
        place_order(
            order=Order("0", "0", StorageType.HOT, 120),
            db_client=self.db_client,
            action_log=action_log,
            connection_pool=self.connection_pool,
        )
        self.assertActionsEqual(action_log, [Action.PLACE])

    def test_when_hot_storage_is_full_then_order_is_placed_in_shelf_storage(self):
        self.fill_hot_storage()

        action_log = ActionLog()
        place_order(
            order=Order("0", "0", StorageType.HOT, 10),
            db_client=self.db_client,
            action_log=action_log,
            connection_pool=self.connection_pool,
        )
        order = self.db_client.fetch_order_if_exists(self.connection, "0")
        self.connection.commit()

        self.assertActionsEqual(action_log, [Action.PLACE])
        self.assertIsNotNone(order)
        self.assertEqual(order.storage_type, StorageType.SHELF)

    def test_when_hot_and_shelf_storage_is_full_then_order_is_discarded_and_placed_in_shelf_storage(self):
        self.fill_hot_storage(start_id=1)
        self.fill_shelf_storage(start_id=1 + MaxInventory.HOT)

        action_log = ActionLog()
        place_order(
            order=Order("0", "0", StorageType.HOT, 10),
            db_client=self.db_client,
            action_log=action_log,
            connection_pool=self.connection_pool,
        )
        order = self.db_client.fetch_order_if_exists(self.connection, "0")
        self.connection.commit()

        self.assertActionsEqual(action_log, [Action.DISCARD, Action.PLACE])
        self.assertIsNotNone(order)
        self.assertEqual(order.storage_type, StorageType.SHELF)


    def tearDown(self):
        self.db_client.delete_all_orders(self.connection)
        self.connection.commit()

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.connection_pool.dispose()


if __name__ == "__main__":
    unittest.main()
