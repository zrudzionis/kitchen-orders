import os


WORKING_DIR_PATH = "."
SHARED_VOLUME = os.path.join(WORKING_DIR_PATH, "containers_data")
ORDERS_SCHEDULE_FILE_PATH = os.path.join(SHARED_VOLUME, "orders-schedule.json")
EVENTS_FILE_PATH = os.path.join(SHARED_VOLUME, "events.json")
