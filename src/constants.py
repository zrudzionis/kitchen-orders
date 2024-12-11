from enum import Enum
import os


WORKING_DIR_PATH = "."
SHARED_VOLUME = os.path.join(WORKING_DIR_PATH, "containers_data")
ORDERS_SCHEDULE_FILE_PATH = os.path.join(SHARED_VOLUME, "orders-schedule.json")
EVENTS_FILE_PATH = os.path.join(SHARED_VOLUME, "events.json")


class TransactionIsolationLevel(Enum):
    READ_UNCOMMITTED = "read uncommitted"
    READ_COMMITTED = "read committed"
    REPEATABLE_READ = "repeatable read"
    SERIALIZABLE = "serializable"

TRANSACTION_ISOLATION_LEVELS = [level.value for level in TransactionIsolationLevel]
