from typing import Optional

from sqlalchemy import Column, Integer, String, TIMESTAMP, SmallInteger, Table, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
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

    endpoints = relationship("UserEndpoints", back_populates="user")
    notifications = relationship("Notifications", back_populates="user")

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

    permission: Optional[str] = None

    status = relationship("EndpointsStatus", back_populates="endpoint", uselist=False, lazy="subquery")
    users = relationship("UserEndpoints", back_populates="endpoint")

    notifications = relationship("EndpointNotifications", back_populates="endpoint", lazy="subquery")

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
            'status': self.status.status if self.status else None,
            'permission': self.permission
        }


class EndpointsStatus(Base):
    __tablename__ = "endpoints_status"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    endpoint_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.endpoints.id", ondelete='CASCADE'),
                         primary_key=True)
    status = Column(String)

    endpoint = relationship("Endpoints", back_populates="status", uselist=False)

    def as_dict(self):
        return {
            'endpoint_id': self.endpoint_id,
            'status': self.status
        }


class UserEndpoints(Base):
    __tablename__ = "user_endpoints"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    user_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.users.id", ondelete='CASCADE'),
                     primary_key=True)
    endpoint_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.endpoints.id", ondelete='CASCADE'),
                         primary_key=True)
    permissions = Column(String)
    created_ts = Column(TIMESTAMP, default=func.now())

    user = relationship("Users", back_populates="endpoints")
    endpoint = relationship("Endpoints", back_populates="users")

    def as_dict(self):
        return {
            'user_id': self.user_id,
            'endpoint_id': self.endpoint_id,
            'created_ts': self.created_ts.isoformat(),
            'permissions': self.permissions
        }


class ShareTokens(Base):
    __tablename__ = "share_tokens"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.users.id", ondelete='CASCADE'))
    endpoint_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.endpoints.id", ondelete='CASCADE'))
    used = Column(Boolean)
    token = Column(String)
    created_ts = Column(TIMESTAMP, default=func.now())

    user = relationship("Users")

    def as_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint_id': self.endpoint_id,
            'used': self.used,
            'created_ts': self.created_ts.isoformat()
        }


class Notifications(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint('user_id', 'name', name='uix_user_id_name'),
        {'schema': DatabaseSchemas.CONFIG_SCHEMA.value},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.users.id", ondelete='CASCADE'))
    name = Column(String)
    description = Column(String)
    type = Column(String)
    properties = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())

    user = relationship("Users", back_populates="notifications")

    def as_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'properties': self.properties,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EndpointNotifications(Base):
    __tablename__ = "endpoint_notifications"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    endpoint_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.endpoints.id",
                                             ondelete='CASCADE'), primary_key=True)
    notification_id = Column(Integer, ForeignKey(f"{DatabaseSchemas.CONFIG_SCHEMA.value}.notifications.id",
                                                 ondelete='CASCADE'), primary_key=True)
    created_at = Column(TIMESTAMP, default=func.now())

    endpoint = relationship("Endpoints", back_populates="notifications", uselist=False)
    notification = relationship("Notifications", uselist=False, lazy="subquery")

    def as_dict(self):
        return {
            'endpoint_id': self.endpoint_id,
            'notification_id': self.notification_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
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
