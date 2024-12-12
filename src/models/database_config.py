import os


class DatabaseConfig:
    def __init__(self, db_name=None, db_user=None, db_password=None, db_host=None, db_port=None):
        self.db_name = db_name or os.getenv('DB_NAME')
        self.user = db_user or os.getenv('DB_USER')
        self.password = db_password or os.getenv('DB_PASSWORD')
        self.host = db_host or os.getenv('DB_HOST', 'localhost')
        self.port = db_port or os.getenv('DB_PORT', '5432')
