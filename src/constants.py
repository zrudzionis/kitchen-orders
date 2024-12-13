from enum import Enum
import os


WORKING_DIR_PATH = "."
SHARED_VOLUME = os.path.join(WORKING_DIR_PATH, "containers_data")
ORDERS_SCHEDULE_FILE_PATH = os.path.join(SHARED_VOLUME, "orders-schedule.json")
EVENTS_FILE_PATH = os.path.join(SHARED_VOLUME, "events.json")


class StorageType(Enum):
    HOT = "hot"
    COLD = "cold"
    SHELF = "shelf"

    def __str__(self):
        return self.value


class MaxInventory(Enum):
    HOT = 6
    COLD = 6
    SHELF = 12

    def __str__(self):
        return self.value


class TransactionIsolationLevel(Enum):
    READ_UNCOMMITTED = "read uncommitted"
    READ_COMMITTED = "read committed"
    REPEATABLE_READ = "repeatable read"
    SERIALIZABLE = "serializable"

    def __str__(self):
        return self.value


TRANSACTION_ISOLATION_LEVELS = [level.value for level in TransactionIsolationLevel]

MAX_DB_CONNECTIONS = 30
MAX_WAIT_DB_CONNECTION_SECONDS = 1
MAX_PROCESSES = 30
JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS = 5
