from sqlalchemy import create_engine, Engine

from models.database_config import DatabaseConfig


def get_database_connection_pool(db_config: DatabaseConfig, max_connections=1, max_wait=1) -> Engine:
    connection_string = (
        f"postgresql+psycopg2://{db_config.user}:{db_config.password}"
        f"@{db_config.host}:{db_config.port}/{db_config.db_name}"
    )
    return create_engine(
        connection_string,
        pool_size=max_connections,
        pool_timeout=max_wait,
        pool_pre_ping=True,
    )
