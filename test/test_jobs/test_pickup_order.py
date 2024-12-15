from typing import List
import unittest

from src.clients.database.connection_pool import get_database_connection_pool
from src.clients.database.database_client import DatabaseClient
from src.constants import MaxInventory, StorageType
from src.jobs.pickup_order import pickup_order
from src.models.action_log import ActionLog
from src.models.database_config import DatabaseConfig
from src.models.order import Order
from src.models.action import Action


class TestPickupOrder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connection_pool = get_database_connection_pool(DatabaseConfig(), max_connections=2)
        cls.connection = cls.connection_pool.connect()
        cls.db_client = DatabaseClient()

    def assertActionsEqual(self, action_log: ActionLog, expected_actions: List[str]):
        got_actions = [action.action_type for action in action_log.get_snapshot()]
        msg = f"Expected: {expected_actions}, got: {got_actions}"

        self.assertEqual(len(got_actions), len(expected_actions), msg)
        for expected_action, got_action in zip(expected_actions, got_actions):
            self.assertEqual(expected_action, got_action, msg)

    def test_when_no_orders_are_present_then_does_not_fail(self):
        action_log = ActionLog()
        pickup_order(
            order=Order("0", "0", StorageType.HOT, 120),
            db_client=self.db_client,
            action_log=action_log,
            connection_pool=self.connection_pool,
        )
        self.assertActionsEqual(action_log, [])

    def test_when_we_have_orders_in_hot_storage_then_picks_up_one_order(self):
        for i in range(MaxInventory.HOT):
            self.db_client.insert_order(
                self.connection,
                Order(str(i), str(i), StorageType.HOT, 10 + i),
                StorageType.HOT,
            )
        self.connection.commit()

        action_log = ActionLog()
        pickup_order(
            order=Order("0", "0", StorageType.HOT, 10),
            db_client=self.db_client,
            action_log=action_log,
            connection_pool=self.connection_pool,
        )

        self.assertActionsEqual(action_log, [Action.PICKUP])

    def tearDown(self):
        self.db_client.delete_all_orders(self.connection)
        self.connection.commit()

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.connection_pool.dispose()


if __name__ == "__main__":
    unittest.main()
