from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.utils.logger import Logger
from app.config.config import Settings

config = Settings().database
LOGGER = Logger().start_logger()

SQLALCHEMY_DATABASE_URL = f"postgresql://{config['user']}:{config['password']}@{config['host']}/{config['name']}"
SQLALCHEMY_ASYNC_DATABASE_URL = \
    f"postgresql+asyncpg://{config['user']}:{config['password']}@{config['host']}/{config['name']}"

engine = create_async_engine(SQLALCHEMY_ASYNC_DATABASE_URL,
                             pool_size=100,
                             max_overflow=2,
                             pool_pre_ping=True,
                             pool_use_lifo=True)

SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()
