from sqlalchemy.dialects.postgresql import JSONB

from app.utils.database import Base

from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func

from app.utils.enums import DatabaseSchemas


class Users(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': DatabaseSchemas.CONFIG_SCHEMA.value}

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    created_ts = Column(TIMESTAMP, default=func.now())
    status = Column(String)
    access_level = Column(String)

    def as_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'created_ts': self.created_ts.isoformat() if self.created_ts else None,
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
    created_ts = Column(TIMESTAMP, default=func.now())

    def as_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'properties': self.properties,
            'admin_users': self.admin_users,
            'created_ts': self.created_ts.isoformat() if self.created_ts else None
        }


