import logging
from retry import retry
from sqlalchemy import Connection, Engine
from sqlalchemy.exc import IntegrityError

from clients.database.database_client import DatabaseClient
from constants import MaxInventory, StorageType, TransactionIsolationLevel
from models.action_log import ActionLog
from models.order import Order
import constants
from jobs.exceptions import RetryException

logger = logging.getLogger(__name__)


@retry(exceptions=RetryException, tries=constants.MAX_PLACE_ORDER_TRIES, logger=logger)
def place_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    session_pool: Engine,
):
    try:
        with session_pool.connect() as connection:
            _place_order(order, db_client, action_log, connection)
    except IntegrityError as e:
        logger.error(
            f"Integrity error while placing an order. Order ID: {order.id}. Error: {e}"
        )
        raise RetryException()


def _place_order(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):

    try:
        with db_client.transaction(connection):
            inventory = db_client.fetch_inventory(connection)
    except Exception as e:
        logger.error(f"Unexepected error while fetching inventory. Error: {e}")
        raise

    shelf_available = inventory.shelf < MaxInventory.SHELF
    best_storage_available = (
        (order.temp == StorageType.HOT and inventory.hot < MaxInventory.HOT)
        or (order.temp == StorageType.COLD and inventory.cold < MaxInventory.COLD)
        or (order.temp == StorageType.SHELF and shelf_available)
    )

    logger.debug(
        f"Placing order. Order ID: {order.id}. Best storage available: {best_storage_available}. Shelf available: {shelf_available}."
    )
    if best_storage_available:
        _place_order_to_best_storage(order, db_client, action_log, connection)
    elif shelf_available:
        _place_order_when_best_storage_is_full(order, db_client, action_log, connection)
    else:
        _place_order_when_no_space_left(order, db_client, action_log, connection)


def _place_order_to_best_storage(
    order: Order,
    db_client: DatabaseClient,
    actions_log: ActionLog,
    connection: Connection,
) -> None:
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        db_client.insert_order(connection, order, order.temp)
    actions_log.place(order.id)
    logger.debug(
        f"Action place. Order ID: {order.id}. Storage: {order.temp}. Best storage."
    )


def _place_order_when_best_storage_is_full(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
) -> None:
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        db_client.insert_order(connection, order, StorageType.SHELF)
    action_log.place(order.id)
    logger.debug(f"Action place. Order ID: {order.id}. Storage: {StorageType.SHELF}.")


def _place_order_when_no_space_left(
    order: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
) -> None:
    success = _move_order_and_place_order(order, db_client, action_log, connection)
    if not success:
        _discard_order_and_place_order(order, db_client, action_log, connection)


def _move_order_and_place_order(
    order_to_place: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
) -> bool:
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        order_to_move = db_client.fetch_order_to_move(connection)

        if order_to_move is None:
            return False

        db_client.move_order(
            connection,
            from_storage=order_to_move.storage_type,
            to_storage=order_to_move.order.temp,
            order_id=order_to_move.id,
        )
        db_client.insert_order(connection, order_to_place, StorageType.SHELF)

    action_log.move(order_to_move.id)
    action_log.place(order_to_place.id)
    logger.debug(
        f"Action move. Order ID: {order_to_move.id}. From: {order_to_move.storage_type}. To: {order_to_move.order.temp}."
    )
    logger.debug(
        f"Action place. Order ID: {order_to_place.id}. Storage: {StorageType.SHELF}."
    )
    return True


def _discard_order_and_place_order(
    order_to_place: Order,
    db_client: DatabaseClient,
    action_log: ActionLog,
    connection: Connection,
):
    with db_client.transaction(connection, TransactionIsolationLevel.READ_COMMITTED):
        order_to_discard = db_client.fetch_order_to_discard(connection)

        if not order_to_discard:
            logger.debug(
                f"Order to discard not found while trying to place order: {order_to_place.id}."
            )
            raise ValueError("Order to discard not found.")

        order_deleted = db_client.delete_order_if_exists(
            connection, order_to_discard.id
        )
        db_client.insert_order(connection, order_to_place, StorageType.SHELF)

    if order_deleted:
        action_log.discard(order_to_discard.id)
        logger.debug(
            f"Action discard. Order ID: {order_to_discard.id}. Storage: {order_to_discard.storage_type}."
        )
    action_log.place(order_to_place.id)
    logger.debug(
        f"Action place. Order ID: {order_to_place.id}. Storage: {StorageType.SHELF}."
    )
