import logging

from sqlalchemy import Connection, Engine

from src.clients.database.database_client import DatabaseClient
from src.constants import TransactionIsolationLevel
from src.models.action_log import ActionLog
from src.models.order import Order


logger = logging.getLogger(__name__)


def pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    session_pool: Engine,
):
    with session_pool.connect() as connection:
        _pickup_order(order, db_client, action_log, connection)


def _pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        # TODO handle discarded order
        # TODO we should probably retry here couple of times
        db_client.delete_order(connection, order.id)
        action_log.pickup(order.id)
        logger.debug(f"Action pickup. Order ID: {order.id}")

