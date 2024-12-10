import os


WORKING_DIR_PATH = "."
SHARED_VOLUME = os.path.join(WORKING_DIR_PATH, "containers_data")
COOKING_IN_PROGRESS_FILE_PATH = os.path.join(SHARED_VOLUME, "cooking-in-progress.json")
CONFIG_FILE_PATH = COOKING_IN_PROGRESS_FILE_PATH
PROBLEM_FILE_PATH = os.path.join(WORKING_DIR_PATH, "problem.json")
