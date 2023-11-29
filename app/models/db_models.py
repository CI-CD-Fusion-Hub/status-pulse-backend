from typing import Optional

from sqlalchemy import Column, Integer, String, TIMESTAMP, SmallInteger, Table, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.sql.ddl import CreateTable

from app.utils.database import Base, SessionLocal
from app.utils.enums import DatabaseSchemas


class Users(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    created_at = Column(TIMESTAMP, default=func.now())
    status = Column(String)
    access_level = Column(String)

    def as_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'access_level': self.access_level
        }


class Auth(Base):
    __tablename__ = "auth"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, unique=True)
    properties = Column(JSONB)
    admin_users = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())

    def as_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'properties': self.properties,
            'admin_users': self.admin_users,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Endpoints(Base):
    __tablename__ = "endpoints"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_table = Column(String, unique=True)
    name = Column(String)
    description = Column(String)
    url = Column(String)
    threshold = Column(SmallInteger)
    application_id = Column(SmallInteger)
    cron = Column(String)
    status_code = Column(Integer)
    response = Column(JSONB)
    type = Column(String)
    created_at = Column(TIMESTAMP, default=func.now())

    status: Optional[str] = None

    def as_dict(self):
        return {
            'id': self.id,
            'log_table': self.log_table,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'threshold': self.threshold,
            'application_id': self.application_id,
            'cron': self.cron,
            'status_code': self.status_code,
            'response': self.response,
            'type': self.type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status
        }


async def create_log_table(table_name: str):
    log_table = Table(
        table_name, Base.metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('status', String),
        Column('endpoint_id', Integer,
               ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.endpoints.id", ondelete='CASCADE'), nullable=True),
        Column('created_at', TIMESTAMP, default=func.now()),
        Column('response', JSONB),
        Column('response_time', Integer),
        schema=DatabaseSchemas.LOG_SCHEMA.value
    )

    # Generate the SQL statement for table creation
    create_table_stmt = CreateTable(log_table)

    # Use the async session to execute the table creation
    async with SessionLocal() as session:
        await session.execute(create_table_stmt)
        await session.commit()
