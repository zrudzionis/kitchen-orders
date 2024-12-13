from typing import Callable
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker


from models.database_config import DatabaseConfig
import constants


def get_database_session_pool(db_config: DatabaseConfig, max_connections=1, max_wait=1) -> Engine:
    connection_string = f"postgresql+psycopg2://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.db_name}"
    return create_engine(
        connection_string,
        pool_size=max_connections,
        pool_timeout=max_wait,
        pool_pre_ping=True,
    )

def get_database_session_factory(engine: Engine) -> Callable:
    return sessionmaker(bind=engine)
