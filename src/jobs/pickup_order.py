import logging

from retry import retry
from sqlalchemy import Connection, Engine
from sqlalchemy.exc import IntegrityError


import constants
from clients.database.database_client import DatabaseClient
from constants import TransactionIsolationLevel
from jobs.exceptions import RetryException
from models.action_log import ActionLog
from models.order import Order


logger = logging.getLogger(__name__)


@retry(exceptions=RetryException, tries=constants.MAX_PICKUP_ORDER_TRIES, logger=logger)
def pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    session_pool: Engine,
):
    try:
        with session_pool.connect() as connection:
            _pickup_order(order, db_client, action_log, connection)
    except IntegrityError as e:
        logger.error(
            f"Integrity error while picking up order. Order ID: {order.id}. Error: {e}"
        )
        raise RetryException()


def _pickup_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        order_deleted = db_client.delete_order_if_exists(connection, order.id)
        if order_deleted:
            action_log.pickup(order.id)
            logger.debug(f"Action pickup. Order ID: {order.id}")
        else:
            logger.debug(
                f"Can't delete order that is not in database. Order ID: {order.id}"
            )
