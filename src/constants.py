from enum import Enum
import os

WEB_SERVER_ENDPOINT = "http://localhost:8000"
SCHEDULE_ORDERS_ENDPOINT = f"{WEB_SERVER_ENDPOINT}/schedule-orders"
MAX_DB_CONNECTIONS = 20
MAX_WORKERS = 20
MAX_WAIT_DB_CONNECTION_SECONDS = 1
JOBS_IN_PROGRESS_REPORTING_PERIOD_SECONDS = 5
# make sure that all jobs are placed in a schedule before starting
JOBS_INITIAL_DELAY_SECONDS = 3
MAX_PICKUP_ORDER_TRIES = 3
MAX_PLACE_ORDER_TRIES = 3

WORKING_DIR_PATH = "."
SHARED_VOLUME = os.path.join(WORKING_DIR_PATH, "containers_data")
ORDERS_SCHEDULE_FILE_PATH = os.path.join(SHARED_VOLUME, "orders-schedule.json")
EVENTS_FILE_PATH = os.path.join(SHARED_VOLUME, "events.json")


class StorageType:
    HOT = "hot"
    COLD = "cold"
    ROOM = "room"


class MaxInventory:
    HOT = 6
    COLD = 6
    ROOM = 12


class TransactionIsolationLevel(Enum):
    READ_UNCOMMITTED = "read uncommitted"
    READ_COMMITTED = "read committed"
    REPEATABLE_READ = "repeatable read"
    SERIALIZABLE = "serializable"

    def __str__(self):
        return self.value


TRANSACTION_ISOLATION_LEVELS = [
    level.value for level in TransactionIsolationLevel]
